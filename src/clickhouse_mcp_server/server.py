import asyncio
import json
import logging
from logging import Logger
from typing import Dict, List, Any, Optional
from pydantic import AnyUrl

import clickhouse_connect
from clickhouse_connect.driver.binding import quote_identifier, format_query_value
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

from clickhouse_mcp_server.config import Config
from clickhouse_mcp_server.utils import dangerous_check

# Configuration constants
DEFAULT_RESOURCE_PREFIX = "clickhouse://"
DEFAULT_RESULTS_LIMIT = 100

class ClickHouseClient:
    """ClickHouse database client"""

    def __init__(self, config: Config, logger: Logger):
        self.logger = logger
        self.db_config = {
            "host": config.host,
            "port": int(config.port),
            "user": config.user,
            "password": config.password,
            "database": config.database
        }
        self._client = None

    def get_client(self):
        """Get ClickHouse client, singleton pattern"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create a new ClickHouse client"""
        try:
            self.logger.debug(f"Creating ClickHouse client with config: {self.db_config}")
            client = clickhouse_connect.get_client(**self.db_config)
            version = client.server_version
            self.logger.info("ClickHouse client created successfully")
            return client
        except Exception as e:
            self.logger.error(f"Failed to create ClickHouse client: {e}")
            raise

    def execute_query(self, query: str, readonly: bool = True):
        """Execute a query against the ClickHouse database"""
        try:
            client = self.get_client()
            settings = {"readonly": 1} if readonly else {}
            res = client.query(query, settings=settings)

            # convert result to list of dicts
            rows = []
            for row in res.result_rows:
                row_dict = {}
                for i, col_name in enumerate(res.column_names):
                    row_dict[col_name] = row[i]
                rows.append(row_dict)
                
            self.logger.debug(f"Query executed successfully: {query}")
            return rows
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            raise

class TableMetadataManager:
    """Manage table metadata in ClickHouse"""
    def __init__(self, client: ClickHouseClient, logger: Logger):
        self.client = client
        self.logger = logger

    def get_table_list(self, database: str) -> List[str]:
        """Get list of tables in the database"""
        query = f"SHOW TABLES FROM {quote_identifier(database)}"
        result = self.client.execute_query(query)
        if not result:
            return []
        return [row[next(iter(row.keys()))] for row in result]

    def get_table_comments(self, database: str) -> Dict[str, str]:
        """Get comments for the tables in the database"""
        query = f"SELECT name, comment FROM system.tables WHERE database = {format_query_value(database)}"
        result = self.client.execute_query(query)
        return {row['name']: row['comment'] for row in result}

    def get_column_comments(self, database: str) -> Dict[str, Dict[str, str]]:
        """Get comments for the columns in the tables in the database"""
        query = f"SELECT table, name, comment FROM system.columns WHERE database = {format_query_value(database)}"
        result = self.client.execute_query(query)

        column_comments = {}
        for row in result:
            table, col_name, comment = row['table'], row['name'], row['comment']
            if table not in column_comments:
                column_comments[table] = {}
            column_comments[table][col_name] = comment
        return column_comments
    
    def format_table_description(self, table_name: str, table_comment: str, columns_info: Dict[str, str]) -> str:
        """Format table description for the model"""
        description = f"Table: {table_name}\n"
        if table_comment:
            description += f"Description: {table_comment}\n"
        else:
            description += "Description: No description provided\n"

        if columns_info:
            # Add column descriptions
            description += "Columns:\n"
            for col_name, col_comment in columns_info.items():
                if col_comment:
                    description += f"  - {col_name}: {col_comment}\n"
                else:
                    description += f"  - {col_name}: No description provided\n"

        return description

class ResourceManager:
    """MCP resource manager"""

    def __init__(self, client: ClickHouseClient, logger: Logger
                 , resource_prefix: str = DEFAULT_RESOURCE_PREFIX
                 , results_limit: int = DEFAULT_RESULTS_LIMIT):
        self.client = client
        self.logger = logger
        self.metadata_manager = TableMetadataManager(client, logger)
        self.resource_prefix = resource_prefix
        self.results_limit = results_limit

    async def list_resources(self) -> List[Resource]:
        """List all resources in the database"""
        self.logger.debug("Listing resources")
        database = self.client.db_config.get("database")
        
        try:
            # Get table list
            table_list = self.metadata_manager.get_table_list(database)
            if not table_list:
                return []

            # Get table comments and column comments
            table_comments = self.metadata_manager.get_table_comments(database)
            column_comments = self.metadata_manager.get_column_comments(database)

            # Format table descriptions
            resources = []
            for table_name in table_list:
                table_comment = table_comments.get(table_name, "")
                columns_info = column_comments.get(table_name, {})
                description = self.metadata_manager.format_table_description(table_name, table_comment, columns_info)

                # Create resources
                resource = Resource(
                    uri=f"{self.resource_prefix}/{table_name}/data",
                    name=f"Table: {table_name}",
                    mimeType="text/plain",
                    description=description,
                    type="table",
                    metadata = {
                        "columns": [
                            {
                                "name": col_name,
                                "description": col_comment
                            }
                            for col_name, col_comment in columns_info.items()
                        ]
                    }
                )
                resources.append(resource)
            self.logger.debug(f"Found {len(resources)} resources")
            return resources
        except Exception as e:
            self.logger.error(f"Failed to list resources: {e}")
            return []

    async def read_resource(self, uri: AnyUrl) -> str:
        """Read resource data"""
        self.logger.debug(f"Reading resource: {uri}")
        uri_str = str(uri)

        try:
            # Parse URI
            if not uri_str.startswith(self.resource_prefix):
                self.logger.error(f"Invalid resource URI: {uri}")
                return ""

                # get talbe name
                table_name = uri_str[len(self.resource_prefix):].split("/")[0]

                # get query
                query = f"SELECT * FROM {quote_identifier(table_name)} LIMIT {self.results_limit}"
                result = self.client.execute_query(query)

                # format result
                if not result:
                    return "No data found"
                return json.dumps(result, default=str , indent=2)
        except Exception as e:
            self.logger.error(f"Failed to read resource: {e}")
            return f"Error reading resource: {str(e)}"


class ToolManager:
    """MCP tool manager"""

    def __init__(self, client: ClickHouseClient, logger: Logger):
        self.client = client
        self.logger = logger

    async def list_tools(self) -> List[Tool]:
        """List all tools"""
        self.logger.debug("Listing tools")
        return [
            Tool(
                name="execute_sql",
                description="Execute a query against the ClickHouse database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to be executed"
                        }
                    },
                    "required": ["query"],
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool"""
        self.logger.debug(f"Calling tool: {name} with arguments: {arguments}")

        # Tool handler mapping
        tool_handlers = {
            "execute_sql": self._handle_execute_sql
        }

        # Get handler
        handler = tool_handlers.get(name)
        if not handler:
            self.logger.error(f"Tool not found: {name}")
            return []

        # Call handler
        return await handler(arguments)

    async def _handle_execute_sql(self, arguments: Dict[str, str]) -> List[TextContent]:
        """Handle execute_sql tool"""
        self.logger.debug("Handling execute_sql tool")
        # Get query
        query = arguments.get("query")
        if not query:
            self.logger.error("Query is required")
            return []

        # Check query
        is_dangerous, pattern = dangerous_check(query)
        if is_dangerous:
            self.logger.error(f"Dangerous query detected: {pattern}")
            return [TextContent(value=f"Error: Dangerous query detected: {pattern}")]

        try:
            # Execute query
            result = self.client.execute_query(query)
            json_result = json.dumps(result, default=str, indent=2)
            return [
                TextContent(
                    type='text',
                    text=json_result,
                    mimeType='application/json'
                )
            ]
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            return [TextContent(type='text', text=f"Error executing query: {str(e)}")]

class DatabaseServer:
    """MCP database server"""
    def __init__(self, config: Config, logger: Logger):
        self.app = Server("clickhouse_mcp_server")
        self.logger = logger

        # create components
        self.client = ClickHouseClient(config, logger)
        self.resource_manager = ResourceManager(self.client, logger)
        self.tool_manager = ToolManager(self.client, logger)

        # register components
        self.app.list_resources()(self.resource_manager.list_resources)
        self.app.read_resource()(self.resource_manager.read_resource)
        self.app.list_tools()(self.tool_manager.list_tools)
        self.app.call_tool()(self.tool_manager.call_tool)

    async def run(self):
        """Run the server"""
        from mcp.server.stdio import stdio_server
        
        self.logger.info("Starting server")
        async with stdio_server() as (read_stream, write_stream):
            try:
                await self.app.run(
                    read_stream, 
                    write_stream,
                    self.app.create_initialization_options()
                )
            except Exception as e:
                self.logger.error(f"Server error: {e}")
                raise

async def main(config: Config):
    """Main function"""
    logger = logging.getLogger("clickhouse_mcp_server")

    # create and start server
    db_server = DatabaseServer(logger=logger, config=config)
    await db_server.run()

if __name__ == "__main__":
    asyncio.run(main(Config.from_env_arguments()))