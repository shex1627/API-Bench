"""
Variable Store Service.

Manages variables across different scopes (global, collection, environment).
Handles variable substitution in requests.
"""

import re
from pathlib import Path
from typing import Any

from ..types import Environment, EnvironmentVariable, VariableScope
from .dynamic_variables import DynamicVariables
from .env_persistence import EnvironmentPersistence


class VariableStore:
    """
    Manages variables across different scopes.
    
    Scopes (in order of precedence, highest to lowest):
    1. Environment variables
    2. Collection variables
    3. Global variables
    """

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self._global_vars: dict[str, EnvironmentVariable] = {}
        self._collection_vars: dict[str, dict[str, EnvironmentVariable]] = {}
        self._environments: dict[str, Environment] = {}
        self._active_environment: str | None = None
        self._persistence: EnvironmentPersistence | None = None

        # Initialize persistence if storage directory provided
        if storage_dir:
            self._persistence = EnvironmentPersistence(storage_dir)
            self._load_from_disk()

    # =========================================================================
    # Persistence
    # =========================================================================

    def _load_from_disk(self) -> None:
        """Load all environments from disk."""
        if not self._persistence:
            return

        # Load all environments
        self._environments = self._persistence.load_all_environments()

        # Load active environment
        self._active_environment = self._persistence.load_active_environment()

    def _save_to_disk(self, env_name: str | None = None) -> None:
        """Save environment(s) to disk."""
        if not self._persistence:
            return

        if env_name:
            # Save specific environment
            env = self._environments.get(env_name)
            if env:
                self._persistence.save_environment(env)
        else:
            # Save all environments
            for env in self._environments.values():
                self._persistence.save_environment(env)

        # Save active environment
        self._persistence.save_active_environment(self._active_environment)

    # =========================================================================
    # Environment Management
    # =========================================================================

    def create_environment(
        self,
        name: str,
        variables: dict[str, str | EnvironmentVariable] | None = None,
        description: str | None = None,
    ) -> Environment:
        """Create a new environment."""
        env_vars: dict[str, EnvironmentVariable] = {}

        if variables:
            for key, value in variables.items():
                if isinstance(value, str):
                    env_vars[key] = EnvironmentVariable(value=value)
                else:
                    env_vars[key] = value

        env = Environment(name=name, variables=env_vars, description=description)
        self._environments[name] = env
        self._save_to_disk(name)  # Auto-save
        return env

    def get_environment(self, name: str) -> Environment | None:
        """Get an environment by name."""
        return self._environments.get(name)

    def list_environments(self) -> list[str]:
        """List all environment names."""
        return list(self._environments.keys())

    def switch_environment(self, name: str | None) -> str | None:
        """Switch the active environment."""
        previous = self._active_environment
        if name is None or name in self._environments:
            self._active_environment = name
            self._save_to_disk()  # Auto-save active environment
        else:
            raise ValueError(f"Environment '{name}' not found")
        return previous

    def get_active_environment(self) -> str | None:
        """Get the name of the active environment."""
        return self._active_environment

    def delete_environment(self, name: str) -> bool:
        """Delete an environment."""
        if name in self._environments:
            del self._environments[name]
            if self._active_environment == name:
                self._active_environment = None
            if self._persistence:
                self._persistence.delete_environment(name)
            self._save_to_disk()  # Save active environment state
            return True
        return False

    # =========================================================================
    # Variable Management
    # =========================================================================

    def set_variable(
        self,
        name: str,
        value: str,
        scope: VariableScope = VariableScope.ENVIRONMENT,
        collection: str | None = None,
        environment: str | None = None,
        secret: bool = False,
    ) -> None:
        """Set a variable in the specified scope."""
        var = EnvironmentVariable(value=value, secret=secret)

        if scope == VariableScope.GLOBAL:
            self._global_vars[name] = var

        elif scope == VariableScope.COLLECTION:
            if collection is None:
                raise ValueError("Collection name required for collection scope")
            if collection not in self._collection_vars:
                self._collection_vars[collection] = {}
            self._collection_vars[collection][name] = var

        elif scope == VariableScope.ENVIRONMENT:
            env_name = environment or self._active_environment
            if env_name is None:
                raise ValueError("No active environment and no environment specified")
            if env_name not in self._environments:
                raise ValueError(f"Environment '{env_name}' not found")
            self._environments[env_name].variables[name] = var
            self._save_to_disk(env_name)  # Auto-save when environment var changes

    def get_variable(
        self,
        name: str,
        collection: str | None = None,
        environment: str | None = None,
    ) -> str | None:
        """
        Get a variable value, checking scopes in order of precedence.
        
        Order: environment > collection > global
        """
        # Check environment scope first
        env_name = environment or self._active_environment
        if env_name and env_name in self._environments:
            env = self._environments[env_name]
            if name in env.variables:
                return env.variables[name].value

        # Check collection scope
        if collection and collection in self._collection_vars:
            if name in self._collection_vars[collection]:
                return self._collection_vars[collection][name].value

        # Check global scope
        if name in self._global_vars:
            return self._global_vars[name].value

        return None

    def get_all_variables(
        self,
        collection: str | None = None,
        environment: str | None = None,
        mask_secrets: bool = True,
    ) -> dict[str, str]:
        """
        Get all variables merged by precedence.
        
        Returns a flat dict with environment > collection > global precedence.
        """
        result: dict[str, str] = {}

        # Start with global (lowest precedence)
        for name, var in self._global_vars.items():
            result[name] = "***" if var.secret and mask_secrets else var.value

        # Add collection (overrides global)
        if collection and collection in self._collection_vars:
            for name, var in self._collection_vars[collection].items():
                result[name] = "***" if var.secret and mask_secrets else var.value

        # Add environment (highest precedence)
        env_name = environment or self._active_environment
        if env_name and env_name in self._environments:
            for name, var in self._environments[env_name].variables.items():
                result[name] = "***" if var.secret and mask_secrets else var.value

        return result

    def delete_variable(
        self,
        name: str,
        scope: VariableScope = VariableScope.ENVIRONMENT,
        collection: str | None = None,
        environment: str | None = None,
    ) -> bool:
        """Delete a variable from the specified scope."""
        if scope == VariableScope.GLOBAL:
            if name in self._global_vars:
                del self._global_vars[name]
                return True

        elif scope == VariableScope.COLLECTION:
            if collection and collection in self._collection_vars:
                if name in self._collection_vars[collection]:
                    del self._collection_vars[collection][name]
                    return True

        elif scope == VariableScope.ENVIRONMENT:
            env_name = environment or self._active_environment
            if env_name and env_name in self._environments:
                if name in self._environments[env_name].variables:
                    del self._environments[env_name].variables[name]
                    self._save_to_disk(env_name)  # Auto-save
                    return True

        return False

    # =========================================================================
    # Variable Substitution
    # =========================================================================

    def substitute(
        self,
        text: str,
        collection: str | None = None,
        environment: str | None = None,
        overrides: dict[str, str] | None = None,
    ) -> str:
        """
        Substitute {{variable}} placeholders in text.

        Variables are resolved in order of precedence:
        1. Overrides (passed at runtime)
        2. Dynamic variables (starting with $, e.g., {{$timestamp}})
        3. Environment variables
        4. Collection variables
        5. Global variables
        """
        pattern = r"\{\{([^}]+)\}\}"

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1).strip()

            # Check overrides first
            if overrides and var_name in overrides:
                return overrides[var_name]

            # Check for dynamic variables (starting with $)
            if var_name.startswith("$"):
                dynamic_value = DynamicVariables.get_value(var_name)
                if dynamic_value is not None:
                    return dynamic_value

            value = self.get_variable(var_name, collection, environment)
            if value is not None:
                return value
            # Return original if not found (allows for chained substitution)
            return match.group(0)

        return re.sub(pattern, replace_var, text)

    def substitute_dict(
        self,
        data: dict[str, Any],
        collection: str | None = None,
        environment: str | None = None,
        overrides: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Recursively substitute variables in a dictionary."""
        result: dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.substitute(value, collection, environment, overrides)
            elif isinstance(value, dict):
                result[key] = self.substitute_dict(value, collection, environment, overrides)
            elif isinstance(value, list):
                result[key] = self.substitute_list(value, collection, environment, overrides)
            else:
                result[key] = value

        return result

    def substitute_list(
        self,
        data: list[Any],
        collection: str | None = None,
        environment: str | None = None,
        overrides: dict[str, str] | None = None,
    ) -> list[Any]:
        """Recursively substitute variables in a list."""
        result: list[Any] = []

        for item in data:
            if isinstance(item, str):
                result.append(self.substitute(item, collection, environment, overrides))
            elif isinstance(item, dict):
                result.append(self.substitute_dict(item, collection, environment, overrides))
            elif isinstance(item, list):
                result.append(self.substitute_list(item, collection, environment, overrides))
            else:
                result.append(item)

        return result

    # =========================================================================
    # Dynamic Variables
    # =========================================================================

    @staticmethod
    def list_dynamic_variables() -> list[str]:
        """List all available dynamic variables (e.g., $timestamp, $guid)."""
        return DynamicVariables.list_variables()

    @staticmethod
    def get_dynamic_variable_value(name: str) -> str | None:
        """Get a generated value for a dynamic variable."""
        return DynamicVariables.get_value(name)

    # =========================================================================
    # Serialization
    # =========================================================================

    def export_environment(self, name: str) -> dict[str, Any] | None:
        """Export an environment as a dictionary."""
        env = self._environments.get(name)
        if env:
            return env.model_dump()
        return None

    def import_environment(self, data: dict[str, Any]) -> Environment:
        """Import an environment from a dictionary."""
        env = Environment.model_validate(data)
        self._environments[env.name] = env
        return env
