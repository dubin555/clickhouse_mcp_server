import asyncio 
from . import server 
from clickhouse_mcp_server.config import Config

def main():
    config = Config.from_env_arguments()
    asyncio.run(server.main(config))