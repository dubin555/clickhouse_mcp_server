import argparse
import os
from dataclasses import dataclass

@dataclass
class Config:
    """
    Configuration class for the Clickhouse MCP server. 
    """

    host: str
    port: int
    user: str
    password: str
    database: str

    @staticmethod
    def from_env_arguments() -> "Config":
        """
        Create a Config instance from environment variables and command-line arguments.
        """
        parser = argparse.ArgumentParser(description="Clickhouse MCP server")
        parser.add_argument("--host", type=str, default=os.getenv("CLICKHOUSE_HOST", "localhost"), help="Clickhouse host")
        parser.add_argument("--port", type=int, default=os.getenv("CLICKHOUSE_PORT", 9000), help="Clickhouse port")
        parser.add_argument("--user", type=str, default=os.getenv("CLICKHOUSE_USER", "default"), help="Clickhouse user")
        parser.add_argument("--password", type=str, default=os.getenv("CLICKHOUSE_PASSWORD", ""), help="Clickhouse password")
        parser.add_argument("--database", type=str, default=os.getenv("CLICKHOUSE_DATABASE", "default"), help="Clickhouse database")

        args = parser.parse_args()

        return Config(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )