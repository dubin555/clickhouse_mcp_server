# ClickHouse MCP Server
A Model Context Protocal (MCP) server implement for ClickHouse.

This server provides AI assistants with a secure and structured way to explore and analyze databases. It enables them to list tables, read data, and execute SQL queries through a controlled interface, ensuring responsible database access.

# Configuration

Set the following environment variables:

```bash
CLICKHOUSE_HOST=localhost    
CLICKHOUSE_PORT=8123         
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=CHANGE_TO_YOUR_PASSWORD
CLICKHOUSE_DATABASE=default
```

Or via command-line args:

* `--host` the database host
* `--port` the database port
* `--user` the database username
* `--password` the database password
* `--database` the database name

# Usage
## Fake some data in clickhouse
Check the SQL in dev_contribute.md for details.
## Post your question to AI assistant in Cline
```
What is the sales volume in each region? Which product is the best - selling?
```
<img src="pics/demo.png" alt="Demo Screenshot" width="600" />

## CLINE

Configure the MCP server in VSCode, Cline extension, or other MCP client.:
Example:
```json
{
  "mcpServers": {
    "clickhouse": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/clickhouse_mcp_server",
        "run",
        "-m",
        "clickhouse_mcp_server.server"
      ],
      "env": {
        "CLICKHOUSE_HOST": "localhost",
        "CLICKHOUSE_PORT": "8123",
        "CLICKHOUSE_USER": "default",
        "CLICKHOUSE_PASSWORD": "CHANGE_TO_YOUR_PASSWORD",
        "CLICKHOUSE_DATABASE": "default"
      }
    }
    
  }
}
```

# License

APACHE - See LICENSE file for details.

# Contribute
See dev_contribute.md for details.

## Prerequisites
- Python with `uv` package manager
- ClickHouse installation
- MCP server dependencies

# Acknowledgement
This library's implementation was inspired by the following three repositories and incorporates their code, respect for the open-source spirit!
* [GreptimeTeam/greptimedb-mcp-server](https://github.com/GreptimeTeam/greptimedb-mcp-server)
* [ktanaka101/mcp-server-duckdb](https://github.com/ktanaka101/mcp-server-duckdb)
* [designcomputer/mysql_mcp_server)](https://github.com/designcomputer/mysql_mcp_server)

Thanks!