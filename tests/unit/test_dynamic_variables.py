"""
Tests for the Dynamic Variables service.
"""

import re
import uuid

import pytest

from api_workbench_mcp.services.dynamic_variables import DynamicVariables
from api_workbench_mcp.services.variable_store import VariableStore


class TestDynamicVariables:
    """Tests for DynamicVariables class."""

    # =========================================================================
    # Core Variables Tests
    # =========================================================================

    def test_guid_format(self):
        """Test $guid returns valid UUID v4 format."""
        value = DynamicVariables.get_value("$guid")
        assert value is not None
        # Should be valid UUID
        parsed = uuid.UUID(value)
        assert parsed.version == 4

    def test_random_uuid_format(self):
        """Test $randomUUID returns valid UUID v4 format."""
        value = DynamicVariables.get_value("$randomUUID")
        assert value is not None
        parsed = uuid.UUID(value)
        assert parsed.version == 4

    def test_timestamp_is_numeric(self):
        """Test $timestamp returns numeric string."""
        value = DynamicVariables.get_value("$timestamp")
        assert value is not None
        assert value.isdigit()
        # Should be a reasonable Unix timestamp (after 2020)
        assert int(value) > 1577836800

    def test_iso_timestamp_format(self):
        """Test $isoTimestamp returns ISO 8601 format."""
        value = DynamicVariables.get_value("$isoTimestamp")
        assert value is not None
        # Should match ISO 8601 format with Z suffix
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"
        assert re.match(pattern, value)

    def test_random_int_range(self):
        """Test $randomInt is between 0 and 1000."""
        for _ in range(100):  # Test multiple times
            value = DynamicVariables.get_value("$randomInt")
            assert value is not None
            num = int(value)
            assert 0 <= num <= 1000

    def test_random_boolean(self):
        """Test $randomBoolean returns true or false."""
        value = DynamicVariables.get_value("$randomBoolean")
        assert value in ["true", "false"]

    # =========================================================================
    # Text & Numbers Tests
    # =========================================================================

    def test_random_alphanumeric(self):
        """Test $randomAlphaNumeric returns single alphanumeric char."""
        value = DynamicVariables.get_value("$randomAlphaNumeric")
        assert value is not None
        assert len(value) == 1
        assert value.isalnum()

    def test_random_hex_color(self):
        """Test $randomHexColor returns valid hex color."""
        value = DynamicVariables.get_value("$randomHexColor")
        assert value is not None
        assert re.match(r"^#[0-9a-f]{6}$", value)

    def test_random_color(self):
        """Test $randomColor returns a color name."""
        value = DynamicVariables.get_value("$randomColor")
        assert value is not None
        assert value in DynamicVariables.COLORS

    # =========================================================================
    # Names Tests
    # =========================================================================

    def test_random_first_name(self):
        """Test $randomFirstName returns a name."""
        value = DynamicVariables.get_value("$randomFirstName")
        assert value is not None
        assert value in DynamicVariables.FIRST_NAMES

    def test_random_last_name(self):
        """Test $randomLastName returns a name."""
        value = DynamicVariables.get_value("$randomLastName")
        assert value is not None
        assert value in DynamicVariables.LAST_NAMES

    def test_random_full_name(self):
        """Test $randomFullName returns first and last name."""
        value = DynamicVariables.get_value("$randomFullName")
        assert value is not None
        parts = value.split(" ")
        assert len(parts) == 2
        assert parts[0] in DynamicVariables.FIRST_NAMES
        assert parts[1] in DynamicVariables.LAST_NAMES

    # =========================================================================
    # Internet & Contact Tests
    # =========================================================================

    def test_random_email(self):
        """Test $randomEmail returns valid email format."""
        value = DynamicVariables.get_value("$randomEmail")
        assert value is not None
        assert "@" in value
        assert "." in value.split("@")[1]

    def test_random_username(self):
        """Test $randomUserName returns username."""
        value = DynamicVariables.get_value("$randomUserName")
        assert value is not None
        assert len(value) > 0

    def test_random_password(self):
        """Test $randomPassword returns 15-char password."""
        value = DynamicVariables.get_value("$randomPassword")
        assert value is not None
        assert len(value) == 15
        assert value.isalnum()

    def test_random_url(self):
        """Test $randomUrl returns valid URL format."""
        value = DynamicVariables.get_value("$randomUrl")
        assert value is not None
        assert value.startswith("https://")

    def test_random_ip(self):
        """Test $randomIP returns valid IPv4 format."""
        value = DynamicVariables.get_value("$randomIP")
        assert value is not None
        parts = value.split(".")
        assert len(parts) == 4
        for part in parts:
            num = int(part)
            assert 1 <= num <= 255

    def test_random_ipv6(self):
        """Test $randomIPV6 returns valid IPv6 format."""
        value = DynamicVariables.get_value("$randomIPV6")
        assert value is not None
        parts = value.split(":")
        assert len(parts) == 8

    def test_random_phone_number(self):
        """Test $randomPhoneNumber returns phone format."""
        value = DynamicVariables.get_value("$randomPhoneNumber")
        assert value is not None
        # Should match XXX-XXX-XXXX format
        assert re.match(r"\d{3}-\d{3}-\d{4}", value)

    def test_random_mac_address(self):
        """Test $randomMACAddress returns valid MAC format."""
        value = DynamicVariables.get_value("$randomMACAddress")
        assert value is not None
        parts = value.split(":")
        assert len(parts) == 6

    # =========================================================================
    # Location Tests
    # =========================================================================

    def test_random_city(self):
        """Test $randomCity returns a city name."""
        value = DynamicVariables.get_value("$randomCity")
        assert value is not None
        assert value in DynamicVariables.CITIES

    def test_random_country(self):
        """Test $randomCountry returns a country name."""
        value = DynamicVariables.get_value("$randomCountry")
        assert value is not None
        country_names = [c[0] for c in DynamicVariables.COUNTRIES]
        assert value in country_names

    def test_random_country_code(self):
        """Test $randomCountryCode returns ISO code."""
        value = DynamicVariables.get_value("$randomCountryCode")
        assert value is not None
        assert len(value) == 2
        assert value.isupper()

    def test_random_street_address(self):
        """Test $randomStreetAddress returns address format."""
        value = DynamicVariables.get_value("$randomStreetAddress")
        assert value is not None
        # Should contain a number
        assert any(c.isdigit() for c in value)

    def test_random_latitude(self):
        """Test $randomLatitude returns valid latitude."""
        value = DynamicVariables.get_value("$randomLatitude")
        assert value is not None
        lat = float(value)
        assert -90 <= lat <= 90

    def test_random_longitude(self):
        """Test $randomLongitude returns valid longitude."""
        value = DynamicVariables.get_value("$randomLongitude")
        assert value is not None
        lon = float(value)
        assert -180 <= lon <= 180

    # =========================================================================
    # Business Tests
    # =========================================================================

    def test_random_company_name(self):
        """Test $randomCompanyName returns company name."""
        value = DynamicVariables.get_value("$randomCompanyName")
        assert value is not None
        assert len(value) > 0

    def test_random_job_title(self):
        """Test $randomJobTitle returns job title."""
        value = DynamicVariables.get_value("$randomJobTitle")
        assert value is not None
        assert value in DynamicVariables.JOB_TITLES

    def test_random_department(self):
        """Test $randomDepartment returns department name."""
        value = DynamicVariables.get_value("$randomDepartment")
        assert value is not None
        assert value in DynamicVariables.DEPARTMENTS

    # =========================================================================
    # Financial Tests
    # =========================================================================

    def test_random_price(self):
        """Test $randomPrice returns valid price."""
        value = DynamicVariables.get_value("$randomPrice")
        assert value is not None
        price = float(value)
        assert 0 <= price <= 1000

    def test_random_currency_code(self):
        """Test $randomCurrencyCode returns ISO currency code."""
        value = DynamicVariables.get_value("$randomCurrencyCode")
        assert value is not None
        codes = [c[0] for c in DynamicVariables.CURRENCIES]
        assert value in codes

    def test_random_bank_account(self):
        """Test $randomBankAccount returns 8-digit number."""
        value = DynamicVariables.get_value("$randomBankAccount")
        assert value is not None
        assert len(value) == 8
        assert value.isdigit()

    # =========================================================================
    # Date Tests
    # =========================================================================

    def test_random_date_past(self):
        """Test $randomDatePast returns ISO date."""
        value = DynamicVariables.get_value("$randomDatePast")
        assert value is not None
        assert "T" in value
        assert value.endswith("Z")

    def test_random_date_future(self):
        """Test $randomDateFuture returns ISO date."""
        value = DynamicVariables.get_value("$randomDateFuture")
        assert value is not None
        assert "T" in value
        assert value.endswith("Z")

    def test_random_weekday(self):
        """Test $randomWeekday returns day name."""
        value = DynamicVariables.get_value("$randomWeekday")
        assert value is not None
        assert value in DynamicVariables.WEEKDAYS

    def test_random_month(self):
        """Test $randomMonth returns month name."""
        value = DynamicVariables.get_value("$randomMonth")
        assert value is not None
        assert value in DynamicVariables.MONTHS

    # =========================================================================
    # File & Content Tests
    # =========================================================================

    def test_random_file_name(self):
        """Test $randomFileName returns filename with extension."""
        value = DynamicVariables.get_value("$randomFileName")
        assert value is not None
        assert "." in value

    def test_random_file_ext(self):
        """Test $randomFileExt returns extension."""
        value = DynamicVariables.get_value("$randomFileExt")
        assert value is not None
        assert value in DynamicVariables.FILE_EXTENSIONS

    def test_random_mime_type(self):
        """Test $randomMimeType returns MIME type."""
        value = DynamicVariables.get_value("$randomMimeType")
        assert value is not None
        assert "/" in value

    def test_random_lorem_sentence(self):
        """Test $randomLoremSentence returns sentence."""
        value = DynamicVariables.get_value("$randomLoremSentence")
        assert value is not None
        assert value.endswith(".")
        assert value[0].isupper()

    def test_random_lorem_paragraph(self):
        """Test $randomLoremParagraph returns multiple sentences."""
        value = DynamicVariables.get_value("$randomLoremParagraph")
        assert value is not None
        # Should have multiple sentences
        assert value.count(".") >= 3

    # =========================================================================
    # Utility Tests
    # =========================================================================

    def test_is_dynamic_variable_true(self):
        """Test is_dynamic_variable returns True for valid dynamic vars."""
        assert DynamicVariables.is_dynamic_variable("$guid") is True
        assert DynamicVariables.is_dynamic_variable("$timestamp") is True
        assert DynamicVariables.is_dynamic_variable("$randomInt") is True

    def test_is_dynamic_variable_false(self):
        """Test is_dynamic_variable returns False for regular vars."""
        assert DynamicVariables.is_dynamic_variable("baseUrl") is False
        assert DynamicVariables.is_dynamic_variable("$unknown") is False
        assert DynamicVariables.is_dynamic_variable("") is False

    def test_get_value_unknown_returns_none(self):
        """Test get_value returns None for unknown variable."""
        assert DynamicVariables.get_value("$unknownVar") is None
        assert DynamicVariables.get_value("regularVar") is None

    def test_list_variables(self):
        """Test list_variables returns all registered variables."""
        variables = DynamicVariables.list_variables()
        assert len(variables) > 0
        assert "$guid" in variables
        assert "$timestamp" in variables
        assert "$randomInt" in variables
        # Should be sorted
        assert variables == sorted(variables)

    def test_values_are_random(self):
        """Test that dynamic variables return different values."""
        values = set()
        for _ in range(10):
            values.add(DynamicVariables.get_value("$guid"))
        # Should have 10 unique values
        assert len(values) == 10


class TestVariableStoreIntegration:
    """Tests for dynamic variable integration with VariableStore."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = VariableStore()

    def test_substitute_dynamic_variable(self):
        """Test substituting dynamic variables in text."""
        result = self.store.substitute("id={{$guid}}")
        assert result != "id={{$guid}}"
        # Should be a valid UUID
        uuid_part = result.replace("id=", "")
        uuid.UUID(uuid_part)

    def test_substitute_timestamp(self):
        """Test substituting $timestamp."""
        result = self.store.substitute("time={{$timestamp}}")
        time_part = result.replace("time=", "")
        assert time_part.isdigit()

    def test_mixed_substitution(self):
        """Test mixing dynamic and regular variables."""
        self.store.create_environment(
            name="test",
            variables={"baseUrl": "http://api.example.com"},
        )
        self.store.switch_environment("test")

        result = self.store.substitute("{{baseUrl}}/items/{{$guid}}")
        assert result.startswith("http://api.example.com/items/")
        # Extract and validate UUID
        uuid_part = result.split("/items/")[1]
        uuid.UUID(uuid_part)

    def test_dynamic_in_dict(self):
        """Test dynamic variables in dictionary substitution."""
        data = {
            "id": "{{$guid}}",
            "timestamp": "{{$timestamp}}",
        }
        result = self.store.substitute_dict(data)

        # Verify UUID
        uuid.UUID(result["id"])
        # Verify timestamp
        assert result["timestamp"].isdigit()

    def test_dynamic_in_list(self):
        """Test dynamic variables in list substitution."""
        data = ["{{$randomFirstName}}", "{{$randomEmail}}"]
        result = self.store.substitute_list(data)

        assert result[0] in DynamicVariables.FIRST_NAMES
        assert "@" in result[1]

    def test_override_dynamic_variable(self):
        """Test that overrides take precedence over dynamic variables."""
        result = self.store.substitute(
            "id={{$guid}}",
            overrides={"$guid": "fixed-uuid"},
        )
        assert result == "id=fixed-uuid"

    def test_unknown_dynamic_variable_kept(self):
        """Test unknown dynamic variables are kept as-is."""
        result = self.store.substitute("{{$unknownDynamic}}")
        assert result == "{{$unknownDynamic}}"

    def test_list_dynamic_variables(self):
        """Test listing dynamic variables through VariableStore."""
        variables = self.store.list_dynamic_variables()
        assert "$guid" in variables
        assert "$timestamp" in variables

    def test_get_dynamic_variable_value(self):
        """Test getting dynamic variable value through VariableStore."""
        value = self.store.get_dynamic_variable_value("$guid")
        assert value is not None
        uuid.UUID(value)
