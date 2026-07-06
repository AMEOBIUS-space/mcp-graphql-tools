"""Tests for MCP GraphQL Tools — schema, queries, mutations, introspection."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPGraphQLToolsServer, TOOL_DEFS
from src.graphql_engine import GraphQLEngine

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>10
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==14
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"add_type","add_query","add_mutation","add_resolver","list_types","list_queries","list_mutations","get_type","validate_query","execute_query","execute_mutation","introspect","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPGraphQLToolsServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-graphql-tools"
        assert len(m["tools"])==14

class TestTypes:
    def test_add(self):
        s=GraphQLEngine.create_schema()
        r=GraphQLEngine.add_type(s,"User",{"id":"ID","name":"String"})
        assert r["success"] is True
    def test_duplicate(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID"})
        r=GraphQLEngine.add_type(s,"User",{"id":"ID"})
        assert r["success"] is False
    def test_list(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID"})
        GraphQLEngine.add_type(s,"Post",{"id":"ID"})
        r=GraphQLEngine.list_types(s)
        assert r["count"]==2
    def test_get(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID","name":"String"})
        r=GraphQLEngine.get_type(s,"User")
        assert r["success"] is True

class TestQueries:
    def test_add(self):
        s=GraphQLEngine.create_schema()
        r=GraphQLEngine.add_query(s,"getUser","User",args={"id":"ID"})
        assert r["success"] is True
    def test_list(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_query(s,"getUser","User")
        GraphQLEngine.add_query(s,"listUsers","[User]")
        r=GraphQLEngine.list_queries(s)
        assert r["count"]==2

class TestMutations:
    def test_add(self):
        s=GraphQLEngine.create_schema()
        r=GraphQLEngine.add_mutation(s,"createUser","User",args={"name":"String"})
        assert r["success"] is True
    def test_list(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_mutation(s,"createUser","User")
        r=GraphQLEngine.list_mutations(s)
        assert r["count"]==1

class TestExecute:
    def test_query(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_query(s,"getUser","User",resolver="getUser")
        GraphQLEngine.add_resolver(s,"getUser")
        r=GraphQLEngine.execute_query(s,"{ getUser }")
        assert r["success"] is True
        assert "getUser" in r["data"]
    def test_mutation(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_mutation(s,"createUser","User")
        r=GraphQLEngine.execute_mutation(s,"{ createUser }")
        assert r["success"] is True
        assert "createUser" in r["data"]
    def test_invalid(self):
        s=GraphQLEngine.create_schema()
        r=GraphQLEngine.execute_query(s,"{ nonexistent }")
        assert r["errors"] is not None

class TestIntrospect:
    def test_basic(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID"})
        GraphQLEngine.add_query(s,"getUser","User")
        r=GraphQLEngine.introspect(s)
        assert "User" in r["schema"]["types"]

class TestStatsReset:
    def test_stats(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID"})
        GraphQLEngine.add_query(s,"getUser","User")
        r=GraphQLEngine.get_stats(s)
        assert r["type_count"]==1
        assert r["query_count"]==1
    def test_reset(self):
        s=GraphQLEngine.create_schema()
        GraphQLEngine.add_type(s,"User",{"id":"ID"})
        r=GraphQLEngine.reset(s)
        assert r["reset"]["type_count"]==1
        assert GraphQLEngine.get_stats(s)["type_count"]==0

class TestDispatch:
    def test_unknown(self):
        s=MCPGraphQLToolsServer();assert "error" in json.loads(s.handle_tool_call("nope",{}))
    def test_missing(self):
        s=MCPGraphQLToolsServer();assert "error" in json.loads(s.handle_tool_call("add_type",{}))
    def test_add_type_dispatch(self):
        s=MCPGraphQLToolsServer()
        r=json.loads(s.handle_tool_call("add_type",{"name":"User","fields":{"id":"ID"}}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-graphql-tools"
