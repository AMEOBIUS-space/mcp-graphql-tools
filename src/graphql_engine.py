"""GraphQL engine — zero dependencies.
Provides schema definition, query parsing, field resolution, validation.
"""
import json, re, time
from typing import Any, Dict, List, Optional

class GraphQLEngine:
    @staticmethod
    def create_schema() -> Dict:
        return {"types": {}, "queries": {}, "mutations": {}, "resolvers": {}, "total_queries": 0, "total_mutations": 0, "total_errors": 0}

    @staticmethod
    def add_type(schema: Dict, name: str, fields: Dict) -> Dict:
        if name in schema["types"]:
            return {"success": False, "error": f"Type '{name}' already exists"}
        schema["types"][name] = {"name": name, "fields": fields, "created": time.time()}
        return {"success": True, "type": name, "field_count": len(fields)}

    @staticmethod
    def add_query(schema: Dict, name: str, return_type: str, args: Dict = None, resolver: str = None) -> Dict:
        schema["queries"][name] = {"name": name, "return_type": return_type, "args": args or {}, "resolver": resolver}
        return {"success": True, "query": name}

    @staticmethod
    def add_mutation(schema: Dict, name: str, return_type: str, args: Dict = None, resolver: str = None) -> Dict:
        schema["mutations"][name] = {"name": name, "return_type": return_type, "args": args or {}, "resolver": resolver}
        return {"success": True, "mutation": name}

    @staticmethod
    def add_resolver(schema: Dict, name: str, handler: str = "default") -> Dict:
        schema["resolvers"][name] = {"handler": handler, "calls": 0}
        return {"success": True, "resolver": name}

    @staticmethod
    def list_types(schema: Dict) -> Dict:
        return {"success": True, "types": list(schema["types"].keys()), "count": len(schema["types"])}

    @staticmethod
    def list_queries(schema: Dict) -> Dict:
        return {"success": True, "queries": list(schema["queries"].keys()), "count": len(schema["queries"])}

    @staticmethod
    def list_mutations(schema: Dict) -> Dict:
        return {"success": True, "mutations": list(schema["mutations"].keys()), "count": len(schema["mutations"])}

    @staticmethod
    def get_type(schema: Dict, name: str) -> Dict:
        if name not in schema["types"]:
            return {"success": False, "error": f"Type '{name}' not found"}
        return {"success": True, "type": schema["types"][name]}

    @staticmethod
    def validate_query(schema: Dict, query: str) -> Dict:
        errors = []
        # Extract field names from simple queries like { field1 field2 }
        fields = re.findall(r'\w+', query)
        skip_words = {"query", "mutation", "id", "create", "update", "delete"}
        for field in fields:
            if field in skip_words:
                continue
            if field not in schema["queries"] and field not in schema["types"] and field not in schema["mutations"]:
                errors.append(f"Unknown field: {field}")
        found = [f for f in fields if f not in skip_words]
        return {"success": True, "valid": len(errors) == 0, "errors": errors, "fields_found": found}

    @staticmethod
    def execute_query(schema: Dict, query: str, variables: Dict = None) -> Dict:
        schema["total_queries"] += 1
        validation = GraphQLEngine.validate_query(schema, query)
        if not validation["valid"]:
            schema["total_errors"] += 1
            return {"success": True, "errors": validation["errors"], "data": None}
        result = {}
        for field in validation["fields_found"]:
            if field in schema["queries"]:
                q = schema["queries"][field]
                resolver_name = q.get("resolver", field)
                if resolver_name in schema["resolvers"]:
                    schema["resolvers"][resolver_name]["calls"] += 1
                result[field] = f"resolved:{field}"
        return {"success": True, "data": result, "errors": None}

    @staticmethod
    def execute_mutation(schema: Dict, mutation: str, variables: Dict = None) -> Dict:
        schema["total_mutations"] += 1
        validation = GraphQLEngine.validate_query(schema, mutation)
        if not validation["valid"]:
            schema["total_errors"] += 1
            return {"success": True, "errors": validation["errors"], "data": None}
        result = {}
        for field in validation["fields_found"]:
            if field in schema["mutations"]:
                result[field] = f"mutated:{field}"
        return {"success": True, "data": result, "errors": None}

    @staticmethod
    def introspect(schema: Dict) -> Dict:
        return {"success": True, "schema": {"types": {k: list(v["fields"].keys()) for k, v in schema["types"].items()}, "queries": list(schema["queries"].keys()), "mutations": list(schema["mutations"].keys()), "resolvers": list(schema["resolvers"].keys())}}

    @staticmethod
    def get_stats(schema: Dict) -> Dict:
        return {"success": True, "type_count": len(schema["types"]), "query_count": len(schema["queries"]), "mutation_count": len(schema["mutations"]), "resolver_count": len(schema["resolvers"]), "total_queries": schema["total_queries"], "total_mutations": schema["total_mutations"], "total_errors": schema["total_errors"]}

    @staticmethod
    def reset(schema: Dict) -> Dict:
        old = GraphQLEngine.get_stats(schema)
        schema["types"] = {}; schema["queries"] = {}; schema["mutations"] = {}; schema["resolvers"] = {}
        schema["total_queries"] = 0; schema["total_mutations"] = 0; schema["total_errors"] = 0
        return {"success": True, "reset": old}
