# API Workbench MCP Server - Feature Backlog

## Priority 1: Authentication & Security

### OAuth 2.0 Flow Support
- **Description**: Implement full OAuth 2.0 authentication flow
- **Features**:
  - Authorization Code flow
  - Client Credentials flow
  - Implicit flow
  - PKCE (Proof Key for Code Exchange) support
  - Token refresh mechanism
  - Store access/refresh tokens in environment variables
- **Use Case**: Most modern APIs (Google, GitHub, Stripe, etc.) use OAuth 2.0
- **Acceptance Criteria**:
  - `auth_type: "oauth2"` with config for grant type, auth URL, token URL, client ID/secret
  - Automatic token refresh when expired
  - Support for custom scopes

### OAuth 1.0 Support
- **Description**: Support for legacy OAuth 1.0 (Twitter API v1, some enterprise APIs)
- **Features**:
  - Consumer key/secret
  - Request token flow
  - Signature generation
- **Priority**: Lower (less common now)

### Digest Authentication
- **Description**: HTTP Digest authentication support
- **Use Case**: Some older APIs and internal systems

## Priority 2: Protocol Support

### GraphQL Support
- **Description**: First-class support for GraphQL APIs
- **Features**:
  - `request_send_graphql` tool or `body_type: "graphql"`
  - Query and mutation support
  - Variables support
  - GraphQL-specific assertions (check field existence, types)
  - Schema introspection
  - Auto-completion hints for queries (optional)
- **Use Case**: GitHub API v4, Shopify, Hasura, many modern APIs
- **Acceptance Criteria**:
  - Send GraphQL queries with variables
  - Support fragments and named operations
  - Validate GraphQL responses
  - Extract data from GraphQL responses for chaining

### WebSocket Support
- **Description**: Support for WebSocket connections
- **Features**:
  - Open WebSocket connection
  - Send/receive messages
  - Subscribe to events
  - Connection lifecycle management
- **Use Case**: Real-time APIs, chat applications, streaming data
- **Priority**: Medium

### gRPC Support
- **Description**: Support for gRPC APIs
- **Features**:
  - Proto file loading
  - Unary, streaming calls
  - Metadata (headers)
- **Use Case**: Microservices, internal APIs
- **Priority**: Lower (more specialized)

## Priority 3: Request Chaining & Dynamic Data

### Response Data Extraction
- **Description**: Extract data from responses and store in variables
- **Features**:
  - `extract_variables` in post-response script or declarative config
  - JSONPath extraction (already have jsonpath-ng dependency)
  - Regex extraction from response body
  - Header value extraction
  - Cookie extraction
- **Use Case**: Login flow (extract auth token), get resource ID then use in next request
- **Example**:
  ```yaml
  post_response:
    extract:
      - name: authToken
        source: body
        path: $.data.token
      - name: userId
        source: body
        path: $.user.id
  ```

### Request Dependencies/Chaining
- **Description**: Define request execution order and dependencies
- **Features**:
  - `depends_on` field in request config
  - Conditional execution based on previous response
  - Parallel vs sequential execution in collections
- **Use Case**: Must login before accessing protected endpoints

### Data-Driven Testing
- **Description**: Run requests with different data sets
- **Features**:
  - Load data from CSV/JSON files
  - `collection_run` with `--data-file` parameter
  - Iterate through rows and run requests
  - Variable substitution from data rows
- **Use Case**: Test with multiple users, test edge cases with various inputs
- **Example**:
  ```bash
  collection_run --collection="User API" --data-file="users.csv"
  ```

## Priority 4: Search & Discovery

### Full-Text Search Across Collections
- **Description**: Search for requests by name, URL, method, headers, body content
- **Features**:
  - `search_requests` tool
  - Search across all collections or specific collection
  - Filter by environment, folder, tag
  - Fuzzy matching
  - Return matching requests with context
- **Use Case**: "Find all requests that use the /users endpoint", "Find requests with Bearer auth"
- **Acceptance Criteria**:
  ```python
  search_requests(
      query="users",
      collection="User API",  # optional
      search_in=["name", "url", "body"],
      filter_method="POST"
  )
  ```

### Request Tagging
- **Description**: Add tags/labels to requests for organization
- **Features**:
  - Add multiple tags to a request
  - Search by tag
  - Filter collection run by tag
- **Use Case**: Tag as "auth", "crud", "admin", "deprecated"

## Priority 5: Collection Management

### Collection Operations
- **Description**: More collection management tools
- **Features**:
  - `collection_duplicate` - Clone a collection
  - `collection_merge` - Combine two collections
  - `collection_diff` - Compare two collections
  - `collection_delete` - Remove a collection
  - `collection_update` - Update collection metadata

### Request Operations
- **Description**: More request management tools
- **Features**:
  - `collection_remove_request` - Remove request from collection
  - `collection_move_request` - Move request to different folder/collection
  - `collection_duplicate_request` - Clone a request
  - `request_update` - Update existing request fields
  - Reorder requests within a folder

### Folder Operations
- **Description**: Better folder management
- **Features**:
  - Create nested folders
  - Move folders
  - Folder-level variables
  - Folder-level auth config (inherited by requests)

## Priority 6: Environment Management

### Environment Operations
- **Description**: Enhanced environment tools
- **Features**:
  - `env_clone` - Duplicate environment (staging → production)
  - `env_delete` - Remove environment
  - `env_export` - Export environment to file
  - `env_import` - Import environment from file
  - `env_diff` - Compare two environments
  - `env_merge` - Merge variables from one env to another

### Variable Scoping Enhancements
- **Description**: Better variable management
- **Features**:
  - Folder-level variables (override collection)
  - Request-level variables (override folder)
  - Computed/derived variables (e.g., `{{timestamp}}`, `{{uuid}}`)
  - Secret masking in logs and history

### Dynamic Variables
- **Description**: Built-in dynamic variables like Postman
- **Features**:
  - `{{$timestamp}}` - Current Unix timestamp
  - `{{$isoTimestamp}}` - ISO 8601 format
  - `{{$randomInt}}` - Random integer
  - `{{$guid}}` - Random GUID/UUID
  - `{{$randomEmail}}` - Random email
  - `{{$randomFirstName}}` - Random first name
- **Use Case**: Generate unique data for testing

## Priority 7: Validation & Testing

### Enhanced Assertions
- **Description**: More assertion types
- **Features**:
  - Schema validation (already have jsonschema dependency ✓)
  - Regex matching in response body
  - Header existence/value assertions (already have ✓)
  - Cookie assertions
  - Response size assertions
  - Certificate validation assertions
  - Custom assertion functions

### Test Reporting
- **Description**: Better test result reporting
- **Features**:
  - Generate HTML/Markdown test reports
  - Export results to JUnit XML format (CI/CD integration)
  - Screenshots of failures (for UI tests)
  - Performance metrics (response times, throughput)
  - Historical test trends

### Pre-request & Post-response Scripts
- **Description**: Execute JavaScript code before/after requests
- **Features**:
  - JavaScript runtime (use `py_mini_racer` or similar)
  - `pm` object like Postman (pm.environment.set, pm.test, etc.)
  - Access to request/response objects
  - Set environment variables dynamically
  - Control flow (skip request, stop collection run)
- **Use Case**: Complex authentication flows, data manipulation, custom validation
- **Note**: Already have fields in code, just need execution engine

## Priority 8: Import/Export Enhancements

### Import Formats
- **Description**: Support more import formats (already have Postman ✓)
- **Features**:
  - OpenAPI 3.x import (complete implementation)
  - Swagger 2.0 import
  - Insomnia import
  - HAR (HTTP Archive) file import
  - cURL command import (single command → request)
  - Paw import

### Export Formats
- **Description**: Export collections to various formats
- **Features**:
  - OpenAPI 3.x export
  - Markdown documentation export
  - cURL commands (already have in `request_inspect` ✓)
  - Python `requests` code
  - JavaScript `fetch` code
  - HTTPie commands
  - Swagger 2.0 export

### Documentation Generation
- **Description**: Auto-generate API documentation from collections
- **Features**:
  - Markdown format with examples
  - HTML static site
  - Include request/response examples
  - Authentication documentation
  - Interactive documentation (like Swagger UI)

## Priority 9: Performance & Monitoring

### Performance Testing
- **Description**: Load and stress testing capabilities
- **Features**:
  - `collection_load_test` tool
  - Configure virtual users, ramp-up time
  - Measure throughput, latency percentiles (p50, p95, p99)
  - Generate performance reports
- **Use Case**: Ensure API can handle expected load

### Request Monitoring
- **Description**: Monitor API endpoints over time
- **Features**:
  - Schedule periodic request execution
  - Alert on failures or slow responses
  - Uptime monitoring
  - Response time trends
- **Note**: May be out of scope for MCP, better suited for external monitoring tools

### Response Caching
- **Description**: Cache responses to avoid redundant requests
- **Features**:
  - `cache_response: true` flag
  - TTL configuration
  - Cache invalidation
  - Cache key based on URL + headers + body
- **Use Case**: Speed up collection runs, reduce API calls during development

## Priority 10: Advanced Features

### Mock Servers
- **Description**: Create mock API responses for testing
- **Features**:
  - Define mock responses per endpoint
  - Match based on path, method, headers
  - Return static or dynamic responses
  - Simulate latency and errors
- **Use Case**: Test frontend without backend, simulate error conditions

### API Proxies & Interceptors
- **Description**: Intercept and modify requests/responses
- **Features**:
  - Request interceptor (modify before sending)
  - Response interceptor (modify before processing)
  - Proxy configuration
  - SSL certificate handling
- **Use Case**: Add headers to all requests, log all traffic, modify responses

### Collaboration Features (Lower Priority)
- **Description**: Multi-user features
- **Features**:
  - Share collections with team (export/import workflow)
  - Comments on requests
  - Version control integration (Git-friendly YAML ✓)
  - Request review/approval workflow
- **Note**: Less relevant for single-user AI agent tool

## Priority 11: MCP Server Integration (NEW)

### MCP Server Discovery & Testing
- **Description**: Use API Workbench to test and document other MCP servers
- **Features**:
  - `mcp_server_discover` - Connect to an MCP server and list available tools
  - `mcp_server_test_tool` - Test an MCP tool with sample inputs
  - `mcp_server_generate_collection` - Auto-generate API collection from MCP server tools
  - Support for MCP server metadata (tool descriptions, schemas)
- **Use Case**: Test your own MCP servers, create documentation for MCP tools
- **Acceptance Criteria**:
  ```python
  mcp_server_discover(
      server_path="/path/to/mcp/server",
      protocol="stdio"  # or "http"
  )
  # Returns: list of available tools with schemas

  mcp_server_generate_collection(
      server_path="/path/to/mcp/server",
      collection_name="My MCP Server API"
  )
  # Creates a collection with one request per tool
  ```

### MCP Request Type
- **Description**: Native MCP protocol support as a request type
- **Features**:
  - `body_type: "mcp"` for MCP JSON-RPC requests
  - Tool call builder (method, params)
  - MCP-specific assertions (tool result validation)
  - Support for MCP notifications and progress
- **Use Case**: Test MCP servers as if they were REST APIs

### MCP Server Collection Template
- **Description**: Pre-built collection template for testing MCP servers
- **Features**:
  - Common MCP protocol requests (initialize, list_tools, call_tool)
  - Variables for server path, protocol
  - Assertions for MCP response format
- **Use Case**: Quickly start testing any MCP server

## Priority 12: Collection-Based Prompts & Learning

### API Hints & Skills System
- **Description**: Collection-based prompt/hints system that provides lessons and best practices for handling different APIs, similar to Claude's skills system
- **Features**:
  - `prompt_create` - Create a new learning/prompt for a collection
  - `prompt_read` - Read prompts/hints for a collection
  - `prompt_update` - Update an existing prompt
  - `prompt_delete` - Remove a prompt
  - `prompt_list` - List all prompts across collections or for a specific collection
  - Store prompts as YAML files alongside collections
  - Tag prompts by category (authentication, pagination, error handling, rate limiting, etc.)
  - Link prompts to specific requests or endpoints
- **Use Case**:
  - "Always use exponential backoff when hitting rate limits on this API"
  - "This API requires a specific date format: YYYY-MM-DDTHH:mm:ssZ"
  - "For pagination, use cursor-based approach with the `next_page_token` field"
  - "Authentication tokens expire after 1 hour, refresh proactively"
- **Example Structure**:
  ```yaml
  # collections/Anthropic API/prompts/rate-limiting.yaml
  name: Rate Limit Handling
  category: error-handling
  applies_to:
    - requests/*
  content: |
    When receiving a 429 Too Many Requests error:
    1. Check the `retry-after` header for wait time
    2. Implement exponential backoff starting at 1 second
    3. Max retry attempts: 3
    4. Log rate limit events for monitoring
  examples:
    - scenario: "Rate limited on messages endpoint"
      solution: "Wait for retry-after seconds, then retry with same request"
  ```
- **Acceptance Criteria**:
  ```python
  # CRUD operations for prompts
  prompt_create(
      collection="Anthropic API",
      name="Rate Limit Handling",
      category="error-handling",
      content="When receiving 429...",
      applies_to=["requests/*"]
  )

  prompt_list(collection="Anthropic API")
  # Returns: list of all prompts for the collection

  prompt_read(collection="Anthropic API", name="Rate Limit Handling")
  # Returns: full prompt content
  ```

### Learning from Request History
- **Description**: Auto-generate prompts/learnings from successful request patterns
- **Features**:
  - Analyze request history for patterns
  - Suggest new prompts based on common fixes or retries
  - Learn from user corrections (e.g., "this header was missing")
- **Use Case**: Build institutional knowledge about API quirks automatically

### Prompt Inheritance
- **Description**: Prompts can be inherited or overridden at different levels
- **Features**:
  - Global prompts (apply to all collections)
  - Collection-level prompts
  - Folder-level prompts
  - Request-level prompts (most specific)
  - Inheritance chain with override capability
- **Use Case**: "All APIs should handle 5xx errors with retry" (global) but "This specific endpoint should not retry" (request-level override)

## Priority 13: Developer Experience (was 12)

### Request Templates
- **Description**: Pre-built request templates for common patterns
- **Features**:
  - CRUD operations template
  - Pagination template (offset, cursor-based)
  - File upload template
  - Webhook testing template
  - Authentication flow templates (OAuth, JWT)
- **Use Case**: Quickly scaffold common API patterns

### Code Generation
- **Description**: Generate client code from collections
- **Features**:
  - Generate Python SDK from collection
  - Generate TypeScript/JavaScript client
  - Generate OpenAPI spec from collection
- **Use Case**: Create API clients for applications

### CLI Improvements
- **Description**: Better command-line interface (if running standalone)
- **Features**:
  - Interactive mode
  - Colored output
  - Progress bars for collection runs
  - Export results to different formats
- **Note**: May not apply to MCP context

### Validation & Linting
- **Description**: Validate collections and requests before execution
- **Features**:
  - `collection_validate` - Check for errors in collection
  - Warn about missing required headers
  - Warn about potentially sensitive data in requests
  - Check for broken variable references
  - Suggest best practices

## Priority 14: Quality of Life (was 13)

### Request History Enhancements
- **Description**: Better history management
- **Features**:
  - `history_clear` - Clear history (all or filtered)
  - `history_export` - Export history to file
  - `history_search` - Full-text search in history
  - Pin favorite requests in history
  - History retention policies (auto-delete old entries)

### ✅ Save Request & Response to File (COMPLETED)
- **Description**: Export request and response data to files for documentation or debugging
- **Implementation**: Added as optional parameters to `request_send` tool
- **Features**:
  - `save_to_file` parameter - Save to file path or True for auto-generated filename
  - `save_format` parameter - Supports JSON, YAML, Markdown, HTTP archive (.har)
  - Auto-generate filenames with timestamp and sanitized URL
  - Streaming support - Captures all SSE events for LLM APIs
  - Security - Masks sensitive headers (Authorization, API keys) in Markdown format
- **Usage**:
  ```python
  # Basic save
  request_send(
      method="POST",
      url="https://api.example.com/users",
      body={"name": "John"},
      save_to_file=True,  # Auto-generates filename
      save_format="json"
  )

  # Streaming + save for LLM debugging
  request_send(
      method="POST",
      url="https://api.anthropic.com/v1/messages",
      body={"model": "claude-3-5-sonnet", "stream": true},
      stream=True,  # Capture all SSE events
      save_to_file="llm_debug.json",
      save_format="json"
  )
  ```

### Favorites/Bookmarks
- **Description**: Quick access to frequently used requests
- **Features**:
  - Star/favorite requests
  - `request_list_favorites` - List all favorites
  - Quick execute from favorites

### Request Comparison
- **Description**: Compare two requests or responses
- **Features**:
  - `request_compare` - Diff two requests
  - `response_compare` - Diff two responses
  - Visual diff output
- **Use Case**: Compare staging vs production responses

### Bulk Operations
- **Description**: Perform operations on multiple items
- **Features**:
  - Update auth for all requests in a collection
  - Find and replace in request URLs/bodies
  - Batch tag assignment
  - Batch variable updates across environments

## Implementation Notes

### Quick Wins (Low Effort, High Value)
1. Response data extraction (JSONPath already available)
2. Environment cloning (`env_clone`)
3. Request tagging
4. Dynamic variables (`{{$timestamp}}`, etc.)
5. Full-text search across collections
6. MCP server discovery and testing
7. Collection-based prompts/hints CRUD (simple YAML storage)

### High Impact Features
1. OAuth 2.0 flow
2. GraphQL support
3. Request chaining/dependencies
4. Pre-request & post-response scripts
5. Data-driven testing
6. MCP server integration
7. Collection-based prompts & learning system (skills for APIs)

### Nice to Have (Lower Priority)
1. Mock servers
2. WebSocket support
3. gRPC support
4. Performance testing
5. Code generation
6. Collaboration features

### Technical Debt
1. Implement script execution engine for pre-request/post-response
2. Add proper logging framework
3. Add metrics/telemetry (optional)
4. Improve error messages
5. Add rate limiting support
6. Add retry logic with exponential backoff

## Roadmap Suggestion

### Phase 1 (Core Enhancements)
- OAuth 2.0 support
- Response data extraction
- Environment cloning
- Full-text search

### Phase 2 (Protocol Support)
- GraphQL support
- MCP server integration
- WebSocket support (basic)

### Phase 3 (Advanced Testing)
- Request chaining/dependencies
- Data-driven testing
- Pre-request/post-response scripts
- Enhanced assertions

### Phase 4 (Developer Experience)
- Request templates
- Documentation generation
- Bulk operations
- Request comparison

### Phase 5 (Enterprise Features)
- Performance testing
- Mock servers
- Advanced monitoring
- Code generation
