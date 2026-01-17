"""
Type definitions for API Workbench MCP Server.

Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class HttpMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class BodyType(str, Enum):
    """Request body content types."""

    JSON = "json"
    FORM = "form"
    MULTIPART = "multipart"
    RAW = "raw"
    BINARY = "binary"


class ResponseFormat(str, Enum):
    """Response verbosity levels (Anthropic best practice)."""

    CONCISE = "concise"
    DETAILED = "detailed"


class VariableScope(str, Enum):
    """Variable scope levels."""

    GLOBAL = "global"
    COLLECTION = "collection"
    ENVIRONMENT = "environment"


class AssertionType(str, Enum):
    """Types of response assertions."""

    STATUS = "status"
    BODY_CONTAINS = "body_contains"
    BODY_EQUALS = "body_equals"
    BODY_JSONPATH = "body_jsonpath"
    HEADER_EXISTS = "header_exists"
    HEADER_EQUALS = "header_equals"
    RESPONSE_TIME = "response_time"
    JSON_SCHEMA = "json_schema"


class AssertionOperator(str, Enum):
    """Comparison operators for assertions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    LT = "lt"
    GT = "gt"
    LTE = "lte"
    GTE = "gte"


# ============================================================================
# Authentication Models
# ============================================================================


class BasicAuth(BaseModel):
    """Basic authentication credentials."""

    username: str
    password: str


class BearerAuth(BaseModel):
    """Bearer token authentication."""

    token: str


class ApiKeyAuth(BaseModel):
    """API key authentication."""

    key: str
    value: str
    location: Literal["header", "query"] = "header"


class OAuth2Auth(BaseModel):
    """OAuth2 authentication (simplified)."""

    access_token: str
    token_type: str = "Bearer"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: AuthType = AuthType.NONE
    basic: BasicAuth | None = None
    bearer: BearerAuth | None = None
    api_key: ApiKeyAuth | None = None
    oauth2: OAuth2Auth | None = None


# ============================================================================
# Request/Response Models
# ============================================================================


class RequestConfig(BaseModel):
    """HTTP request configuration."""

    method: HttpMethod
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    body_type: BodyType = BodyType.JSON
    auth: AuthConfig | None = None
    timeout: int = Field(default=30000, description="Timeout in milliseconds")
    follow_redirects: bool = True
    validate_ssl: bool = True


class ResponseData(BaseModel):
    """HTTP response data."""

    status: int
    status_text: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    raw_body: str | None = None
    cookies: dict[str, str] = Field(default_factory=dict)
    duration: int = Field(description="Duration in milliseconds")
    size: int = Field(default=0, description="Response size in bytes")
    redirects: list[str] = Field(default_factory=list)


class RequestSendInput(BaseModel):
    """Input for request_send tool."""

    method: HttpMethod
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    body_type: BodyType = BodyType.JSON
    auth: AuthConfig | None = None
    timeout: int = Field(default=30000, ge=1000, le=300000)
    follow_redirects: bool = True
    validate_ssl: bool = True
    environment: str | None = Field(
        default=None, description="Environment to use for variable substitution"
    )
    variable_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Temporary variable overrides for this request only"
    )
    response_format: ResponseFormat = ResponseFormat.CONCISE
    max_response_size: int = Field(default=25000, description="Max response tokens")
    stream: bool = Field(default=False, description="Enable streaming for SSE/LLM APIs")


class RequestSendOutput(BaseModel):
    """Output for request_send tool."""

    # Always included (concise)
    status: int
    status_text: str
    duration: int
    body: Any | None = None

    # Detailed format only
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    redirects: list[str] | None = None
    raw_body: str | None = None
    size: int | None = None

    # Metadata
    truncated: bool = False
    truncation_message: str | None = None

    # Streaming data (when stream=True)
    streaming: dict[str, Any] | None = Field(
        default=None,
        description="Streaming events and metadata (events, event_count, timings)"
    )


class RequestInspectInput(BaseModel):
    """Input for request_inspect (dry run) tool."""

    method: HttpMethod
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    environment: str | None = None


class RequestInspectOutput(BaseModel):
    """Output for request_inspect tool."""

    resolved_url: str
    resolved_headers: dict[str, str]
    resolved_body: Any | None = None
    curl_command: str
    warnings: list[str] = Field(default_factory=list)


# ============================================================================
# Environment Models
# ============================================================================


class EnvironmentVariable(BaseModel):
    """A single environment variable."""

    value: str
    secret: bool = Field(default=False, description="Mask value in responses")


class Environment(BaseModel):
    """Environment configuration."""

    name: str
    description: str | None = None
    variables: dict[str, EnvironmentVariable] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EnvCreateInput(BaseModel):
    """Input for env_create tool."""

    name: str
    variables: dict[str, str | EnvironmentVariable] = Field(default_factory=dict)
    description: str | None = None


class EnvSetVarInput(BaseModel):
    """Input for env_set_var tool."""

    name: str
    value: str
    scope: VariableScope = VariableScope.ENVIRONMENT
    environment: str | None = None
    secret: bool = False


class EnvListInput(BaseModel):
    """Input for env_list tool."""

    show_variables: bool = False
    environment: str | None = None
    mask_secrets: bool = True


# ============================================================================
# Collection Models
# ============================================================================


class CollectionRequest(BaseModel):
    """A request within a collection."""

    name: str
    method: HttpMethod
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    body_type: BodyType = BodyType.JSON
    auth: AuthConfig | None = None
    pre_request_script: str | None = None
    post_response_script: str | None = None
    assertions: list["AssertionConfig"] = Field(default_factory=list)


class CollectionFolder(BaseModel):
    """A folder within a collection."""

    name: str
    description: str | None = None
    requests: list[str] = Field(default_factory=list)  # Request names
    folders: list["CollectionFolder"] = Field(default_factory=list)


class Collection(BaseModel):
    """API collection configuration."""

    name: str
    description: str | None = None
    base_url: str | None = None
    auth: AuthConfig | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    folders: list[CollectionFolder] = Field(default_factory=list)
    requests: dict[str, CollectionRequest] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CollectionCreateInput(BaseModel):
    """Input for collection_create tool."""

    name: str
    description: str | None = None
    folders: list[str] = Field(default_factory=list)
    base_url: str | None = None
    auth: AuthConfig | None = None


class CollectionRunInput(BaseModel):
    """Input for collection_run tool."""

    collection: str
    folder: str | None = None
    environment: str | None = None
    iterations: int = Field(default=1, ge=1, le=100)
    delay: int = Field(default=0, ge=0, description="Delay between requests in ms")
    stop_on_error: bool = False
    data_file: str | None = None
    response_format: Literal["summary", "detailed", "verbose"] = "summary"
    generate_report: "ReportConfig | None" = None


class ReportConfig(BaseModel):
    """Report generation configuration."""

    format: Literal["json", "junit", "html"]
    output_path: str | None = None


class CollectionRunSummary(BaseModel):
    """Summary of a collection run."""

    total: int
    passed: int
    failed: int
    skipped: int
    duration: int


class RequestResult(BaseModel):
    """Result of a single request execution."""

    name: str
    status: Literal["passed", "failed", "skipped"]
    response_status: int | None = None
    duration: int
    assertions: "AssertionSummary | None" = None
    error: str | None = None


class AssertionSummary(BaseModel):
    """Summary of assertions for a request."""

    total: int
    passed: int
    failed: int


class CollectionRunOutput(BaseModel):
    """Output for collection_run tool."""

    summary: CollectionRunSummary
    results: list[RequestResult] = Field(default_factory=list)
    report_path: str | None = None


# ============================================================================
# Assertion Models
# ============================================================================


class AssertionConfig(BaseModel):
    """Configuration for a single assertion."""

    type: AssertionType
    target: str | None = None  # JSONPath, header name, etc.
    expected: Any | None = None
    operator: AssertionOperator = AssertionOperator.EQUALS


class AssertionResult(BaseModel):
    """Result of a single assertion."""

    name: str
    passed: bool
    actual: Any | None = None
    expected: Any | None = None
    message: str | None = None


class AssertionCheckInput(BaseModel):
    """Input for assertion_check tool."""

    response: dict[str, Any]  # status, body, headers
    assertions: list[AssertionConfig]


class AssertionCheckOutput(BaseModel):
    """Output for assertion_check tool."""

    passed: bool
    results: list[AssertionResult]


# ============================================================================
# Script Models
# ============================================================================


class ScriptContext(BaseModel):
    """Context available to scripts."""

    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    environment: str | None = None


class ScriptRunInput(BaseModel):
    """Input for script_run tool."""

    script: str
    context: ScriptContext
    phase: Literal["prerequest", "postresponse", "standalone"]


class ScriptRunOutput(BaseModel):
    """Output for script_run tool."""

    success: bool
    logs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    variables_set: dict[str, str] = Field(default_factory=dict)
    assertions: list[AssertionResult] = Field(default_factory=list)


# ============================================================================
# History Models
# ============================================================================


class HistoryEntry(BaseModel):
    """A single history entry."""

    id: str
    method: HttpMethod
    url: str
    status: int
    duration: int
    timestamp: datetime
    environment: str | None = None


class HistoryListInput(BaseModel):
    """Input for history_list tool."""

    limit: int = Field(default=20, ge=1, le=100)
    method: HttpMethod | None = None
    url_pattern: str | None = None
    status_code: int | None = None
    response_format: ResponseFormat = ResponseFormat.CONCISE


class HistoryListOutput(BaseModel):
    """Output for history_list tool."""

    entries: list[HistoryEntry]
    total: int


# ============================================================================
# Import/Export Models
# ============================================================================


class ImportFormat(str, Enum):
    """Supported import formats."""

    POSTMAN_V2 = "postman_v2"
    POSTMAN_V2_1 = "postman_v2.1"
    OPENAPI_3 = "openapi_3"
    SWAGGER_2 = "swagger_2"
    CURL = "curl"
    HAR = "har"


class ExportFormat(str, Enum):
    """Supported export formats."""

    POSTMAN_V2_1 = "postman_v2.1"
    OPENAPI_3 = "openapi_3"
    CURL = "curl"
    MARKDOWN = "markdown"


class ImportCollectionInput(BaseModel):
    """Input for import_collection tool."""

    source: str  # File path or URL
    format: ImportFormat
    target_collection: str | None = None


class ImportCollectionOutput(BaseModel):
    """Output for import_collection tool."""

    collection: str
    requests_imported: int
    folders_created: int
    environments_imported: int = 0
    warnings: list[str] = Field(default_factory=list)


class ExportCollectionInput(BaseModel):
    """Input for export_collection tool."""

    collection: str
    format: ExportFormat
    output_path: str | None = None
    include_environment: str | None = None


# ============================================================================
# Utility Models
# ============================================================================


class HealthCheckOutput(BaseModel):
    """Output for health_check tool."""

    status: Literal["healthy", "degraded"]
    version: str
    active_environment: str | None = None
    collections_loaded: int
    history_entries: int
    uptime: int
    capabilities: list[str]


class SearchToolsInput(BaseModel):
    """Input for search_tools tool."""

    query: str
    category: Literal[
        "request", "collection", "environment", "script", "assertion", "history", "all"
    ] = "all"
    detail_level: Literal["names", "summary", "full"] = "summary"


class ToolInfo(BaseModel):
    """Information about a tool."""

    name: str
    category: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class SearchToolsOutput(BaseModel):
    """Output for search_tools tool."""

    tools: list[ToolInfo]
    total: int


# Enable forward references
CollectionFolder.model_rebuild()
CollectionRunInput.model_rebuild()
