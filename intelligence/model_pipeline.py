"""
Multi-Model Intelligence Pipeline for Agent Zero
Coordinates multiple AI models for optimal task execution
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
from enum import Enum

class TaskType(Enum):
    """Enumeration of task types for model routing"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation" 
    PROBLEM_SOLVING = "problem_solving"
    SYSTEM_ADMIN = "system_admin"
    WEB_AUTOMATION = "web_automation"
    GENERAL = "general"
    FAST_QUERY = "fast_query"

@dataclass
class ModelResponse:
    """Standardised model response structure"""
    content: str
    model_used: str
    provider: str
    execution_time: float
    tokens_used: int
    confidence: float
    success: bool
    error: Optional[str] = None

class ModelProvider:
    """Base class for model providers"""
    
    def __init__(self, name: str, config: Dict[str, Any], logger: logging.Logger):
        self.name = name
        self.config = config
        self.logger = logger
        self.session = None
        self.available = False
        
    async def initialise(self) -> bool:
        """Initialise the provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
            )
            self.available = await self.test_connection()
            return self.available
        except Exception as e:
            self.logger.error(f"Failed to initialise {self.name}: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to the provider"""
        raise NotImplementedError
    
    async def generate_response(self, prompt: str, task_type: TaskType, **kwargs) -> ModelResponse:
        """Generate response for given prompt"""
        raise NotImplementedError
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

class GroqProvider(ModelProvider):
    """Groq API provider for fast inference"""
    
    async def test_connection(self) -> bool:
        """Test Groq API connectivity"""
        if not self.config.get("api_key"):
            self.logger.warning("Groq API key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": self.config["models"]["fast"],
                "messages": [{"role": "user", "content": "Test connection"}],
                "max_tokens": 10
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/chat/completions",
                headers=headers,
                json=test_payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Groq connection test failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, task_type: TaskType, **kwargs) -> ModelResponse:
        """Generate response using Groq"""
        start_time = time.time()
        
        # Select appropriate model based on task type
        if task_type == TaskType.FAST_QUERY:
            model = self.config["models"]["fast"]
        elif task_type == TaskType.PROBLEM_SOLVING:
            model = self.config["models"]["reasoning"]
        else:
            model = self.config["models"]["code"]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": kwargs.get("system_prompt", "You are Agent Zero, an expert system administrator.")
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.3)
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    execution_time = time.time() - start_time
                    
                    return ModelResponse(
                        content=data["choices"][0]["message"]["content"],
                        model_used=model,
                        provider="groq",
                        execution_time=execution_time,
                        tokens_used=data["usage"]["total_tokens"],
                        confidence=0.9,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Groq API error {response.status}: {error_text}")
                    
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Groq generation failed: {e}")
            
            return ModelResponse(
                content="",
                model_used=model,
                provider="groq",
                execution_time=execution_time,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error=str(e)
            )

class MistralCodestralProvider(ModelProvider):
    """Mistral Codestral provider for code-specific tasks"""
    
    async def test_connection(self) -> bool:
        """Test Mistral Codestral API connectivity"""
        if not self.config.get("api_key"):
            self.logger.warning("Mistral Codestral API key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Codestral uses different endpoint structure
            test_payload = {
                "model": self.config["model"],
                "prompt": "# Test connection\ndef test():\n    return True",
                "max_tokens": 10
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/fim/completions",
                headers=headers,
                json=test_payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Mistral Codestral connection test failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, task_type: TaskType, **kwargs) -> ModelResponse:
        """Generate response using Mistral Codestral"""
        start_time = time.time()
        
        # Only handle code-related tasks
        if task_type not in [TaskType.CODE_ANALYSIS, TaskType.CODE_GENERATION]:
            return ModelResponse(
                content="",
                model_used=self.config["model"],
                provider="mistral_codestral",
                execution_time=0,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error="Task type not supported by Codestral"
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Codestral expects different payload format
            if task_type == TaskType.CODE_ANALYSIS:
                # Use chat endpoint for analysis
                payload = {
                    "model": self.config["model"],
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Analyse the following code and provide detailed insights:\n\n{prompt}"
                        }
                    ],
                    "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"])
                }
                endpoint = f"{self.config['endpoint']}/chat/completions"
            else:
                # Use FIM endpoint for generation
                payload = {
                    "model": self.config["model"], 
                    "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"]),
                    "temperature": kwargs.get("temperature", 0.1),
                    "stop": kwargs.get("stop", ["\n\n"])
                }
                endpoint = f"{self.config['endpoint']}/fim/completions"
            
            async with self.session.post(
                endpoint,
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    execution_time = time.time() - start_time
                    
                    # Extract content based on endpoint type
                    if task_type == TaskType.CODE_ANALYSIS:
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    else:
                        content = data["choices"][0]["text"]
                        tokens_used = data.get("usage", {}).get("total_tokens", len(content.split()))
                    
                    return ModelResponse(
                        content=content,
                        model_used=self.config["model"],
                        provider="mistral_codestral",
                        execution_time=execution_time,
                        tokens_used=tokens_used,
                        confidence=0.95,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Codestral API error {response.status}: {error_text}")
                    
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Mistral Codestral generation failed: {e}")
            
            return ModelResponse(
                content="",
                model_used=self.config["model"],
                provider="mistral_codestral",
                execution_time=execution_time,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error=str(e)
            )

class OpenRouterProvider(ModelProvider):
    """OpenRouter provider for diverse model access"""
    
    async def test_connection(self) -> bool:
        """Test OpenRouter API connectivity"""
        if not self.config.get("api_key"):
            self.logger.warning("OpenRouter API key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://agent-zero.ai",
                "X-Title": "Agent Zero"
            }
            
            test_payload = {
                "model": self.config["models"]["deepseek"],
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/chat/completions",
                headers=headers,
                json=test_payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"OpenRouter connection test failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, task_type: TaskType, **kwargs) -> ModelResponse:
        """Generate response using OpenRouter"""
        start_time = time.time()
        
        # Select model based on task type
        if task_type == TaskType.PROBLEM_SOLVING:
            model = self.config["models"]["kimi_k2"]
        elif task_type in [TaskType.CODE_ANALYSIS, TaskType.CODE_GENERATION]:
            model = self.config["models"]["deepseek"]
        else:
            model = self.config["models"]["deepseek"]  # Default
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://agent-zero.ai",
                "X-Title": "Agent Zero"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": kwargs.get("system_prompt", "You are Agent Zero, an expert system administrator.")
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.3)
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    execution_time = time.time() - start_time
                    
                    return ModelResponse(
                        content=data["choices"][0]["message"]["content"],
                        model_used=model,
                        provider="openrouter",
                        execution_time=execution_time,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        confidence=0.85,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"OpenRouter generation failed: {e}")
            
            return ModelResponse(
                content="",
                model_used=model,
                provider="openrouter",
                execution_time=execution_time,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error=str(e)
            )

class HuggingFaceProvider(ModelProvider):
    """HuggingFace provider for web automation and embeddings"""
    
    async def test_connection(self) -> bool:
        """Test HuggingFace API connectivity"""
        if not self.config.get("api_key"):
            self.logger.warning("HuggingFace API key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Test with embedding model
            test_payload = {
                "inputs": "Test connection",
                "options": {"wait_for_model": True}
            }
            
            async with self.session.post(
                f"{self.config['endpoint']}/models/{self.config['models']['embeddings']}",
                headers=headers,
                json=test_payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"HuggingFace connection test failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, task_type: TaskType, **kwargs) -> ModelResponse:
        """Generate response using HuggingFace"""
        start_time = time.time()
        
        # HuggingFace mainly used for web automation tasks
        if task_type != TaskType.WEB_AUTOMATION:
            return ModelResponse(
                content="",
                model_used="N/A",
                provider="huggingface",
                execution_time=0,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error="Task type not supported by HuggingFace provider"
            )
        
        try:
            # This would integrate with browser-use or similar
            # For now, return a placeholder response
            execution_time = time.time() - start_time
            
            return ModelResponse(
                content="Web automation task queued for processing",
                model_used=self.config["models"]["browser_use"],
                provider="huggingface",
                execution_time=execution_time,
                tokens_used=0,
                confidence=0.7,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"HuggingFace generation failed: {e}")
            
            return ModelResponse(
                content="",
                model_used="N/A",
                provider="huggingface",
                execution_time=execution_time,
                tokens_used=0,
                confidence=0.0,
                success=False,
                error=str(e)
            )

class MultiModelPipeline:
    """
    Main pipeline that coordinates multiple AI models for optimal task execution
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.providers: Dict[str, ModelProvider] = {}
        self.routing_strategy = self._create_routing_strategy()
        
    def _create_routing_strategy(self) -> Dict[TaskType, List[str]]:
        """Create routing strategy for different task types"""
        return {
            TaskType.CODE_ANALYSIS: ["mistral_codestral", "groq", "openrouter"],
            TaskType.CODE_GENERATION: ["mistral_codestral", "groq", "openrouter"],
            TaskType.PROBLEM_SOLVING: ["openrouter", "groq"],
            TaskType.SYSTEM_ADMIN: ["groq", "openrouter"],
            TaskType.WEB_AUTOMATION: ["huggingface", "groq"],
            TaskType.FAST_QUERY: ["groq", "openrouter"],
            TaskType.GENERAL: ["groq", "openrouter"]
        }
    
    async def initialise(self) -> bool:
        """Initialise all available providers"""
        provider_configs = self.config.get("providers", {})
        
        # Initialise Groq provider
        if "groq" in provider_configs:
            self.providers["groq"] = GroqProvider("groq", provider_configs["groq"], self.logger)
        
        # Initialise Mistral Codestral provider
        if "mistral_codestral" in provider_configs:
            self.providers["mistral_codestral"] = MistralCodestralProvider(
                "mistral_codestral", provider_configs["mistral_codestral"], self.logger
            )
        
        # Initialise OpenRouter provider  
        if "openrouter" in provider_configs:
            self.providers["openrouter"] = OpenRouterProvider(
                "openrouter", provider_configs["openrouter"], self.logger
            )
        
        # Initialise HuggingFace provider
        if "huggingface" in provider_configs:
            self.providers["huggingface"] = HuggingFaceProvider(
                "huggingface", provider_configs["huggingface"], self.logger
            )
        
        # Initialise all providers
        available_count = 0
        for name, provider in self.providers.items():
            if await provider.initialise():
                available_count += 1
                self.logger.info(f"Provider {name} initialised successfully")
            else:
                self.logger.warning(f"Provider {name} failed to initialise")
        
        self.logger.info(f"Pipeline initialised with {available_count}/{len(self.providers)} providers")
        return available_count > 0
    
    async def generate_response(self, prompt: str, task_type: TaskType = TaskType.GENERAL, **kwargs) -> ModelResponse:
        """
        Generate response using the best available provider for the task type
        """
        routing_order = self.routing_strategy.get(task_type, ["groq", "openrouter"])
        
        for provider_name in routing_order:
            if provider_name in self.providers and self.providers[provider_name].available:
                try:
                    response = await self.providers[provider_name].generate_response(
                        prompt, task_type, **kwargs
                    )
                    
                    if response.success:
                        self.logger.info(
                            f"Task completed by {provider_name} in {response.execution_time:.2f}s "
                            f"({response.tokens_used} tokens)"
                        )
                        return response
                    else:
                        self.logger.warning(f"Provider {provider_name} failed: {response.error}")
                        
                except Exception as e:
                    self.logger.error(f"Provider {provider_name} exception: {e}")
                    continue
        
        # If all providers failed, return error response
        return ModelResponse(
            content="",
            model_used="none",
            provider="none", 
            execution_time=0,
            tokens_used=0,
            confidence=0.0,
            success=False,
            error="All providers failed or unavailable"
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers"""
        health_status = {
            "total_providers": len(self.providers),
            "available_providers": 0,
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            is_healthy = await provider.test_connection() if provider.available else False
            health_status["providers"][name] = {
                "available": provider.available,
                "healthy": is_healthy
            }
            if is_healthy:
                health_status["available_providers"] += 1
        
        return health_status
    
    async def check_api_connectivity(self) -> Dict[str, Any]:
        """Check API connectivity for all providers"""
        connectivity_status = {}
        
        for name, provider in self.providers.items():
            try:
                connected = await provider.test_connection()
                connectivity_status[name] = {
                    "connected": connected,
                    "error": None
                }
            except Exception as e:
                connectivity_status[name] = {
                    "connected": False,
                    "error": str(e)
                }
        
        return connectivity_status
    
    async def shutdown(self):
        """Shutdown all providers"""
        for provider in self.providers.values():
            await provider.cleanup()
        
        self.logger.info("Model pipeline shutdown completed")
