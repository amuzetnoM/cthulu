"""
Configuration management for Herald trading bot
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration loader and accessor"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
        
    def load(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.example.yaml to config.yaml and configure it."
            )
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'mt5.login' or 'trading.symbol')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config.get('mt5.login')
            123456789
            >>> config.get('trading.risk_per_trade', 0.01)
            0.01
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'mt5.login')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def save(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)
            
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section
        
        Args:
            section: Section name (e.g., 'mt5', 'trading')
            
        Returns:
            Dictionary of section configuration
        """
        return self.config.get(section, {})
        
    def validate(self) -> bool:
        """
        Validate required configuration fields
        
        Returns:
            True if configuration is valid
        """
        required_fields = [
            'mt5.login',
            'mt5.password',
            'mt5.server',
            'trading.symbol',
            'trading.timeframe',
            'trading.risk_per_trade',
            'strategy.name'
        ]
        
        missing = []
        for field in required_fields:
            if self.get(field) is None:
                missing.append(field)
                
        if missing:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing)}"
            )
            
        return True
