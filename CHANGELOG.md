# Changelog

All notable changes to the API Workbench MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Variable Overrides**: New `variable_overrides` parameter in `request_send` tool allows temporary variable substitution without modifying environment variables. Perfect for quick testing and ad-hoc requests.
  - Overrides take precedence over environment/collection/global variables
  - Doesn't modify the actual environment
  - Supports nested objects and arrays in request body
  - Example: `variable_overrides={"model": "claude-3-opus", "prompt": "Custom prompt"}`

- **Environment Persistence**: Environments and variables are now automatically saved to disk and restored on server restart
  - Auto-save on every environment/variable change
  - Secret variables are encrypted using machine-specific keys (AES-256 via Fernet)
  - Environments stored as JSON files in configurable directory
  - Active environment selection persists across restarts
  - Configure storage location with `API_WORKBENCH_ENVIRONMENTS` environment variable
  - Encryption keys derived from machine ID + username for consistency

### Fixed
- Fixed database path issue when running through Claude Desktop by adding `API_WORKBENCH_HISTORY_DB` environment variable support

## [0.1.0] - 2025-01-15

### Added
- Initial release
- HTTP request execution with all major methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- Authentication support (Basic, Bearer, API Key, OAuth2)
- Environment and variable management
- Collection organization with folders
- Request history tracking with SQLite
- Response assertions (status, JSONPath, headers, response time)
- Import/Export (Postman collections)
- Variable substitution with `{{variable}}` syntax
- Request inspection (dry run with cURL generation)
- Token-efficient response formatting (concise vs detailed)
- Health check and tool discovery
