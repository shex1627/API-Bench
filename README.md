# API Workbench MCP Server

A comprehensive MCP (Model Context Protocol) server for API testing - an open source Postman replacement designed specifically for AI agents.

## Features

- 🚀 **Send HTTP Requests** - All methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- 🔐 **Authentication** - Basic, Bearer, API Key, OAuth2
- 📁 **Collections** - Organize requests into collections with folders
- 🌍 **Environments** - Manage variables across different environments
- ✅ **Assertions** - Validate responses with JSONPath, status codes, headers
- 📜 **History** - Track and replay past requests
- 📥 **Import/Export** - Postman collections, OpenAPI specs
- 🔄 **Variable Substitution** - Use `{{variables}}` in URLs, headers, body

## Design Philosophy

This server is designed following [Anthropic's best practices](https://www.anthropic.com/engineering/writing-tools-for-agents) for building effective tools for AI agents:

1. **Token Efficiency** - `response_format` parameter controls verbosity (concise vs detailed)
2. **Consolidated Tools** - High-impact tools that combine common workflows
3. **Helpful Errors** - Actionable suggestions, not just error codes
4. **Progressive Discovery** - `search_tools` for on-demand tool loading
5. **Clear Namespacing** - `request_*`, `collection_*`, `env_*` prefixes

## Installation

```bash
pip install api-workbench-mcp
```

Or install from source:

```bash
git clone https://github.com/yourusername/api-workbench-mcp.git
cd api-workbench-mcp
pip install -e .
```

## Quick Start

### Run the Server

```bash
# Run with default settings
api-workbench-mcp

# Or with Python
python -m api_workbench_mcp
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "api-workbench": {
      "command": "api-workbench-mcp",
      "env": {
        "API_WORKBENCH_COLLECTIONS": "/Users/shadowclone/Desktop/Code/api-workbench-mcp/collections",
        "API_WORKBENCH_DEFAULT_ENV": "development"
      }
    }
  }
}
```

### Using with Claude Code

```bash
claude mcp add api-workbench -- api-workbench-mcp
```

## Tools Reference

### Request Tools

#### `request_send`
Send an HTTP request with full control over method, headers, body, and auth.

```python
# Simple GET
request_send(method="GET", url="https://api.example.com/users")

# POST with JSON body
request_send(
    method="POST",
    url="{{baseUrl}}/users",
    body={"name": "John", "email": "john@example.com"},
    auth_type="bearer",
    auth_credentials={"token": "{{authToken}}"}
)

# Detailed response format
request_send(
    method="GET",
    url="https://api.example.com/users",
    response_format="detailed"  # Includes headers, cookies, redirects
)

# Variable overrides - temporary changes without modifying environment
request_send(
    method="POST",
    url="{{baseUrl}}/messages",
    body={
        "model": "{{model}}",
        "messages": [{"role": "user", "content": "{{prompt}}"}]
    },
    variable_overrides={
        "model": "claude-3-opus-20240229",
        "prompt": "What is the capital of France?"
    }
)
```

#### `request_inspect`
Preview a request without sending (dry run). Returns resolved URL after variable substitution and equivalent cURL command.

### Environment Tools

#### `env_create`
Create a new environment with variables.

```python
env_create(
    name="production",
    variables={
        "baseUrl": "https://api.prod.com",
        "apiKey": "secret123"
    }
)
```

#### `env_switch`
Switch the active environment.

```python
env_switch(name="staging")
```

#### `env_set_var` / `env_get_var`
Set or get individual variables.

```python
env_set_var(name="authToken", value="xyz789", secret=True)
```

### Collection Tools

#### `collection_create`
Create a new API collection.

```python
collection_create(
    name="User API",
    description="User management endpoints",
    folders=["Auth", "Users", "Admin"],
    base_url="https://api.example.com"
)
```

#### `collection_add_request`
Add a request to a collection.

```python
collection_add_request(
    collection="User API",
    name="Create User",
    method="POST",
    url="{{baseUrl}}/users",
    body={"name": "{{userName}}"},
    folder="Users"
)
```

#### `collection_run`
Run all requests in a collection and return test results.

```python
collection_run(
    collection="User API",
    environment="staging",
    iterations=3,
    response_format="detailed"
)
```

### Assertion Tools

#### `assertion_check`
Run assertions against a response without scripts.

```python
assertion_check(
    response_status=200,
    response_body={"id": 1, "name": "John"},
    assertions=[
        {"type": "status", "expected": 200},
        {"type": "body_jsonpath", "target": "$.id", "operator": "exists"},
        {"type": "body_jsonpath", "target": "$.name", "expected": "John"}
    ]
)
```

### History Tools

#### `history_list`
List recent request history.

```python
history_list(limit=10, method="POST", url_pattern="/users")
```

#### `history_replay`
Re-execute a historical request with optional modifications.

```python
history_replay(entry_id="abc123", environment="production")
```

### Import/Export Tools

#### `import_collection`
Import from Postman or OpenAPI.

```python
import_collection(source="./postman_collection.json", format="postman_v2.1")
```

#### `export_collection`
Export to various formats.

```python
export_collection(collection="User API", output_path="./export.json")
```

### Utility Tools

#### `health_check`
Check server health and configuration.

#### `search_tools`
Discover available tools by keyword or category.

```python
search_tools(query="run tests", category="collection")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_WORKBENCH_COLLECTIONS` | Collections directory | `./collections` |
| `API_WORKBENCH_HISTORY_DB` | History database path | `./history.db` |
| `API_WORKBENCH_ENVIRONMENTS` | Environments storage directory | `./environments` |
| `API_WORKBENCH_DEFAULT_ENV` | Default environment | None |

**Note**: Environments are automatically persisted to disk. Secret variables are encrypted using machine-specific keys for security.

## Collection Storage Format

Collections are stored as YAML files for human readability and git-friendliness:

```
collections/
├── user-api/
│   ├── collection.yaml
│   └── requests/
│       ├── create-user.yaml
│       ├── get-user.yaml
│       └── delete-user.yaml
```

### collection.yaml

```yaml
name: User API
description: User management endpoints
base_url: "{{baseUrl}}"
folders:
  - name: Auth
    requests:
      - login
      - logout
  - name: Users
    requests:
      - create-user
      - get-user
```

### requests/create-user.yaml

```yaml
name: Create User
method: POST
url: "{{baseUrl}}/users"
headers:
  Content-Type: application/json
body:
  type: json
  content:
    name: "{{userName}}"
    email: "{{userEmail}}"
postresponse: |
  pm.test("Status is 201", () => {
    pm.response.to.have.status(201);
  });
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/api-workbench-mcp.git
cd api-workbench-mcp
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/
```

### Linting

```bash
ruff check src/
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Designed following [Anthropic's MCP best practices](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Inspired by [Bruno](https://www.usebruno.com/) and Postman
- Built with the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
