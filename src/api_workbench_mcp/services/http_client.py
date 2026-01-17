"""
HTTP Client Service.

Handles HTTP request execution with support for various auth types,
body formats, and response handling.
"""

import json
import time
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

import httpx

from ..types import (
    ApiKeyAuth,
    AuthConfig,
    AuthType,
    BasicAuth,
    BearerAuth,
    BodyType,
    HttpMethod,
    RequestConfig,
    RequestInspectOutput,
    RequestSendInput,
    RequestSendOutput,
    ResponseData,
    ResponseFormat,
)
from .variable_store import VariableStore


class HttpClient:
    """
    HTTP client for executing API requests.
    
    Features:
    - Variable substitution
    - Multiple auth types
    - Various body formats
    - Response formatting (concise/detailed)
    - Automatic truncation for large responses
    """

    def __init__(self, variable_store: VariableStore) -> None:
        self._variable_store = variable_store
        self._default_timeout = 30.0  # seconds

    async def send_request(
        self,
        input_data: RequestSendInput,
        collection: str | None = None,
    ) -> RequestSendOutput:
        """
        Send an HTTP request and return the response.

        Handles variable substitution, authentication, and response formatting.
        """
        # Resolve variables (with optional overrides)
        env = input_data.environment
        overrides = input_data.variable_overrides if input_data.variable_overrides else None
        url = self._variable_store.substitute(input_data.url, collection, env, overrides)
        headers = {
            k: self._variable_store.substitute(v, collection, env, overrides)
            for k, v in input_data.headers.items()
        }
        query_params = {
            k: self._variable_store.substitute(v, collection, env, overrides)
            for k, v in input_data.query_params.items()
        }

        # Add query params to URL
        if query_params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(query_params)}"

        # Prepare body
        body, content_type = self._prepare_body(input_data.body, input_data.body_type, collection, env, overrides)
        if content_type and "Content-Type" not in headers:
            headers["Content-Type"] = content_type

        # Apply authentication
        headers = self._apply_auth(headers, input_data.auth, collection, env, overrides)

        # Execute request
        timeout = input_data.timeout / 1000.0  # Convert to seconds

        start_time = time.monotonic()

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=input_data.follow_redirects,
            verify=input_data.validate_ssl,
        ) as client:
            try:
                # Handle streaming requests
                if input_data.stream:
                    streaming_events: list[str] = []
                    accumulated_text = ""
                    first_chunk_time: int | None = None
                    last_chunk_time: int | None = None

                    async with client.stream(
                        method=input_data.method.value,
                        url=url,
                        headers=headers,
                        content=body if isinstance(body, (str, bytes)) else None,
                        json=body if isinstance(body, dict) and input_data.body_type == BodyType.JSON else None,
                        data=body if isinstance(body, dict) and input_data.body_type == BodyType.FORM else None,
                    ) as response:
                        async for chunk in response.aiter_text():
                            chunk_time = int((time.monotonic() - start_time) * 1000)
                            if first_chunk_time is None:
                                first_chunk_time = chunk_time
                            last_chunk_time = chunk_time

                            streaming_events.append(chunk)
                            accumulated_text += chunk

                    duration = int((time.monotonic() - start_time) * 1000)

                    # Try to parse accumulated response as JSON
                    try:
                        parsed_body = json.loads(accumulated_text)
                    except (json.JSONDecodeError, ValueError):
                        parsed_body = accumulated_text

                    # Build response data with streaming info
                    response_data = ResponseData(
                        status=response.status_code,
                        status_text=response.reason_phrase or "",
                        headers=dict(response.headers),
                        body=parsed_body,
                        raw_body=accumulated_text,
                        cookies=dict(response.cookies),
                        duration=duration,
                        size=len(accumulated_text.encode('utf-8')),
                        redirects=[],
                    )

                    # Add streaming metadata
                    streaming_metadata = {
                        "events": streaming_events,
                        "event_count": len(streaming_events),
                        "first_chunk_time_ms": first_chunk_time or 0,
                        "last_chunk_time_ms": last_chunk_time or 0,
                    }

                    output = self._format_output(
                        response_data,
                        input_data.response_format,
                        input_data.max_response_size,
                    )
                    output.streaming = streaming_metadata
                    return output

                else:
                    # Non-streaming request (original behavior)
                    response = await client.request(
                        method=input_data.method.value,
                        url=url,
                        headers=headers,
                        content=body if isinstance(body, (str, bytes)) else None,
                        json=body if isinstance(body, dict) and input_data.body_type == BodyType.JSON else None,
                        data=body if isinstance(body, dict) and input_data.body_type == BodyType.FORM else None,
                    )

                    duration = int((time.monotonic() - start_time) * 1000)

                    # Parse response
                    response_data = self._parse_response(response, duration)

                    # Format output
                    return self._format_output(
                        response_data,
                        input_data.response_format,
                        input_data.max_response_size,
                    )

            except httpx.TimeoutException:
                return RequestSendOutput(
                    status=0,
                    status_text="Timeout",
                    duration=int((time.monotonic() - start_time) * 1000),
                    body={"error": f"Request timed out after {input_data.timeout}ms"},
                )
            except httpx.RequestError as e:
                return RequestSendOutput(
                    status=0,
                    status_text="Connection Error",
                    duration=int((time.monotonic() - start_time) * 1000),
                    body={"error": str(e)},
                )

    def inspect_request(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
        collection: str | None = None,
        environment: str | None = None,
    ) -> RequestInspectOutput:
        """
        Inspect a request without sending it (dry run).
        
        Returns the resolved URL, headers, body, and cURL command.
        """
        headers = headers or {}
        
        # Resolve variables
        resolved_url = self._variable_store.substitute(url, collection, environment)
        resolved_headers = {
            k: self._variable_store.substitute(v, collection, environment)
            for k, v in headers.items()
        }
        
        resolved_body = None
        if body:
            if isinstance(body, str):
                resolved_body = self._variable_store.substitute(body, collection, environment)
            elif isinstance(body, dict):
                resolved_body = self._variable_store.substitute_dict(body, collection, environment)

        # Generate cURL command
        curl_cmd = self._generate_curl(method, resolved_url, resolved_headers, resolved_body)

        # Check for warnings
        warnings: list[str] = []
        if "{{" in resolved_url:
            warnings.append("URL contains unresolved variables")
        for key, value in resolved_headers.items():
            if "{{" in value:
                warnings.append(f"Header '{key}' contains unresolved variables")

        return RequestInspectOutput(
            resolved_url=resolved_url,
            resolved_headers=resolved_headers,
            resolved_body=resolved_body,
            curl_command=curl_cmd,
            warnings=warnings,
        )

    def _prepare_body(
        self,
        body: Any | None,
        body_type: BodyType,
        collection: str | None,
        environment: str | None,
        overrides: dict[str, str] | None = None,
    ) -> tuple[Any, str | None]:
        """Prepare the request body and determine content type."""
        if body is None:
            return None, None

        content_type: str | None = None

        if body_type == BodyType.JSON:
            if isinstance(body, dict):
                body = self._variable_store.substitute_dict(body, collection, environment, overrides)
            elif isinstance(body, str):
                body = self._variable_store.substitute(body, collection, environment, overrides)
            content_type = "application/json"

        elif body_type == BodyType.FORM:
            if isinstance(body, dict):
                body = {
                    k: self._variable_store.substitute(str(v), collection, environment, overrides)
                    for k, v in body.items()
                }
            content_type = "application/x-www-form-urlencoded"

        elif body_type == BodyType.RAW:
            if isinstance(body, str):
                body = self._variable_store.substitute(body, collection, environment, overrides)
            content_type = "text/plain"

        elif body_type == BodyType.MULTIPART:
            content_type = None  # Let httpx handle it

        return body, content_type

    def _apply_auth(
        self,
        headers: dict[str, str],
        auth: AuthConfig | None,
        collection: str | None,
        environment: str | None,
        overrides: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Apply authentication to headers."""
        if auth is None or auth.type == AuthType.NONE:
            return headers

        headers = headers.copy()

        if auth.type == AuthType.BASIC and auth.basic:
            import base64
            username = self._variable_store.substitute(auth.basic.username, collection, environment, overrides)
            password = self._variable_store.substitute(auth.basic.password, collection, environment, overrides)
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif auth.type == AuthType.BEARER and auth.bearer:
            token = self._variable_store.substitute(auth.bearer.token, collection, environment, overrides)
            headers["Authorization"] = f"Bearer {token}"

        elif auth.type == AuthType.API_KEY and auth.api_key:
            key = self._variable_store.substitute(auth.api_key.key, collection, environment, overrides)
            value = self._variable_store.substitute(auth.api_key.value, collection, environment, overrides)
            if auth.api_key.location == "header":
                headers[key] = value
            # Query param auth is handled in URL construction

        elif auth.type == AuthType.OAUTH2 and auth.oauth2:
            token = self._variable_store.substitute(auth.oauth2.access_token, collection, environment, overrides)
            token_type = auth.oauth2.token_type
            headers["Authorization"] = f"{token_type} {token}"

        return headers

    def _parse_response(self, response: httpx.Response, duration: int) -> ResponseData:
        """Parse the HTTP response into a ResponseData object."""
        # Try to parse body as JSON
        body: Any = None
        raw_body = response.text
        
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError):
            body = raw_body

        # Extract cookies
        cookies = dict(response.cookies)

        # Track redirects
        redirects = [str(r.url) for r in response.history]

        return ResponseData(
            status=response.status_code,
            status_text=response.reason_phrase or "",
            headers=dict(response.headers),
            body=body,
            raw_body=raw_body,
            cookies=cookies,
            duration=duration,
            size=len(response.content),
            redirects=redirects,
        )

    def _format_output(
        self,
        response: ResponseData,
        format: ResponseFormat,
        max_size: int,
    ) -> RequestSendOutput:
        """Format the response according to the requested format."""
        truncated = False
        truncation_message: str | None = None

        # Check if truncation is needed
        body = response.body
        if body and isinstance(body, (str, dict, list)):
            body_str = json.dumps(body) if isinstance(body, (dict, list)) else body
            estimated_tokens = len(body_str) // 4  # Rough estimate
            
            if estimated_tokens > max_size:
                truncated = True
                truncation_message = (
                    f"Response truncated from ~{estimated_tokens} to ~{max_size} tokens. "
                    "Use filters or specific endpoints for complete data."
                )
                # Truncate the body
                if isinstance(body, str):
                    body = body[: max_size * 4] + "... [truncated]"
                elif isinstance(body, list):
                    # Keep first N items
                    max_items = max(1, max_size // 100)
                    body = body[:max_items]
                    if len(response.body) > max_items:
                        body.append({"_truncated": f"Showing {max_items} of {len(response.body)} items"})

        if format == ResponseFormat.CONCISE:
            return RequestSendOutput(
                status=response.status,
                status_text=response.status_text,
                duration=response.duration,
                body=body,
                truncated=truncated,
                truncation_message=truncation_message,
            )
        else:  # DETAILED
            return RequestSendOutput(
                status=response.status,
                status_text=response.status_text,
                duration=response.duration,
                body=body,
                headers=response.headers,
                cookies=response.cookies,
                redirects=response.redirects if response.redirects else None,
                raw_body=response.raw_body if len(response.raw_body or "") < 10000 else None,
                size=response.size,
                truncated=truncated,
                truncation_message=truncation_message,
            )

    def _generate_curl(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str],
        body: Any | None,
    ) -> str:
        """Generate an equivalent cURL command."""
        parts = ["curl", "-X", method.value]

        for key, value in headers.items():
            # Escape single quotes in header values
            escaped_value = value.replace("'", "'\\''")
            parts.append("-H")
            parts.append(f"'{key}: {escaped_value}'")

        if body:
            if isinstance(body, dict):
                body_str = json.dumps(body)
            else:
                body_str = str(body)
            # Escape single quotes in body
            escaped_body = body_str.replace("'", "'\\''")
            parts.append("-d")
            parts.append(f"'{escaped_body}'")

        parts.append(f"'{url}'")

        return " ".join(parts)
