"""
Configuration management for Minecraft Bedrock Admin Panel
Handles server connection settings and setup flow
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

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
            "password": ""
        }
    }

    def __init__(self):
        self.config_path = Path(self.CONFIG_FILE)
        self.config = self._load_config()

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
        self.config['admin'].update(admin_config)
        return self.save()

    def update_server_config(self, server_config: Dict[str, str]) -> bool:
        """Update server connection settings"""
        self.config['server'].update(server_config)
        return self.save()

    def update_admin_config(self, admin_config: Dict[str, str]) -> bool:
        """Update admin credentials"""
        self.config['admin'].update(admin_config)
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
