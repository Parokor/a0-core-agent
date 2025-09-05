"""
Configuration Manager for Agent Zero
Handles loading, validation, and management of system configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

@dataclass
class AgentZeroConfig:
    """Main configuration structure"""
    system: Dict[str, Any]
    models: Dict[str, Any]
    security: Dict[str, Any]
    logging: Dict[str, Any]
    interfaces: Dict[str, Any]

class ConfigManager:
    """Manages Agent Zero configuration loading and validation"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.config_path = base_path / "config"
        self.env_path = base_path / ".env"
        self.logger = logging.getLogger(__name__)
        
    def load_environment_variables(self) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        
        if self.env_path.exists():
            try:
                with open(self.env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                self.logger.error(f"Error loading .env file: {e}")
        
        return env_vars
    
    def get_default_config(self) -> AgentZeroConfig:
        """Return default configuration"""
        return AgentZeroConfig(
            system={
                "version": "1.0.0",
                "log_level": "INFO",
                "max_concurrent_tasks": 5,
                "task_poll_interval": 10,
                "safety_mode": True,
                "auto_approve_safe_commands": False,
                "auto_security_updates": False,
                "backup_before_changes": True
            },
            models={
                "primary_provider": "groq",
                "fallback_providers": ["openrouter", "huggingface"],
                "code_specialist": "mistral_codestral",
                "problem_solver": "kimi_k2",
                "web_automation": "huggingface_browser",
                "providers": {
                    "groq": {
                        "api_key": "${GROQ_API_KEY}",
                        "endpoint": "https://api.groq.com/openai/v1",
                        "models": {
                            "fast": "llama-3.3-70b-versatile",
                            "reasoning": "mixtral-8x22b-instruct-v0.1",
                            "code": "llama-3.1-70b-versatile"
                        },
                        "rate_limits": {
                            "requests_per_minute": 30,
                            "tokens_per_minute": 6000
                        }
                    },
                    "openrouter": {
                        "api_key": "${OPENROUTER_API_KEY}",
                        "endpoint": "https://openrouter.ai/api/v1",
                        "models": {
                            "kimi_k2": "moonshot/moonshot-v1-32k",
                            "deepseek": "deepseek/deepseek-r1:free",
                            "vision": "meta-llama/llama-3.2-90b-vision-instruct:free"
                        }
                    },
                    "mistral_codestral": {
                        "api_key": "${MISTRAL_API_KEY}",
                        "endpoint": "https://codestral.mistral.ai/v1",
                        "model": "codestral-latest",
                        "max_tokens": 8192,
                        "use_for_tasks": ["code_analysis", "code_generation", "debugging"]
                    },
                    "huggingface": {
                        "api_key": "${HUGGINGFACE_API_KEY}",
                        "endpoint": "https://api-inference.huggingface.co",
                        "models": {
                            "browser_use": "microsoft/DialoGPT-medium",
                            "embeddings": "sentence-transformers/all-MiniLM-L6-v2"
                        }
                    },
                    "claude_alternatives": {
                        "community_proxy": {
                            "enabled": False,
                            "endpoint": "${CLAUDE_PROXY_URL}",
                            "api_key": "${CLAUDE_API_KEY}"
                        },
                        "local_claude": {
                            "enabled": False,
                            "model": "claude-3-sonnet-local",
                            "endpoint": "http://localhost:8000/v1"
                        }
                    }
                }
            },
            security={
                "max_risk_level": 7,
                "require_confirmation_above_risk": 5,
                "blocked_commands": [
                    "rm -rf /", "mkfs", "dd if=/dev/zero", ":(){ :|:& };:",
                    "sudo rm -rf", "format", "fdisk"
                ],
                "allowed_sudo_commands": [
                    "pacman", "systemctl", "journalctl", "mount", "umount",
                    "ip", "iptables", "ufw", "fail2ban-client"
                ],
                "audit_logging": True,
                "backup_before_critical": True,
                "sandbox_mode": False
            },
            logging={
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5,
                "log_to_syslog": True,
                "log_to_file": True,
                "log_api_calls": True,
                "sensitive_data_masking": True
            },
            interfaces={
                "claude": {
                    "enabled": True,
                    "mode": "fallback_chain",
                    "timeout": 30
                },
                "web": {
                    "enabled": False,
                    "host": "127.0.0.1",
                    "port": 8080,
                    "auth_required": True,
                    "ssl_enabled": False
                },
                "cli": {
                    "enabled": True,
                    "interactive_mode": True
                }
            }
        )
    
    def substitute_environment_variables(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively substitute environment variables in configuration"""
        if isinstance(config_dict, dict):
            return {k: self.substitute_environment_variables(v) for k, v in config_dict.items()}
        elif isinstance(config_dict, list):
            return [self.substitute_environment_variables(item) for item in config_dict]
        elif isinstance(config_dict, str) and config_dict.startswith("${") and config_dict.endswith("}"):
            env_var = config_dict[2:-1]
            return os.getenv(env_var, config_dict)
        else:
            return config_dict
    
    def validate_configuration(self, config: AgentZeroConfig) -> bool:
        """Validate configuration completeness and correctness"""
        errors = []
        
        # Check required API keys
        required_apis = []
        available_apis = []
        
        # Check Groq (primary)
        if os.getenv("GROQ_API_KEY"):
            available_apis.append("groq")
        else:
            required_apis.append("groq")
        
        # Check OpenRouter (secondary)
        if os.getenv("OPENROUTER_API_KEY"):
            available_apis.append("openrouter")
        
        # Check optional APIs
        if os.getenv("MISTRAL_API_KEY"):
            available_apis.append("mistral_codestral")
        
        if os.getenv("HUGGINGFACE_API_KEY"):
            available_apis.append("huggingface")
        
        # Validate minimum requirements
        if not available_apis:
            errors.append("No API keys configured. At least GROQ_API_KEY is required.")
        
        if required_apis:
            self.logger.warning(f"Missing recommended APIs: {required_apis}")
            self.logger.info("System will run with reduced capabilities")
        
        # Validate paths
        required_paths = [
            self.base_path / "tasks",
            self.base_path / "logs",
            self.base_path / "config"
        ]
        
        for path in required_paths:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created directory: {path}")
                except Exception as e:
                    errors.append(f"Cannot create directory {path}: {e}")
        
        # Validate security settings
        if config.security["max_risk_level"] > 10:
            errors.append("max_risk_level cannot exceed 10")
        
        if config.security["require_confirmation_above_risk"] > config.security["max_risk_level"]:
            errors.append("require_confirmation_above_risk cannot exceed max_risk_level")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            return False
        
        self.logger.info(f"Configuration validated. Available APIs: {available_apis}")
        return True
    
    def load_config(self) -> AgentZeroConfig:
        """Load complete configuration from files and environment"""
        # Load environment variables first
        self.load_environment_variables()
        
        # Start with default configuration
        config = self.get_default_config()
        
        # Try to load custom configuration file
        config_file = self.config_path / "agent_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    custom_config = json.load(f)
                
                # Merge custom configuration
                config_dict = asdict(config)
                self._deep_merge(config_dict, custom_config)
                
                # Substitute environment variables
                config_dict = self.substitute_environment_variables(config_dict)
                
                # Create new config object
                config = AgentZeroConfig(**config_dict)
                
                self.logger.info("Custom configuration loaded")
                
            except Exception as e:
                self.logger.error(f"Error loading custom configuration: {e}")
                self.logger.info("Using default configuration")
        
        # Validate configuration
        if not self.validate_configuration(config):
            raise ValueError("Configuration validation failed")
        
        return config
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict):
        """Recursively merge update_dict into base_dict"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def save_config(self, config: AgentZeroConfig):
        """Save configuration to file"""
        config_file = self.config_path / "agent_config.json"
        
        try:
            self.config_path.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
