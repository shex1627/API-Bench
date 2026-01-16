"""
Assertion Engine Service.

Validates HTTP responses against various assertion types.
"""

import json
import re
from typing import Any

from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError
import jsonschema

from ..types import (
    AssertionCheckInput,
    AssertionCheckOutput,
    AssertionConfig,
    AssertionOperator,
    AssertionResult,
    AssertionType,
)


class AssertionEngine:
    """
    Validates HTTP responses against configured assertions.
    
    Supports:
    - Status code checks
    - Body content validation (contains, equals, JSONPath)
    - Header validation
    - Response time checks
    - JSON schema validation
    """

    def check_assertions(
        self,
        input_data: AssertionCheckInput,
    ) -> AssertionCheckOutput:
        """
        Run all assertions against a response.
        
        Returns detailed results for each assertion.
        """
        results: list[AssertionResult] = []
        all_passed = True

        for assertion in input_data.assertions:
            result = self._check_single_assertion(assertion, input_data.response)
            results.append(result)
            if not result.passed:
                all_passed = False

        return AssertionCheckOutput(passed=all_passed, results=results)

    def _check_single_assertion(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check a single assertion against the response."""
        try:
            if assertion.type == AssertionType.STATUS:
                return self._check_status(assertion, response)
            elif assertion.type == AssertionType.BODY_CONTAINS:
                return self._check_body_contains(assertion, response)
            elif assertion.type == AssertionType.BODY_EQUALS:
                return self._check_body_equals(assertion, response)
            elif assertion.type == AssertionType.BODY_JSONPATH:
                return self._check_body_jsonpath(assertion, response)
            elif assertion.type == AssertionType.HEADER_EXISTS:
                return self._check_header_exists(assertion, response)
            elif assertion.type == AssertionType.HEADER_EQUALS:
                return self._check_header_equals(assertion, response)
            elif assertion.type == AssertionType.RESPONSE_TIME:
                return self._check_response_time(assertion, response)
            elif assertion.type == AssertionType.JSON_SCHEMA:
                return self._check_json_schema(assertion, response)
            else:
                return AssertionResult(
                    name=f"Unknown assertion type: {assertion.type}",
                    passed=False,
                    message=f"Unsupported assertion type: {assertion.type}",
                )
        except Exception as e:
            return AssertionResult(
                name=f"{assertion.type.value} assertion",
                passed=False,
                message=f"Assertion error: {str(e)}",
            )

    def _check_status(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check status code assertion."""
        actual = response.get("status")
        expected = assertion.expected
        
        passed = self._compare(actual, expected, assertion.operator)
        
        return AssertionResult(
            name=f"Status code {assertion.operator.value} {expected}",
            passed=passed,
            actual=actual,
            expected=expected,
            message=None if passed else f"Expected status {expected}, got {actual}",
        )

    def _check_body_contains(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check if body contains expected value."""
        body = response.get("body")
        expected = assertion.expected
        
        # Convert body to string for searching
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = str(body) if body else ""
        
        passed = str(expected) in body_str
        
        return AssertionResult(
            name=f"Body contains '{expected}'",
            passed=passed,
            actual=body_str[:200] + "..." if len(body_str) > 200 else body_str,
            expected=expected,
            message=None if passed else f"Body does not contain '{expected}'",
        )

    def _check_body_equals(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check if body equals expected value."""
        body = response.get("body")
        expected = assertion.expected
        
        passed = body == expected
        
        return AssertionResult(
            name="Body equals expected",
            passed=passed,
            actual=body,
            expected=expected,
            message=None if passed else "Body does not match expected value",
        )

    def _check_body_jsonpath(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check JSONPath expression against body."""
        body = response.get("body")
        target = assertion.target
        expected = assertion.expected
        operator = assertion.operator
        
        if not target:
            return AssertionResult(
                name="JSONPath assertion",
                passed=False,
                message="No JSONPath target specified",
            )
        
        if not isinstance(body, dict):
            return AssertionResult(
                name=f"JSONPath {target}",
                passed=False,
                message="Body is not a JSON object",
            )
        
        try:
            jsonpath_expr = jsonpath_parse(target)
            matches = jsonpath_expr.find(body)
        except JsonPathParserError as e:
            return AssertionResult(
                name=f"JSONPath {target}",
                passed=False,
                message=f"Invalid JSONPath expression: {e}",
            )
        
        if operator == AssertionOperator.EXISTS:
            passed = len(matches) > 0
            return AssertionResult(
                name=f"JSONPath {target} exists",
                passed=passed,
                actual=f"{len(matches)} matches found",
                message=None if passed else f"No matches found for {target}",
            )
        
        if operator == AssertionOperator.NOT_EXISTS:
            passed = len(matches) == 0
            return AssertionResult(
                name=f"JSONPath {target} not exists",
                passed=passed,
                actual=f"{len(matches)} matches found",
                message=None if passed else f"Unexpected matches found for {target}",
            )
        
        if len(matches) == 0:
            return AssertionResult(
                name=f"JSONPath {target}",
                passed=False,
                message=f"No matches found for JSONPath: {target}",
            )
        
        actual = matches[0].value
        passed = self._compare(actual, expected, operator)
        
        return AssertionResult(
            name=f"JSONPath {target} {operator.value} {expected}",
            passed=passed,
            actual=actual,
            expected=expected,
            message=None if passed else f"Expected {expected}, got {actual}",
        )

    def _check_header_exists(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check if header exists."""
        headers = response.get("headers", {})
        target = assertion.target
        
        if not target:
            return AssertionResult(
                name="Header exists",
                passed=False,
                message="No header name specified",
            )
        
        # Headers are case-insensitive
        header_lower = {k.lower(): v for k, v in headers.items()}
        passed = target.lower() in header_lower
        
        return AssertionResult(
            name=f"Header '{target}' exists",
            passed=passed,
            actual=list(headers.keys()),
            message=None if passed else f"Header '{target}' not found",
        )

    def _check_header_equals(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check if header equals expected value."""
        headers = response.get("headers", {})
        target = assertion.target
        expected = assertion.expected
        
        if not target:
            return AssertionResult(
                name="Header equals",
                passed=False,
                message="No header name specified",
            )
        
        # Headers are case-insensitive
        header_lower = {k.lower(): v for k, v in headers.items()}
        actual = header_lower.get(target.lower())
        
        if actual is None:
            return AssertionResult(
                name=f"Header '{target}' equals '{expected}'",
                passed=False,
                actual=None,
                expected=expected,
                message=f"Header '{target}' not found",
            )
        
        passed = self._compare(actual, expected, assertion.operator)
        
        return AssertionResult(
            name=f"Header '{target}' {assertion.operator.value} '{expected}'",
            passed=passed,
            actual=actual,
            expected=expected,
            message=None if passed else f"Expected '{expected}', got '{actual}'",
        )

    def _check_response_time(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Check response time assertion."""
        duration = response.get("duration", 0)
        expected = assertion.expected
        operator = assertion.operator
        
        if expected is None:
            return AssertionResult(
                name="Response time",
                passed=False,
                message="No expected time specified",
            )
        
        try:
            expected_ms = int(expected)
        except (ValueError, TypeError):
            return AssertionResult(
                name="Response time",
                passed=False,
                message=f"Invalid expected time: {expected}",
            )
        
        passed = self._compare(duration, expected_ms, operator)
        
        return AssertionResult(
            name=f"Response time {operator.value} {expected_ms}ms",
            passed=passed,
            actual=f"{duration}ms",
            expected=f"{expected_ms}ms",
            message=None if passed else f"Response time {duration}ms did not meet expectation",
        )

    def _check_json_schema(
        self,
        assertion: AssertionConfig,
        response: dict[str, Any],
    ) -> AssertionResult:
        """Validate body against JSON schema."""
        body = response.get("body")
        schema = assertion.expected
        
        if not isinstance(body, dict):
            return AssertionResult(
                name="JSON Schema validation",
                passed=False,
                message="Body is not a JSON object",
            )
        
        if not isinstance(schema, dict):
            return AssertionResult(
                name="JSON Schema validation",
                passed=False,
                message="Schema must be a JSON object",
            )
        
        try:
            jsonschema.validate(instance=body, schema=schema)
            return AssertionResult(
                name="JSON Schema validation",
                passed=True,
            )
        except jsonschema.ValidationError as e:
            return AssertionResult(
                name="JSON Schema validation",
                passed=False,
                message=f"Schema validation failed: {e.message}",
            )
        except jsonschema.SchemaError as e:
            return AssertionResult(
                name="JSON Schema validation",
                passed=False,
                message=f"Invalid schema: {e.message}",
            )

    def _compare(
        self,
        actual: Any,
        expected: Any,
        operator: AssertionOperator,
    ) -> bool:
        """Compare actual and expected values using the specified operator."""
        if operator == AssertionOperator.EQUALS:
            return actual == expected
        elif operator == AssertionOperator.NOT_EQUALS:
            return actual != expected
        elif operator == AssertionOperator.CONTAINS:
            return str(expected) in str(actual)
        elif operator == AssertionOperator.NOT_CONTAINS:
            return str(expected) not in str(actual)
        elif operator == AssertionOperator.MATCHES:
            try:
                return bool(re.match(str(expected), str(actual)))
            except re.error:
                return False
        elif operator == AssertionOperator.EXISTS:
            return actual is not None
        elif operator == AssertionOperator.NOT_EXISTS:
            return actual is None
        elif operator == AssertionOperator.LT:
            try:
                return float(actual) < float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == AssertionOperator.GT:
            try:
                return float(actual) > float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == AssertionOperator.LTE:
            try:
                return float(actual) <= float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == AssertionOperator.GTE:
            try:
                return float(actual) >= float(expected)
            except (ValueError, TypeError):
                return False
        else:
            return False
