"""mcp-graphql-tools package — MCP server for GraphQL."""
from .graphql_engine import GraphQLEngine
from .server import MCPGraphQLToolsServer, TOOL_DEFS
__all__ = ["GraphQLEngine", "MCPGraphQLToolsServer", "TOOL_DEFS"]
__version__ = "1.0.0"
