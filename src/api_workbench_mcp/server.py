"""
API Workbench MCP Server.

A comprehensive MCP server for API testing - an open source Postman replacement.
Designed following Anthropic's best practices for building effective tools for agents.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .services import (
    AssertionEngine,
    CollectionStore,
    HistoryManager,
    HttpClient,
    VariableStore,
)
from .types import (
    AssertionCheckInput,
    AssertionConfig,
    AssertionOperator,
    AssertionType,
    AuthConfig,
    AuthType,
    BasicAuth,
    BearerAuth,
    ApiKeyAuth,
    BodyType,
    CollectionRequest,
    CollectionRunSummary,
    EnvCreateInput,
    EnvironmentVariable,
    HistoryListInput,
    HttpMethod,
    ImportFormat,
    RequestResult,
    RequestSendInput,
    ResponseFormat,
    VariableScope,
)


# =============================================================================
# Server Setup
# =============================================================================

COLLECTIONS_DIR = os.environ.get("API_WORKBENCH_COLLECTIONS", "collections")
HISTORY_DB = os.environ.get("API_WORKBENCH_HISTORY_DB", "history.db")
DEFAULT_ENV = os.environ.get("API_WORKBENCH_DEFAULT_ENV")

variable_store = VariableStore()
http_client = HttpClient(variable_store)
collection_store = CollectionStore(COLLECTIONS_DIR)
assertion_engine = AssertionEngine()
history_manager = HistoryManager(HISTORY_DB)

_start_time = time.time()

mcp = FastMCP("API Workbench")


# =============================================================================
# Request Tools
# =============================================================================


@mcp.tool()
async def request_send(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    body: Any | None = None,
    body_type: str = "json",
    auth_type: str | None = None,
    auth_credentials: dict[str, str] | None = None,
    timeout: int = 30000,
    follow_redirects: bool = True,
    validate_ssl: bool = True,
    environment: str | None = None,
    variable_overrides: dict[str, str] | None = None,
    response_format: str = "concise",
) -> dict[str, Any]:
    """
    Send an HTTP request and receive the response.

    Variables in {{double_braces}} are automatically substituted from the active environment.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
        url: Request URL. Supports {{variable}} substitution.
        headers: Request headers as key-value pairs.
        query_params: Query parameters to append to URL.
        body: Request body (dict for JSON, dict for form data).
        body_type: Body type: json, form, raw, multipart.
        auth_type: Auth type: none, basic, bearer, api_key.
        auth_credentials: For basic: {username, password}. For bearer: {token}.
        timeout: Timeout in milliseconds (default 30000).
        environment: Environment for variable substitution.
        variable_overrides: Temporary variable overrides for this request only.
            Overrides take precedence over environment/collection/global variables.
            Example: {"model": "claude-3-opus", "prompt": "Custom prompt"}
        response_format: 'concise' (default) or 'detailed'.

    Returns:
        Response with status, body, duration. Detailed includes headers/cookies.
    """
    # Build auth config
    auth = None
    if auth_type and auth_type != "none" and auth_credentials:
        auth = AuthConfig(type=AuthType(auth_type))
        if auth_type == "basic":
            auth.basic = BasicAuth(
                username=auth_credentials.get("username", ""),
                password=auth_credentials.get("password", ""),
            )
        elif auth_type == "bearer":
            auth.bearer = BearerAuth(token=auth_credentials.get("token", ""))
        elif auth_type == "api_key":
            auth.api_key = ApiKeyAuth(
                key=auth_credentials.get("key", ""),
                value=auth_credentials.get("value", ""),
                location=auth_credentials.get("location", "header"),
            )

    input_data = RequestSendInput(
        method=HttpMethod(method.upper()),
        url=url,
        headers=headers or {},
        query_params=query_params or {},
        body=body,
        body_type=BodyType(body_type),
        auth=auth,
        timeout=timeout,
        follow_redirects=follow_redirects,
        validate_ssl=validate_ssl,
        environment=environment,
        variable_overrides=variable_overrides or {},
        response_format=ResponseFormat(response_format),
    )

    result = await http_client.send_request(input_data)

    # Record in history
    await history_manager.add_entry(
        method=input_data.method,
        url=url,
        status=result.status,
        duration=result.duration,
        environment=environment,
        request_headers=headers,
        request_body=body,
        response_body=result.body,
    )

    return result.model_dump(exclude_none=True)


@mcp.tool()
def request_inspect(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: Any | None = None,
    environment: str | None = None,
) -> dict[str, Any]:
    """
    Preview a request without sending it (dry run).
    
    Returns the resolved URL, headers, body after variable substitution,
    plus an equivalent cURL command.
    
    Args:
        method: HTTP method
        url: Request URL with {{variables}}
        headers: Request headers
        body: Request body
        environment: Environment for substitution
    
    Returns:
        resolved_url, resolved_headers, resolved_body, curl_command, warnings
    """
    result = http_client.inspect_request(
        method=HttpMethod(method.upper()),
        url=url,
        headers=headers,
        body=body,
        environment=environment,
    )
    return result.model_dump()


# =============================================================================
# Environment Tools
# =============================================================================


@mcp.tool()
def env_create(
    name: str,
    variables: dict[str, str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a new environment with variables.
    
    Args:
        name: Environment name (e.g., 'development', 'staging', 'production')
        variables: Initial variables as key-value pairs
        description: Optional description
    
    Returns:
        Created environment details
    """
    env = variable_store.create_environment(name, variables, description)
    return {
        "name": env.name,
        "description": env.description,
        "variable_count": len(env.variables),
        "message": f"Environment '{name}' created successfully",
    }


@mcp.tool()
def env_switch(name: str | None) -> dict[str, Any]:
    """
    Switch the active environment.
    
    Args:
        name: Environment name to activate, or None to deactivate
    
    Returns:
        Previous and current environment names
    """
    previous = variable_store.switch_environment(name)
    return {
        "previous_environment": previous,
        "current_environment": name,
        "message": f"Switched from '{previous}' to '{name}'" if name else "Environment deactivated",
    }


@mcp.tool()
def env_set_var(
    name: str,
    value: str,
    scope: str = "environment",
    environment: str | None = None,
    secret: bool = False,
) -> dict[str, Any]:
    """
    Set or update a variable.
    
    Args:
        name: Variable name
        value: Variable value
        scope: Scope: 'environment', 'collection', or 'global'
        environment: Target environment (uses active if not specified)
        secret: Whether to mask value in responses
    
    Returns:
        Confirmation of variable set
    """
    variable_store.set_variable(
        name=name,
        value=value,
        scope=VariableScope(scope),
        environment=environment,
        secret=secret,
    )
    return {
        "name": name,
        "scope": scope,
        "secret": secret,
        "message": f"Variable '{name}' set in {scope} scope",
    }


@mcp.tool()
def env_get_var(name: str, environment: str | None = None) -> dict[str, Any]:
    """
    Get a variable value.
    
    Args:
        name: Variable name
        environment: Environment to check (uses active if not specified)
    
    Returns:
        Variable value or None if not found
    """
    value = variable_store.get_variable(name, environment=environment)
    return {
        "name": name,
        "value": value,
        "found": value is not None,
    }


@mcp.tool()
def env_list(
    show_variables: bool = False,
    environment: str | None = None,
    mask_secrets: bool = True,
) -> dict[str, Any]:
    """
    List environments and optionally their variables.
    
    Args:
        show_variables: Whether to include variable values
        environment: Specific environment to show, or all
        mask_secrets: Whether to mask secret values (default true)
    
    Returns:
        List of environments with optional variables
    """
    environments = variable_store.list_environments()
    active = variable_store.get_active_environment()

    if environment:
        env = variable_store.get_environment(environment)
        if not env:
            return {"error": f"Environment '{environment}' not found"}
        
        result = {
            "name": env.name,
            "description": env.description,
            "active": env.name == active,
        }
        if show_variables:
            result["variables"] = variable_store.get_all_variables(
                environment=environment, mask_secrets=mask_secrets
            )
        return result

    result = {
        "environments": environments,
        "active_environment": active,
        "count": len(environments),
    }
    
    if show_variables:
        result["all_variables"] = variable_store.get_all_variables(mask_secrets=mask_secrets)
    
    return result


# =============================================================================
# Collection Tools
# =============================================================================


@mcp.tool()
def collection_create(
    name: str,
    description: str | None = None,
    folders: list[str] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """
    Create a new API collection.
    
    Args:
        name: Collection name
        description: Collection description
        folders: Initial folder names to create
        base_url: Base URL for all requests (stored as collection variable)
    
    Returns:
        Created collection details
    """
    collection = collection_store.create_collection(
        name=name,
        description=description,
        folders=folders,
        base_url=base_url,
    )
    return {
        "name": collection.name,
        "description": collection.description,
        "folders": [f.name for f in collection.folders],
        "message": f"Collection '{name}' created successfully",
    }


@mcp.tool()
def collection_list(
    filter_term: str | None = None,
    response_format: str = "summary",
) -> dict[str, Any]:
    """
    List available collections.
    
    Args:
        filter_term: Optional search term to filter collections
        response_format: 'names', 'summary', or 'detailed'
    
    Returns:
        List of collections matching the filter
    """
    collections = collection_store.list_collections()
    
    if filter_term:
        collections = [c for c in collections if filter_term.lower() in c.lower()]

    if response_format == "names":
        return {"collections": collections, "count": len(collections)}

    result = []
    for name in collections:
        coll = collection_store.get_collection(name)
        if coll:
            info = {
                "name": coll.name,
                "description": coll.description,
                "request_count": len(coll.requests),
                "folder_count": len(coll.folders),
            }
            if response_format == "detailed":
                info["requests"] = list(coll.requests.keys())
                info["folders"] = [f.name for f in coll.folders]
            result.append(info)

    return {"collections": result, "count": len(result)}


@mcp.tool()
def collection_add_request(
    collection: str,
    name: str,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: Any | None = None,
    folder: str | None = None,
    pre_request_script: str | None = None,
    post_response_script: str | None = None,
) -> dict[str, Any]:
    """
    Add a request to a collection.
    
    Args:
        collection: Collection name
        name: Request name
        method: HTTP method
        url: Request URL
        headers: Request headers
        body: Request body
        folder: Folder path to add request to (e.g., 'Users/Authentication')
        pre_request_script: JavaScript to run before request
        post_response_script: JavaScript to run after response
    
    Returns:
        Confirmation of request added
    """
    request = CollectionRequest(
        name=name,
        method=HttpMethod(method.upper()),
        url=url,
        headers=headers or {},
        body=body,
        pre_request_script=pre_request_script,
        post_response_script=post_response_script,
    )

    success = collection_store.add_request(collection, request, folder)
    
    if not success:
        return {"error": f"Collection '{collection}' not found"}

    return {
        "collection": collection,
        "request": name,
        "folder": folder,
        "message": f"Request '{name}' added to collection '{collection}'",
    }


@mcp.tool()
async def collection_run(
    collection: str,
    folder: str | None = None,
    environment: str | None = None,
    iterations: int = 1,
    delay: int = 0,
    stop_on_error: bool = False,
    response_format: str = "summary",
) -> dict[str, Any]:
    """
    Run all requests in a collection and return test results.
    
    Args:
        collection: Collection name
        folder: Optional subfolder to run
        environment: Environment for variable substitution
        iterations: Number of times to run (default 1)
        delay: Delay between requests in ms (default 0)
        stop_on_error: Stop on first failure (default false)
        response_format: 'summary', 'detailed', or 'verbose'
    
    Returns:
        Test results with pass/fail counts and timing
    """
    coll = collection_store.get_collection(collection)
    if not coll:
        return {"error": f"Collection '{collection}' not found"}

    # Get requests to run
    request_names = collection_store.get_all_request_names(collection, folder)
    
    results: list[RequestResult] = []
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    start_time = time.time()

    for iteration in range(iterations):
        for req_name in request_names:
            request = coll.requests.get(req_name)
            if not request:
                total_skipped += 1
                results.append(RequestResult(
                    name=req_name,
                    status="skipped",
                    duration=0,
                    error="Request not found",
                ))
                continue

            # Build request input
            input_data = RequestSendInput(
                method=request.method,
                url=request.url,
                headers=request.headers,
                body=request.body,
                body_type=request.body_type,
                auth=request.auth,
                environment=environment,
                response_format=ResponseFormat.CONCISE,
            )

            try:
                response = await http_client.send_request(input_data, collection)
                
                # Run assertions if defined
                assertion_passed = True
                assertion_results = None
                
                if request.assertions:
                    assertion_input = AssertionCheckInput(
                        response={
                            "status": response.status,
                            "body": response.body,
                            "headers": response.headers or {},
                            "duration": response.duration,
                        },
                        assertions=[
                            AssertionConfig(**a) if isinstance(a, dict) else a
                            for a in request.assertions
                        ],
                    )
                    assertion_output = assertion_engine.check_assertions(assertion_input)
                    assertion_passed = assertion_output.passed
                    assertion_results = {
                        "total": len(assertion_output.results),
                        "passed": sum(1 for r in assertion_output.results if r.passed),
                        "failed": sum(1 for r in assertion_output.results if not r.passed),
                    }

                if assertion_passed:
                    total_passed += 1
                    status = "passed"
                else:
                    total_failed += 1
                    status = "failed"

                results.append(RequestResult(
                    name=req_name,
                    status=status,
                    response_status=response.status,
                    duration=response.duration,
                    assertions=assertion_results,
                ))

                if not assertion_passed and stop_on_error:
                    break

            except Exception as e:
                total_failed += 1
                results.append(RequestResult(
                    name=req_name,
                    status="failed",
                    duration=0,
                    error=str(e),
                ))
                if stop_on_error:
                    break

            # Delay between requests
            if delay > 0:
                await asyncio.sleep(delay / 1000)

        if stop_on_error and total_failed > 0:
            break

    total_duration = int((time.time() - start_time) * 1000)

    summary = CollectionRunSummary(
        total=len(results),
        passed=total_passed,
        failed=total_failed,
        skipped=total_skipped,
        duration=total_duration,
    )

    output = {
        "summary": summary.model_dump(),
    }

    if response_format in ("detailed", "verbose"):
        output["results"] = [r.model_dump(exclude_none=True) for r in results]

    return output


# =============================================================================
# Assertion Tools
# =============================================================================


@mcp.tool()
def assertion_check(
    response_status: int,
    response_body: Any,
    response_headers: dict[str, str] | None = None,
    response_duration: int | None = None,
    assertions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run assertions against a response without scripts.
    
    Args:
        response_status: HTTP status code
        response_body: Response body (JSON or string)
        response_headers: Response headers
        response_duration: Response time in ms
        assertions: List of assertions to check. Each has:
            - type: status, body_contains, body_equals, body_jsonpath,
                   header_exists, header_equals, response_time, json_schema
            - target: For jsonpath/header assertions
            - expected: Expected value
            - operator: equals, contains, lt, gt, exists, etc.
    
    Returns:
        Overall pass/fail and individual assertion results
    
    Example assertions:
        [
            {"type": "status", "expected": 200},
            {"type": "body_jsonpath", "target": "$.id", "operator": "exists"},
            {"type": "header_exists", "target": "Content-Type"}
        ]
    """
    if not assertions:
        return {"passed": True, "results": [], "message": "No assertions provided"}

    parsed_assertions = []
    for a in assertions:
        parsed_assertions.append(AssertionConfig(
            type=AssertionType(a["type"]),
            target=a.get("target"),
            expected=a.get("expected"),
            operator=AssertionOperator(a.get("operator", "equals")),
        ))

    input_data = AssertionCheckInput(
        response={
            "status": response_status,
            "body": response_body,
            "headers": response_headers or {},
            "duration": response_duration or 0,
        },
        assertions=parsed_assertions,
    )

    result = assertion_engine.check_assertions(input_data)
    
    return {
        "passed": result.passed,
        "results": [r.model_dump(exclude_none=True) for r in result.results],
    }


# =============================================================================
# History Tools
# =============================================================================


@mcp.tool()
async def history_list(
    limit: int = 20,
    method: str | None = None,
    url_pattern: str | None = None,
    status_code: int | None = None,
) -> dict[str, Any]:
    """
    List recent request history.
    
    Args:
        limit: Maximum entries to return (default 20, max 100)
        method: Filter by HTTP method
        url_pattern: Filter by URL pattern (partial match)
        status_code: Filter by status code
    
    Returns:
        List of history entries with id, method, url, status, duration, timestamp
    """
    input_data = HistoryListInput(
        limit=min(limit, 100),
        method=HttpMethod(method.upper()) if method else None,
        url_pattern=url_pattern,
        status_code=status_code,
    )

    result = await history_manager.list_entries(input_data)
    
    return {
        "entries": [
            {
                "id": e.id,
                "method": e.method.value,
                "url": e.url,
                "status": e.status,
                "duration": e.duration,
                "timestamp": e.timestamp.isoformat(),
                "environment": e.environment,
            }
            for e in result.entries
        ],
        "total": result.total,
        "showing": len(result.entries),
    }


@mcp.tool()
async def history_get(entry_id: str) -> dict[str, Any]:
    """
    Get full details of a history entry.
    
    Args:
        entry_id: History entry ID from history_list
    
    Returns:
        Full request/response details for replay
    """
    entry = await history_manager.get_entry(entry_id)
    if not entry:
        return {"error": f"History entry '{entry_id}' not found"}
    return entry


@mcp.tool()
async def history_replay(
    entry_id: str,
    environment: str | None = None,
    header_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Re-execute a request from history.
    
    Args:
        entry_id: History entry ID to replay
        environment: Override environment
        header_overrides: Headers to override
    
    Returns:
        New response from replayed request
    """
    entry = await history_manager.get_entry(entry_id)
    if not entry:
        return {"error": f"History entry '{entry_id}' not found"}

    headers = entry.get("request", {}).get("headers", {}) or {}
    if header_overrides:
        headers.update(header_overrides)

    return await request_send(
        method=entry["method"],
        url=entry["url"],
        headers=headers,
        body=entry.get("request", {}).get("body"),
        environment=environment,
    )


# =============================================================================
# Import/Export Tools
# =============================================================================


@mcp.tool()
def import_collection(
    source: str,
    format: str = "postman_v2.1",
) -> dict[str, Any]:
    """
    Import a collection from various formats.
    
    Args:
        source: File path to import from
        format: Format type: postman_v2, postman_v2.1, openapi_3, curl
    
    Returns:
        Import results with request/folder counts
    """
    try:
        with open(source) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": f"File not found: {source}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    if format in ("postman_v2", "postman_v2.1"):
        collection = collection_store.import_postman_collection(data)
        return {
            "collection": collection.name,
            "requests_imported": len(collection.requests),
            "folders_created": len(collection.folders),
            "message": f"Successfully imported '{collection.name}'",
        }
    else:
        return {"error": f"Format '{format}' not yet supported"}


@mcp.tool()
def export_collection(
    collection: str,
    output_path: str | None = None,
    format: str = "postman_v2.1",
) -> dict[str, Any]:
    """
    Export a collection to various formats.
    
    Args:
        collection: Collection name to export
        output_path: File path to write to (optional, returns JSON if not provided)
        format: Export format: postman_v2.1, openapi_3, curl, markdown
    
    Returns:
        Export path or exported data
    """
    if format == "postman_v2.1":
        data = collection_store.export_postman_collection(collection)
        if not data:
            return {"error": f"Collection '{collection}' not found"}
        
        if output_path:
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            return {
                "collection": collection,
                "output_path": output_path,
                "message": f"Exported to {output_path}",
            }
        else:
            return {"collection": collection, "data": data}
    else:
        return {"error": f"Format '{format}' not yet supported"}


# =============================================================================
# Utility Tools
# =============================================================================


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """
    Check server health and configuration status.
    
    Returns server status, version, loaded collections, history count, and capabilities.
    """
    history_count = await history_manager.get_count()
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "active_environment": variable_store.get_active_environment(),
        "collections_loaded": len(collection_store.list_collections()),
        "history_entries": history_count,
        "uptime_seconds": int(time.time() - _start_time),
        "capabilities": [
            "request_send",
            "request_inspect",
            "environments",
            "collections",
            "collection_run",
            "assertions",
            "history",
            "import_export",
        ],
    }


@mcp.tool()
def search_tools(
    query: str,
    category: str = "all",
) -> dict[str, Any]:
    """
    Search available tools by keyword or category.
    
    Use this to discover what operations are available without loading all tool definitions.
    
    Args:
        query: Search term or natural language query
        category: Filter by category: request, collection, environment, 
                 script, assertion, history, import_export, all
    
    Returns:
        List of matching tools with names and descriptions
    """
    all_tools = [
        {"name": "request_send", "category": "request", "description": "Send HTTP requests"},
        {"name": "request_inspect", "category": "request", "description": "Preview request without sending"},
        {"name": "env_create", "category": "environment", "description": "Create environment"},
        {"name": "env_switch", "category": "environment", "description": "Switch active environment"},
        {"name": "env_set_var", "category": "environment", "description": "Set variable"},
        {"name": "env_get_var", "category": "environment", "description": "Get variable value"},
        {"name": "env_list", "category": "environment", "description": "List environments"},
        {"name": "collection_create", "category": "collection", "description": "Create collection"},
        {"name": "collection_list", "category": "collection", "description": "List collections"},
        {"name": "collection_add_request", "category": "collection", "description": "Add request to collection"},
        {"name": "collection_run", "category": "collection", "description": "Run collection tests"},
        {"name": "assertion_check", "category": "assertion", "description": "Check assertions against response"},
        {"name": "history_list", "category": "history", "description": "List request history"},
        {"name": "history_get", "category": "history", "description": "Get history entry details"},
        {"name": "history_replay", "category": "history", "description": "Replay historical request"},
        {"name": "import_collection", "category": "import_export", "description": "Import from Postman/OpenAPI"},
        {"name": "export_collection", "category": "import_export", "description": "Export collection"},
        {"name": "health_check", "category": "utility", "description": "Server health status"},
    ]

    # Filter by category
    if category != "all":
        all_tools = [t for t in all_tools if t["category"] == category]

    # Filter by query
    query_lower = query.lower()
    matching = [
        t for t in all_tools
        if query_lower in t["name"].lower() or query_lower in t["description"].lower()
    ]

    return {
        "tools": matching,
        "total": len(matching),
        "query": query,
        "category": category,
    }


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    import sys
    
    # Set default environment if specified
    if DEFAULT_ENV:
        try:
            variable_store.switch_environment(DEFAULT_ENV)
        except ValueError:
            print(f"Warning: Default environment '{DEFAULT_ENV}' not found", file=sys.stderr)
    
    mcp.run()


if __name__ == "__main__":
    main()
