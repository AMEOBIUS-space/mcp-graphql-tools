"""MCP Server for GraphQL — schema, queries, mutations, introspection."""
import json, sys, argparse
from .graphql_engine import GraphQLEngine

_store = GraphQLEngine.create_schema()

TOOL_DEFS = [
    {"name":"add_type","description":"Add a GraphQL type.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"fields":{"type":"object"}},"required":["name","fields"]}},
    {"name":"add_query","description":"Add a query field.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"return_type":{"type":"string"},"args":{"type":"object"},"resolver":{"type":"string"}},"required":["name","return_type"]}},
    {"name":"add_mutation","description":"Add a mutation field.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"return_type":{"type":"string"},"args":{"type":"object"},"resolver":{"type":"string"}},"required":["name","return_type"]}},
    {"name":"add_resolver","description":"Add a resolver.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"handler":{"type":"string","default":"default"}},"required":["name"]}},
    {"name":"list_types","description":"List all types.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"list_queries","description":"List all queries.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"list_mutations","description":"List all mutations.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_type","description":"Get type details.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}},
    {"name":"validate_query","description":"Validate a GraphQL query.","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
    {"name":"execute_query","description":"Execute a GraphQL query.","inputSchema":{"type":"object","properties":{"query":{"type":"string"},"variables":{"type":"object"}},"required":["query"]}},
    {"name":"execute_mutation","description":"Execute a GraphQL mutation.","inputSchema":{"type":"object","properties":{"mutation":{"type":"string"},"variables":{"type":"object"}},"required":["mutation"]}},
    {"name":"introspect","description":"Introspect the schema.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_stats","description":"Get GraphQL statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset the schema.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPGraphQLToolsServer:
    def __init__(self,name="mcp-graphql-tools",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="add_type":return json.dumps(GraphQLEngine.add_type(_store,args["name"],args["fields"]))
            elif name=="add_query":return json.dumps(GraphQLEngine.add_query(_store,args["name"],args["return_type"],args.get("args"),args.get("resolver")))
            elif name=="add_mutation":return json.dumps(GraphQLEngine.add_mutation(_store,args["name"],args["return_type"],args.get("args"),args.get("resolver")))
            elif name=="add_resolver":return json.dumps(GraphQLEngine.add_resolver(_store,args["name"],args.get("handler","default")))
            elif name=="list_types":return json.dumps(GraphQLEngine.list_types(_store))
            elif name=="list_queries":return json.dumps(GraphQLEngine.list_queries(_store))
            elif name=="list_mutations":return json.dumps(GraphQLEngine.list_mutations(_store))
            elif name=="get_type":return json.dumps(GraphQLEngine.get_type(_store,args["name"]))
            elif name=="validate_query":return json.dumps(GraphQLEngine.validate_query(_store,args["query"]))
            elif name=="execute_query":return json.dumps(GraphQLEngine.execute_query(_store,args["query"],args.get("variables")))
            elif name=="execute_mutation":return json.dumps(GraphQLEngine.execute_mutation(_store,args["mutation"],args.get("variables")))
            elif name=="introspect":return json.dumps(GraphQLEngine.introspect(_store))
            elif name=="get_stats":return json.dumps(GraphQLEngine.get_stats(_store))
            elif name=="reset":return json.dumps(GraphQLEngine.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPGraphQLToolsServer()
    for line in sys.stdin:
        line=line.strip()
        if not line:continue
        try:request=json.loads(line)
        except json.JSONDecodeError:print(json.dumps({"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"}}),flush=True);continue
        method=request.get("method","");req_id=request.get("id");params=request.get("params",{})
        if method=="initialize":response={"jsonrpc":"2.0","id":req_id,"result":{"server":server.name,"version":server.version}}
        elif method=="tools/list":response={"jsonrpc":"2.0","id":req_id,"result":{"tools":server.list_tools()}}
        elif method=="tools/call":
            result=server.handle_tool_call(params.get("name",""),params.get("arguments",{}))
            response={"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":result}]}}
        elif method=="shutdown":response={"jsonrpc":"2.0","id":req_id,"result":{}};print(json.dumps(response),flush=True);break
        else:response={"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Method not found: {method}"}}
        print(json.dumps(response),flush=True)

def main():
    parser=argparse.ArgumentParser(description="MCP GraphQL Tools Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPGraphQLToolsServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
