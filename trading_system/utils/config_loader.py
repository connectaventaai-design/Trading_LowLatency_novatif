"""Configuration loader utility."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import re


class ConfigLoader:
    """Load and manage configuration files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir is None:
            # Default to config directory in trading_system
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
            
        # Load environment variables
        load_dotenv()
        
        self._configs: Dict[str, Dict[str, Any]] = {}
        
    def load(self, config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            config_name: Name of the config file (without .yaml extension)
            
        Returns:
            Dictionary containing configuration data
        """
        if config_name in self._configs:
            return self._configs[config_name]
            
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Substitute environment variables
        config = self._substitute_env_vars(config)
        
        self._configs[config_name] = config
        return config
        
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config.
        
        Args:
            config: Configuration data (dict, list, or str)
            
        Returns:
            Configuration with substituted environment variables
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME} pattern
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, config)
            for var_name in matches:
                env_value = os.getenv(var_name, '')
                config = config.replace(f'${{{var_name}}}', env_value)
            return config
        else:
            return config
            
    def get(self, config_name: str, *keys: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            config_name: Name of the config file
            *keys: Nested keys to traverse
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.load(config_name)
        
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
                
        return config
        
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
        
    def reload(self, config_name: Optional[str] = None) -> None:
        """
        Reload configuration files.
        
        Args:
            config_name: Specific config to reload, or None to reload all
        """
        if config_name:
            if config_name in self._configs:
                del self._configs[config_name]
            self.load(config_name)
        else:
            self._configs.clear()


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
