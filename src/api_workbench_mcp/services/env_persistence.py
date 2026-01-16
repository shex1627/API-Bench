"""
Environment Persistence Service.

Handles saving and loading environments to/from disk with encryption for secrets.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..types import Environment


class EnvironmentPersistence:
    """
    Manages environment persistence with encryption for secrets.

    Environments are stored as JSON files in a dedicated directory.
    Secret values are encrypted using a machine-specific key.
    """

    def __init__(self, storage_dir: str | Path = "environments") -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """
        Get or create encryption cipher using machine-specific key.

        Uses machine ID + username to generate a consistent key for this machine.
        """
        key_file = self._storage_dir / ".key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            # Generate key from machine-specific data
            # This ensures the same key is used across server restarts
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"api-workbench-salt",  # Static salt is OK here
                iterations=100000,
            )
            key_material = kdf.derive(machine_id.encode())
            key = base64.urlsafe_b64encode(key_material)

            # Save key for reuse
            with open(key_file, "wb") as f:
                f.write(key)

            # Restrict permissions (owner read/write only)
            key_file.chmod(0o600)

        return Fernet(key)

    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier."""
        # Use a combination of username and hostname
        import socket
        username = os.getenv("USER", os.getenv("USERNAME", "default"))
        hostname = socket.gethostname()
        return f"{username}@{hostname}"

    def _encrypt_value(self, value: str) -> str:
        """Encrypt a secret value."""
        encrypted = self._cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        encrypted = base64.b64decode(encrypted_value.encode())
        return self._cipher.decrypt(encrypted).decode()

    def save_environment(self, env: Environment) -> None:
        """Save an environment to disk."""
        # Convert to dict
        env_data = env.model_dump()

        # Encrypt secret values
        for var_name, var in env_data.get("variables", {}).items():
            if isinstance(var, dict) and var.get("secret"):
                var["value"] = self._encrypt_value(var["value"])

        # Save to file
        file_path = self._storage_dir / f"{env.name}.json"
        with open(file_path, "w") as f:
            json.dump(env_data, f, indent=2, default=str)

        # Restrict permissions
        file_path.chmod(0o600)

    def load_environment(self, name: str) -> Environment | None:
        """Load an environment from disk."""
        file_path = self._storage_dir / f"{name}.json"

        if not file_path.exists():
            return None

        with open(file_path) as f:
            env_data = json.load(f)

        # Decrypt secret values
        for var_name, var in env_data.get("variables", {}).items():
            if isinstance(var, dict) and var.get("secret"):
                try:
                    var["value"] = self._decrypt_value(var["value"])
                except Exception:
                    # If decryption fails, leave as is (might be corrupted)
                    pass

        return Environment.model_validate(env_data)

    def load_all_environments(self) -> dict[str, Environment]:
        """Load all environments from disk."""
        environments: dict[str, Environment] = {}

        for file_path in self._storage_dir.glob("*.json"):
            # Skip system files
            if file_path.stem in (".key", ".state"):
                continue

            env = self.load_environment(file_path.stem)
            if env:
                environments[env.name] = env

        return environments

    def delete_environment(self, name: str) -> bool:
        """Delete an environment from disk."""
        file_path = self._storage_dir / f"{name}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def list_environment_names(self) -> list[str]:
        """List all saved environment names."""
        return [
            f.stem
            for f in self._storage_dir.glob("*.json")
            if f.stem != ".key"
        ]

    def save_active_environment(self, name: str | None) -> None:
        """Save the active environment name."""
        state_file = self._storage_dir / ".state.json"
        with open(state_file, "w") as f:
            json.dump({"active_environment": name}, f)

    def load_active_environment(self) -> str | None:
        """Load the active environment name."""
        state_file = self._storage_dir / ".state.json"

        if not state_file.exists():
            return None

        with open(state_file) as f:
            state = json.load(f)

        return state.get("active_environment")
