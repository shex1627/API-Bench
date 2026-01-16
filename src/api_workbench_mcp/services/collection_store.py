"""
Collection Store Service.

Manages API collections with file-based persistence.
Supports YAML format for human-readable, git-friendly storage.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..types import (
    AuthConfig,
    BodyType,
    Collection,
    CollectionFolder,
    CollectionRequest,
    HttpMethod,
)


class CollectionStore:
    """
    Manages API collections with file-based persistence.
    
    Collections are stored as YAML files for human readability
    and git-friendliness (similar to Bruno's approach).
    """

    def __init__(self, collections_dir: str | Path = "collections") -> None:
        self._collections_dir = Path(collections_dir)
        self._collections_dir.mkdir(parents=True, exist_ok=True)
        self._collections: dict[str, Collection] = {}
        self._load_all_collections()

    def _load_all_collections(self) -> None:
        """Load all collections from the collections directory."""
        for path in self._collections_dir.glob("*/collection.yaml"):
            try:
                collection = self._load_collection_from_dir(path.parent)
                if collection:
                    self._collections[collection.name] = collection
            except Exception as e:
                print(f"Warning: Failed to load collection from {path}: {e}")

    def _load_collection_from_dir(self, collection_dir: Path) -> Collection | None:
        """Load a collection from a directory."""
        collection_file = collection_dir / "collection.yaml"
        if not collection_file.exists():
            return None

        with open(collection_file) as f:
            data = yaml.safe_load(f)

        # Load requests
        requests: dict[str, CollectionRequest] = {}
        requests_dir = collection_dir / "requests"
        if requests_dir.exists():
            for req_file in requests_dir.glob("**/*.yaml"):
                try:
                    with open(req_file) as f:
                        req_data = yaml.safe_load(f)
                    request = self._parse_request(req_data)
                    requests[request.name] = request
                except Exception as e:
                    print(f"Warning: Failed to load request from {req_file}: {e}")

        return Collection(
            name=data.get("name", collection_dir.name),
            description=data.get("description"),
            base_url=data.get("base_url"),
            auth=AuthConfig.model_validate(data["auth"]) if data.get("auth") else None,
            variables=data.get("variables", {}),
            folders=self._parse_folders(data.get("folders", [])),
            requests=requests,
        )

    def _parse_request(self, data: dict[str, Any]) -> CollectionRequest:
        """Parse a request from YAML data."""
        return CollectionRequest(
            name=data["name"],
            method=HttpMethod(data.get("method", "GET").upper()),
            url=data["url"],
            headers=data.get("headers", {}),
            body=data.get("body", {}).get("content") if isinstance(data.get("body"), dict) else data.get("body"),
            body_type=BodyType(data.get("body", {}).get("type", "json")) if isinstance(data.get("body"), dict) else BodyType.JSON,
            auth=AuthConfig.model_validate(data["auth"]) if data.get("auth") else None,
            pre_request_script=data.get("prerequest"),
            post_response_script=data.get("postresponse"),
            assertions=data.get("assertions", []),
        )

    def _parse_folders(self, folders_data: list[dict[str, Any]]) -> list[CollectionFolder]:
        """Parse folders from YAML data."""
        folders: list[CollectionFolder] = []
        for folder_data in folders_data:
            folders.append(
                CollectionFolder(
                    name=folder_data["name"],
                    description=folder_data.get("description"),
                    requests=folder_data.get("requests", []),
                    folders=self._parse_folders(folder_data.get("folders", [])),
                )
            )
        return folders

    # =========================================================================
    # Collection CRUD
    # =========================================================================

    def create_collection(
        self,
        name: str,
        description: str | None = None,
        folders: list[str] | None = None,
        base_url: str | None = None,
        auth: AuthConfig | None = None,
    ) -> Collection:
        """Create a new collection."""
        collection = Collection(
            name=name,
            description=description,
            base_url=base_url,
            auth=auth,
            folders=[CollectionFolder(name=f) for f in (folders or [])],
        )
        
        self._collections[name] = collection
        self._save_collection(collection)
        return collection

    def get_collection(self, name: str) -> Collection | None:
        """Get a collection by name."""
        return self._collections.get(name)

    def list_collections(self) -> list[str]:
        """List all collection names."""
        return list(self._collections.keys())

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        if name not in self._collections:
            return False

        del self._collections[name]
        
        # Remove from filesystem
        collection_dir = self._collections_dir / self._sanitize_filename(name)
        if collection_dir.exists():
            import shutil
            shutil.rmtree(collection_dir)
        
        return True

    def update_collection(self, collection: Collection) -> None:
        """Update an existing collection."""
        collection.updated_at = datetime.now()
        self._collections[collection.name] = collection
        self._save_collection(collection)

    # =========================================================================
    # Request Management
    # =========================================================================

    def add_request(
        self,
        collection_name: str,
        request: CollectionRequest,
        folder: str | None = None,
    ) -> bool:
        """Add a request to a collection."""
        collection = self._collections.get(collection_name)
        if not collection:
            return False

        collection.requests[request.name] = request
        
        # Add to folder if specified
        if folder:
            self._add_request_to_folder(collection, request.name, folder)
        
        collection.updated_at = datetime.now()
        self._save_collection(collection)
        return True

    def get_request(self, collection_name: str, request_name: str) -> CollectionRequest | None:
        """Get a request from a collection."""
        collection = self._collections.get(collection_name)
        if not collection:
            return None
        return collection.requests.get(request_name)

    def delete_request(self, collection_name: str, request_name: str) -> bool:
        """Delete a request from a collection."""
        collection = self._collections.get(collection_name)
        if not collection or request_name not in collection.requests:
            return False

        del collection.requests[request_name]
        
        # Remove from folders
        self._remove_request_from_folders(collection.folders, request_name)
        
        collection.updated_at = datetime.now()
        self._save_collection(collection)
        return True

    def get_requests_in_folder(
        self,
        collection_name: str,
        folder_path: str | None = None,
    ) -> list[CollectionRequest]:
        """Get all requests in a collection or folder."""
        collection = self._collections.get(collection_name)
        if not collection:
            return []

        if folder_path is None:
            return list(collection.requests.values())

        # Find the folder
        folder = self._find_folder(collection.folders, folder_path)
        if not folder:
            return []

        # Get requests in folder
        return [
            collection.requests[name]
            for name in folder.requests
            if name in collection.requests
        ]

    def get_all_request_names(
        self,
        collection_name: str,
        folder_path: str | None = None,
    ) -> list[str]:
        """Get all request names in order (respecting folder structure)."""
        collection = self._collections.get(collection_name)
        if not collection:
            return []

        if folder_path is None:
            # Return all requests, folders first
            names: list[str] = []
            self._collect_request_names(collection.folders, names, collection.requests)
            # Add any requests not in folders
            for name in collection.requests:
                if name not in names:
                    names.append(name)
            return names

        folder = self._find_folder(collection.folders, folder_path)
        if not folder:
            return []

        return folder.requests

    def _collect_request_names(
        self,
        folders: list[CollectionFolder],
        names: list[str],
        requests: dict[str, CollectionRequest],
    ) -> None:
        """Recursively collect request names from folders."""
        for folder in folders:
            for name in folder.requests:
                if name in requests and name not in names:
                    names.append(name)
            self._collect_request_names(folder.folders, names, requests)

    # =========================================================================
    # Folder Management
    # =========================================================================

    def add_folder(
        self,
        collection_name: str,
        folder_name: str,
        parent_path: str | None = None,
    ) -> bool:
        """Add a folder to a collection."""
        collection = self._collections.get(collection_name)
        if not collection:
            return False

        new_folder = CollectionFolder(name=folder_name)

        if parent_path is None:
            collection.folders.append(new_folder)
        else:
            parent = self._find_folder(collection.folders, parent_path)
            if not parent:
                return False
            parent.folders.append(new_folder)

        collection.updated_at = datetime.now()
        self._save_collection(collection)
        return True

    def _find_folder(
        self,
        folders: list[CollectionFolder],
        path: str,
    ) -> CollectionFolder | None:
        """Find a folder by path (e.g., 'Users/Authentication')."""
        parts = path.split("/")
        current_folders = folders

        for part in parts:
            found = None
            for folder in current_folders:
                if folder.name == part:
                    found = folder
                    break
            if not found:
                return None
            current_folders = found.folders

        return found

    def _add_request_to_folder(
        self,
        collection: Collection,
        request_name: str,
        folder_path: str,
    ) -> bool:
        """Add a request to a folder."""
        folder = self._find_folder(collection.folders, folder_path)
        if not folder:
            return False
        if request_name not in folder.requests:
            folder.requests.append(request_name)
        return True

    def _remove_request_from_folders(
        self,
        folders: list[CollectionFolder],
        request_name: str,
    ) -> None:
        """Remove a request from all folders."""
        for folder in folders:
            if request_name in folder.requests:
                folder.requests.remove(request_name)
            self._remove_request_from_folders(folder.folders, request_name)

    # =========================================================================
    # Persistence
    # =========================================================================

    def _save_collection(self, collection: Collection) -> None:
        """Save a collection to disk."""
        collection_dir = self._collections_dir / self._sanitize_filename(collection.name)
        collection_dir.mkdir(parents=True, exist_ok=True)

        # Save collection metadata
        collection_data = {
            "name": collection.name,
            "description": collection.description,
            "base_url": collection.base_url,
            "auth": collection.auth.model_dump() if collection.auth else None,
            "variables": collection.variables,
            "folders": self._serialize_folders(collection.folders),
        }

        with open(collection_dir / "collection.yaml", "w") as f:
            yaml.dump(collection_data, f, default_flow_style=False, sort_keys=False)

        # Save requests
        requests_dir = collection_dir / "requests"
        requests_dir.mkdir(exist_ok=True)

        for request in collection.requests.values():
            request_data = {
                "name": request.name,
                "method": request.method.value,
                "url": request.url,
                "headers": request.headers if request.headers else None,
                "body": {
                    "type": request.body_type.value,
                    "content": request.body,
                } if request.body else None,
                "auth": request.auth.model_dump() if request.auth else None,
                "prerequest": request.pre_request_script,
                "postresponse": request.post_response_script,
                "assertions": request.assertions if request.assertions else None,
            }
            # Remove None values
            request_data = {k: v for k, v in request_data.items() if v is not None}

            filename = self._sanitize_filename(request.name) + ".yaml"
            with open(requests_dir / filename, "w") as f:
                yaml.dump(request_data, f, default_flow_style=False, sort_keys=False)

    def _serialize_folders(self, folders: list[CollectionFolder]) -> list[dict[str, Any]]:
        """Serialize folders to YAML-friendly format."""
        result: list[dict[str, Any]] = []
        for folder in folders:
            folder_data: dict[str, Any] = {"name": folder.name}
            if folder.description:
                folder_data["description"] = folder.description
            if folder.requests:
                folder_data["requests"] = folder.requests
            if folder.folders:
                folder_data["folders"] = self._serialize_folders(folder.folders)
            result.append(folder_data)
        return result

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a name for use as a filename."""
        # Replace problematic characters
        return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()

    # =========================================================================
    # Import/Export
    # =========================================================================

    def import_postman_collection(self, data: dict[str, Any]) -> Collection:
        """Import a Postman v2.1 collection."""
        info = data.get("info", {})
        name = info.get("name", "Imported Collection")
        description = info.get("description")

        collection = Collection(
            name=name,
            description=description,
        )

        # Import items (requests and folders)
        self._import_postman_items(data.get("item", []), collection, None)

        # Import variables
        for var in data.get("variable", []):
            collection.variables[var.get("key", "")] = var.get("value", "")

        self._collections[name] = collection
        self._save_collection(collection)
        return collection

    def _import_postman_items(
        self,
        items: list[dict[str, Any]],
        collection: Collection,
        folder_path: str | None,
    ) -> None:
        """Recursively import Postman items."""
        for item in items:
            if "item" in item:
                # This is a folder
                folder_name = item.get("name", "Folder")
                new_folder = CollectionFolder(
                    name=folder_name,
                    description=item.get("description"),
                )
                
                if folder_path is None:
                    collection.folders.append(new_folder)
                else:
                    parent = self._find_folder(collection.folders, folder_path)
                    if parent:
                        parent.folders.append(new_folder)

                new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                self._import_postman_items(item["item"], collection, new_path)
            else:
                # This is a request
                request = self._import_postman_request(item)
                collection.requests[request.name] = request
                
                if folder_path:
                    folder = self._find_folder(collection.folders, folder_path)
                    if folder:
                        folder.requests.append(request.name)

    def _import_postman_request(self, item: dict[str, Any]) -> CollectionRequest:
        """Import a single Postman request."""
        request_data = item.get("request", {})
        
        # Handle URL
        url = request_data.get("url", "")
        if isinstance(url, dict):
            url = url.get("raw", "")

        # Handle headers
        headers: dict[str, str] = {}
        for header in request_data.get("header", []):
            if not header.get("disabled"):
                headers[header.get("key", "")] = header.get("value", "")

        # Handle body
        body = None
        body_type = BodyType.JSON
        body_data = request_data.get("body", {})
        if body_data:
            mode = body_data.get("mode", "raw")
            if mode == "raw":
                body = body_data.get("raw")
                body_type = BodyType.RAW
                # Try to detect JSON
                if body:
                    try:
                        body = json.loads(body)
                        body_type = BodyType.JSON
                    except json.JSONDecodeError:
                        pass
            elif mode == "formdata":
                body = {item["key"]: item["value"] for item in body_data.get("formdata", [])}
                body_type = BodyType.FORM
            elif mode == "urlencoded":
                body = {item["key"]: item["value"] for item in body_data.get("urlencoded", [])}
                body_type = BodyType.FORM

        # Handle scripts
        pre_script = None
        post_script = None
        for event in item.get("event", []):
            if event.get("listen") == "prerequest":
                script = event.get("script", {}).get("exec", [])
                pre_script = "\n".join(script) if script else None
            elif event.get("listen") == "test":
                script = event.get("script", {}).get("exec", [])
                post_script = "\n".join(script) if script else None

        return CollectionRequest(
            name=item.get("name", "Request"),
            method=HttpMethod(request_data.get("method", "GET").upper()),
            url=url,
            headers=headers,
            body=body,
            body_type=body_type,
            pre_request_script=pre_script,
            post_response_script=post_script,
        )

    def export_postman_collection(self, name: str) -> dict[str, Any] | None:
        """Export a collection to Postman v2.1 format."""
        collection = self._collections.get(name)
        if not collection:
            return None

        return {
            "info": {
                "_postman_id": f"api-workbench-{name}",
                "name": collection.name,
                "description": collection.description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": self._export_postman_items(collection),
            "variable": [
                {"key": k, "value": v}
                for k, v in collection.variables.items()
            ],
        }

    def _export_postman_items(self, collection: Collection) -> list[dict[str, Any]]:
        """Export collection items to Postman format."""
        items: list[dict[str, Any]] = []

        # Export folders first
        for folder in collection.folders:
            items.append(self._export_postman_folder(folder, collection))

        # Export requests not in folders
        folder_requests = set()
        for folder in collection.folders:
            folder_requests.update(self._collect_folder_requests(folder))

        for name, request in collection.requests.items():
            if name not in folder_requests:
                items.append(self._export_postman_request(request))

        return items

    def _export_postman_folder(
        self,
        folder: CollectionFolder,
        collection: Collection,
    ) -> dict[str, Any]:
        """Export a folder to Postman format."""
        items: list[dict[str, Any]] = []

        # Add requests
        for req_name in folder.requests:
            if req_name in collection.requests:
                items.append(self._export_postman_request(collection.requests[req_name]))

        # Add subfolders
        for subfolder in folder.folders:
            items.append(self._export_postman_folder(subfolder, collection))

        return {
            "name": folder.name,
            "description": folder.description,
            "item": items,
        }

    def _export_postman_request(self, request: CollectionRequest) -> dict[str, Any]:
        """Export a request to Postman format."""
        return {
            "name": request.name,
            "request": {
                "method": request.method.value,
                "url": {"raw": request.url},
                "header": [
                    {"key": k, "value": v}
                    for k, v in request.headers.items()
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(request.body) if isinstance(request.body, dict) else request.body,
                } if request.body else None,
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"exec": request.pre_request_script.split("\n")},
                } if request.pre_request_script else None,
                {
                    "listen": "test",
                    "script": {"exec": request.post_response_script.split("\n")},
                } if request.post_response_script else None,
            ],
        }

    def _collect_folder_requests(self, folder: CollectionFolder) -> set[str]:
        """Collect all request names in a folder and subfolders."""
        requests = set(folder.requests)
        for subfolder in folder.folders:
            requests.update(self._collect_folder_requests(subfolder))
        return requests
