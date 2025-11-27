"""
Configuration management for Minecraft Bedrock Admin Panel
Handles server connection settings and setup flow
"""

import json
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("Warning: bcrypt not installed, passwords will be stored in plaintext")

class Config:
    """Manages application configuration with persistence"""

    CONFIG_FILE = "/app/data/server_config.json"

    # Default configuration structure
    DEFAULT_CONFIG = {
        "setup_completed": False,
        "server": {
            "container_name": "",
            "server_host": "",
            "ssh_host": "",
            "ssh_user": "",
            "connection_type": "ssh"  # 'ssh' or 'local'
        },
        "map": {
            "enabled": False,
            "url": "",
            "type": "unmined"  # 'unmined', 'chunkbase', or 'custom'
        },
        "admin": {
            "username": "",
            "password_hash": ""  # Stored as bcrypt hash
        },
        "security": {
            "secret_key": "",  # Auto-generated on first run
            "ssl_verify": True  # Set to False for self-signed certs
        }
    }

    def __init__(self):
        self.config_path = Path(self.CONFIG_FILE)
        self.config = self._load_config()
        self._ensure_security_settings()

    def _ensure_security_settings(self):
        """Ensure security settings exist and secret_key is generated"""
        if 'security' not in self.config:
            self.config['security'] = self.DEFAULT_CONFIG['security'].copy()

        # Generate secret key if not set
        if not self.config['security'].get('secret_key'):
            self.config['security']['secret_key'] = secrets.token_hex(32)
            self.save()
            print("✓ Generated new secure secret key")

        # Migrate old plaintext password to hash if needed
        if 'admin' in self.config:
            if 'password' in self.config['admin'] and self.config['admin']['password']:
                # Old plaintext password exists, hash it
                plaintext = self.config['admin']['password']
                self.config['admin']['password_hash'] = self._hash_password(plaintext)
                del self.config['admin']['password']
                self.save()
                print("✓ Migrated admin password to secure hash")

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # Fallback: store as-is (not recommended for production)
            return f"plain:{password}"

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        if not password_hash:
            return False

        if BCRYPT_AVAILABLE and not password_hash.startswith('plain:'):
            try:
                return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            except Exception:
                return False
        else:
            # Fallback for plaintext passwords (migration case)
            stored = password_hash.replace('plain:', '') if password_hash.startswith('plain:') else password_hash
            return password == stored

    def verify_admin_password(self, password: str) -> bool:
        """Verify the admin password"""
        password_hash = self.config.get('admin', {}).get('password_hash', '')
        return self._verify_password(password, password_hash)

    def get_secret_key(self) -> str:
        """Get the secret key for Flask sessions"""
        return self.config.get('security', {}).get('secret_key', 'fallback-key-change-me')

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        # First check if config file exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._create_default_config()
        else:
            # Check if we have environment variables (legacy setup)
            if os.getenv('CONTAINER_NAME'):
                return self._migrate_from_env()
            else:
                return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = self.DEFAULT_CONFIG.copy()

        # Set admin credentials from environment if available
        config['admin']['username'] = os.getenv('ADMIN_USER', 'admin')
        config['admin']['password'] = os.getenv('ADMIN_PASS', '')

        return config

    def _migrate_from_env(self) -> Dict[str, Any]:
        """Migrate from environment variables to config file"""
        config = self.DEFAULT_CONFIG.copy()

        config['setup_completed'] = True
        config['server']['container_name'] = os.getenv('CONTAINER_NAME', '')
        config['server']['server_host'] = os.getenv('SERVER_HOST', '')
        config['server']['ssh_host'] = os.getenv('SSH_HOST', '')
        config['server']['ssh_user'] = os.getenv('SSH_USER', '')
        config['admin']['username'] = os.getenv('ADMIN_USER', 'admin')
        config['admin']['password'] = os.getenv('ADMIN_PASS', '')

        # Set config before saving
        self.config = config

        # Save the migrated config
        self.save()
        print("✓ Migrated configuration from environment variables")

        return config

    def save(self) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def is_setup_completed(self) -> bool:
        """Check if initial setup has been completed"""
        return self.config.get('setup_completed', False)

    def complete_setup(self, server_config: Dict[str, str], admin_config: Dict[str, str]) -> bool:
        """Complete initial setup with server and admin configuration"""
        self.config['setup_completed'] = True
        self.config['server'].update(server_config)

        # Hash the password before storing
        if 'password' in admin_config:
            self.config['admin']['username'] = admin_config.get('username', 'admin')
            self.config['admin']['password_hash'] = self._hash_password(admin_config['password'])
        else:
            self.config['admin'].update(admin_config)

        return self.save()

    def update_server_config(self, server_config: Dict[str, str]) -> bool:
        """Update server connection settings"""
        self.config['server'].update(server_config)
        return self.save()

    def update_admin_config(self, admin_config: Dict[str, str]) -> bool:
        """Update admin credentials"""
        if 'username' in admin_config:
            self.config['admin']['username'] = admin_config['username']

        # Hash new password if provided
        if 'password' in admin_config and admin_config['password']:
            self.config['admin']['password_hash'] = self._hash_password(admin_config['password'])

        return self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def get_server_config(self) -> Dict[str, str]:
        """Get server configuration"""
        return self.config.get('server', {})

    def get_admin_config(self) -> Dict[str, str]:
        """Get admin configuration"""
        return self.config.get('admin', {})

    def reset(self) -> bool:
        """Reset configuration to defaults"""
        self.config = self._create_default_config()
        return self.save()


# Global configuration instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get or create global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
