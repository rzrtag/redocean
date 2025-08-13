"""
Hash-based change detection for incremental updates.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class HashManager:
    """Manages content hashes for detecting changes."""

    def __init__(self, cache_dir: Path):
        """Initialize hash manager.

        Args:
            cache_dir: Directory to store hash cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hash_file = self.cache_dir / "content_hashes.json"
        self._hashes = self._load_hashes()

    def _load_hashes(self) -> Dict[str, str]:
        """Load existing hashes from cache file."""
        if self.hash_file.exists():
            try:
                with open(self.hash_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_hashes(self):
        """Save hashes to cache file."""
        with open(self.hash_file, 'w') as f:
            json.dump(self._hashes, f, indent=2)

    def get_content_hash(self, content: Union[str, bytes, Dict, list]) -> str:
        """Generate hash for content.

        Args:
            content: Content to hash

        Returns:
            SHA256 hash string
        """
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        elif isinstance(content, bytes):
            content_str = content.decode('utf-8', errors='ignore')
        else:
            content_str = str(content)

        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def has_changed(self, key: str, content: Union[str, bytes, Dict, list]) -> bool:
        """Check if content has changed since last check.

        Args:
            key: Unique identifier for the content
            content: Current content to check

        Returns:
            True if content has changed, False otherwise
        """
        current_hash = self.get_content_hash(content)
        previous_hash = self._hashes.get(key)

        if previous_hash != current_hash:
            self._hashes[key] = current_hash
            self._save_hashes()
            return True

        return False

    def get_hash(self, key: str) -> Optional[str]:
        """Get stored hash for a key.

        Args:
            key: Content identifier

        Returns:
            Stored hash or None if not found
        """
        return self._hashes.get(key)

    def set_hash(self, key: str, content: Union[str, bytes, Dict, list]):
        """Set hash for content without checking for changes.

        Args:
            key: Content identifier
            content: Content to hash
        """
        self._hashes[key] = self.get_content_hash(content)
        self._save_hashes()

    def clear_hash(self, key: str):
        """Remove hash for a key.

        Args:
            key: Content identifier to remove
        """
        if key in self._hashes:
            del self._hashes[key]
            self._save_hashes()

    def clear_all(self):
        """Clear all stored hashes."""
        self._hashes.clear()
        self._save_hashes()
