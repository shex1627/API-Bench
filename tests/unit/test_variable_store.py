"""
Tests for the Variable Store service.
"""

import pytest

from api_workbench_mcp.services.variable_store import VariableStore
from api_workbench_mcp.types import VariableScope


class TestVariableStore:
    """Tests for VariableStore."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = VariableStore()

    # =========================================================================
    # Environment Management Tests
    # =========================================================================

    def test_create_environment(self):
        """Test creating an environment."""
        env = self.store.create_environment(
            name="test",
            variables={"baseUrl": "http://localhost:3000"},
            description="Test environment",
        )
        
        assert env.name == "test"
        assert env.description == "Test environment"
        assert len(env.variables) == 1
        assert env.variables["baseUrl"].value == "http://localhost:3000"

    def test_create_environment_with_mixed_variables(self):
        """Test creating environment with both string and EnvironmentVariable values."""
        from api_workbench_mcp.types import EnvironmentVariable
        
        env = self.store.create_environment(
            name="mixed",
            variables={
                "url": "http://example.com",
                "secret": EnvironmentVariable(value="password123", secret=True),
            },
        )
        
        assert env.variables["url"].value == "http://example.com"
        assert env.variables["url"].secret is False
        assert env.variables["secret"].value == "password123"
        assert env.variables["secret"].secret is True

    def test_list_environments(self):
        """Test listing environments."""
        self.store.create_environment("dev")
        self.store.create_environment("staging")
        self.store.create_environment("prod")
        
        envs = self.store.list_environments()
        
        assert len(envs) == 3
        assert "dev" in envs
        assert "staging" in envs
        assert "prod" in envs

    def test_switch_environment(self):
        """Test switching active environment."""
        self.store.create_environment("dev")
        self.store.create_environment("prod")
        
        assert self.store.get_active_environment() is None
        
        self.store.switch_environment("dev")
        assert self.store.get_active_environment() == "dev"
        
        previous = self.store.switch_environment("prod")
        assert previous == "dev"
        assert self.store.get_active_environment() == "prod"

    def test_switch_to_nonexistent_environment_raises(self):
        """Test that switching to nonexistent environment raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.store.switch_environment("nonexistent")
        
        assert "not found" in str(exc_info.value)

    def test_delete_environment(self):
        """Test deleting an environment."""
        self.store.create_environment("temp")
        self.store.switch_environment("temp")
        
        assert self.store.delete_environment("temp") is True
        assert "temp" not in self.store.list_environments()
        assert self.store.get_active_environment() is None

    def test_delete_nonexistent_environment(self):
        """Test deleting nonexistent environment returns False."""
        assert self.store.delete_environment("nonexistent") is False

    # =========================================================================
    # Variable Management Tests
    # =========================================================================

    def test_set_and_get_global_variable(self):
        """Test setting and getting global variables."""
        self.store.set_variable(
            name="globalVar",
            value="globalValue",
            scope=VariableScope.GLOBAL,
        )
        
        value = self.store.get_variable("globalVar")
        assert value == "globalValue"

    def test_set_and_get_environment_variable(self):
        """Test setting and getting environment variables."""
        self.store.create_environment("test")
        self.store.switch_environment("test")
        
        self.store.set_variable(
            name="envVar",
            value="envValue",
            scope=VariableScope.ENVIRONMENT,
        )
        
        value = self.store.get_variable("envVar")
        assert value == "envValue"

    def test_variable_precedence(self):
        """Test that environment variables override global variables."""
        self.store.set_variable("shared", "global", scope=VariableScope.GLOBAL)
        
        self.store.create_environment("test")
        self.store.switch_environment("test")
        self.store.set_variable("shared", "environment", scope=VariableScope.ENVIRONMENT)
        
        # Environment should win
        value = self.store.get_variable("shared")
        assert value == "environment"

    def test_get_nonexistent_variable(self):
        """Test getting a nonexistent variable returns None."""
        value = self.store.get_variable("nonexistent")
        assert value is None

    def test_get_all_variables_with_masking(self):
        """Test getting all variables with secret masking."""
        from api_workbench_mcp.types import EnvironmentVariable
        
        self.store.create_environment(
            name="test",
            variables={
                "url": "http://example.com",
                "apiKey": EnvironmentVariable(value="secret123", secret=True),
            },
        )
        self.store.switch_environment("test")
        
        # With masking (default)
        all_vars = self.store.get_all_variables(mask_secrets=True)
        assert all_vars["url"] == "http://example.com"
        assert all_vars["apiKey"] == "***"
        
        # Without masking
        all_vars = self.store.get_all_variables(mask_secrets=False)
        assert all_vars["apiKey"] == "secret123"

    def test_delete_variable(self):
        """Test deleting a variable."""
        self.store.set_variable("toDelete", "value", scope=VariableScope.GLOBAL)
        assert self.store.get_variable("toDelete") == "value"
        
        result = self.store.delete_variable("toDelete", scope=VariableScope.GLOBAL)
        assert result is True
        assert self.store.get_variable("toDelete") is None

    # =========================================================================
    # Variable Substitution Tests
    # =========================================================================

    def test_simple_substitution(self):
        """Test simple variable substitution."""
        self.store.create_environment(
            name="test",
            variables={"baseUrl": "http://api.example.com"},
        )
        self.store.switch_environment("test")
        
        result = self.store.substitute("{{baseUrl}}/users")
        assert result == "http://api.example.com/users"

    def test_multiple_substitution(self):
        """Test multiple variable substitutions in one string."""
        self.store.create_environment(
            name="test",
            variables={
                "host": "api.example.com",
                "version": "v2",
            },
        )
        self.store.switch_environment("test")
        
        result = self.store.substitute("https://{{host}}/{{version}}/users")
        assert result == "https://api.example.com/v2/users"

    def test_unresolved_variable_kept(self):
        """Test that unresolved variables are kept as-is."""
        result = self.store.substitute("{{unknown}}/path")
        assert result == "{{unknown}}/path"

    def test_substitute_dict(self):
        """Test substituting variables in a dictionary."""
        self.store.create_environment(
            name="test",
            variables={"name": "John", "email": "john@example.com"},
        )
        self.store.switch_environment("test")
        
        data = {
            "user": {
                "name": "{{name}}",
                "contact": {
                    "email": "{{email}}",
                },
            },
        }
        
        result = self.store.substitute_dict(data)
        
        assert result["user"]["name"] == "John"
        assert result["user"]["contact"]["email"] == "john@example.com"

    def test_substitute_list(self):
        """Test substituting variables in a list."""
        self.store.create_environment(
            name="test",
            variables={"item1": "first", "item2": "second"},
        )
        self.store.switch_environment("test")
        
        data = ["{{item1}}", "static", "{{item2}}"]
        result = self.store.substitute_list(data)
        
        assert result == ["first", "static", "second"]

    def test_whitespace_in_variable_name(self):
        """Test that whitespace in variable names is handled."""
        self.store.create_environment(
            name="test",
            variables={"myVar": "value"},
        )
        self.store.switch_environment("test")
        
        # Variable name with surrounding whitespace
        result = self.store.substitute("{{ myVar }}")
        assert result == "value"


class TestVariableStoreExport:
    """Tests for VariableStore import/export."""

    def test_export_environment(self):
        """Test exporting an environment."""
        store = VariableStore()
        store.create_environment(
            name="export-test",
            variables={"key": "value"},
            description="Test export",
        )
        
        exported = store.export_environment("export-test")
        
        assert exported is not None
        assert exported["name"] == "export-test"
        assert exported["description"] == "Test export"
        assert "variables" in exported

    def test_export_nonexistent_environment(self):
        """Test exporting nonexistent environment returns None."""
        store = VariableStore()
        assert store.export_environment("nonexistent") is None

    def test_import_environment(self):
        """Test importing an environment."""
        store = VariableStore()
        
        data = {
            "name": "imported",
            "description": "Imported env",
            "variables": {
                "url": {"value": "http://example.com", "secret": False},
            },
        }
        
        env = store.import_environment(data)
        
        assert env.name == "imported"
        assert store.get_environment("imported") is not None
