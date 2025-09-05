#!/usr/bin/env python3
# /opt/agentzero/interfaces/claude_interface.py

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AgentResponse:
    content: str
    model_used: str
    execution_time: float
    tokens_used: int
    confidence: float

class ClaudeCodeInterface:
    """
    Interface principal usando Claude Code concept con CCProxy
    Implementa fallback chain: Puter.js -> Community SDK -> Direct API
    """
    
    def __init__(self):
        self.config = self.load_config()
        self.session = None
        self.fallback_chain = [
            self.puter_js_request,
            self.community_sdk_request, 
            self.direct_claude_request
        ]
        
    def load_config(self) -> Dict:
        """Carga configuración con múltiples providers"""
        return {
            "puter_js": {
                "endpoint": "https://puter.js.org/api/claude",
                "enabled": True,
                "daily_limit": 1000
            },
            "ccproxy": {
                "endpoint": "https://ccproxy.orchestre.dev/v1",
                "groq_key": os.getenv("GROQ_API_KEY"),
                "enabled": True
            },
            "community_sdk": {
                "github_repo": "anthropic-community/claude-sdk",
                "local_path": "/opt/agentzero/sdks/claude-community"
            },
            "direct_claude": {
                "api_key": os.getenv("CLAUDE_API_KEY"),
                "endpoint": "https://api.anthropic.com/v1/messages"
            }
        }
        
    async def puter_js_request(self, prompt: str, context: Dict) -> Optional[AgentResponse]:
        """
        Método 1: Puter.js - Completamente gratuito
        Simula Claude Code experience sin costo
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "prompt": prompt,
                    "model": "claude-3-sonnet",
                    "max_tokens": context.get("max_tokens", 4000),
                    "temperature": context.get("temperature", 0.3),
                    "system_context": context.get("system_role", "system_admin")
                }
                
                async with session.post(
                    self.config["puter_js"]["endpoint"],
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return AgentResponse(
                            content=data["response"],
                            model_used="claude-via-puter",
                            execution_time=data.get("execution_time", 0),
                            tokens_used=data.get("tokens", 0),
                            confidence=0.9
                        )
        except Exception as e:
            self.log(f"Puter.js failed: {e}")
            return None
            
    async def community_sdk_request(self, prompt: str, context: Dict) -> Optional[AgentResponse]:
        """
        Método 2: Community SDK - Anthropic community libraries
        """
        try:
            # Importar SDK community dinámicamente
            import sys
            sys.path.append(self.config["community_sdk"]["local_path"])
            from anthropic_sdk import ClaudeClient
            
            client = ClaudeClient(api_key=os.getenv("CLAUDE_API_KEY"))
            
            response = await client.complete(
                prompt=prompt,
                max_tokens=context.get("max_tokens", 4000),
                temperature=context.get("temperature", 0.3)
            )
            
            return AgentResponse(
                content=response.content,
                model_used="claude-community-sdk",
                execution_time=response.execution_time,
                tokens_used=response.usage.total_tokens,
                confidence=0.95
            )
            
        except Exception as e:
            self.log(f"Community SDK failed: {e}")
            return None
            
    async def ccproxy_groq_speedup(self, prompt: str, context: Dict) -> Optional[AgentResponse]:
        """
        Método CCProxy: Claude Code + Groq para velocidad extrema
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.config['ccproxy']['groq_key']}",
                "Content-Type": "application/json",
                "X-Proxy-Provider": "groq",
                "X-Target-Model": "llama-3.3-70b-versatile"
            }
            
            payload = {
                "model": "claude-3-sonnet-via-groq",
                "messages": [
                    {"role": "system", "content": context.get("system_role", "")},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": context.get("max_tokens", 4000),
                "temperature": context.get("temperature", 0.3)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["ccproxy"]["endpoint"] + "/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15  # Groq es ultra-rápido
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return AgentResponse(
                            content=data["choices"][0]["message"]["content"],
                            model_used="claude-groq-proxy",
                            execution_time=data.get("response_time", 0),
                            tokens_used=data["usage"]["total_tokens"],
                            confidence=0.85
                        )
                        
        except Exception as e:
            self.log(f"CCProxy Groq failed: {e}")
            return None

    async def intelligent_request(self, prompt: str, task_type: str = "general") -> AgentResponse:
        """
        Router inteligente que selecciona el mejor método según el tipo de tarea
        """
        context = {
            "system_role": "You are Agent Zero, a system administrator AI with root privileges",
            "max_tokens": 8000 if task_type == "complex" else 4000,
            "temperature": 0.1 if task_type == "system" else 0.3,
            "task_type": task_type
        }
        
        # Estrategia de routing por tipo de tarea
        if task_type == "code":
            # Para código: Mistral Codestral primero
            response = await self.mistral_codestral_request(prompt, context)
            if response: return response
            
        elif task_type == "fast":
            # Para respuestas rápidas: CCProxy + Groq
            response = await self.ccproxy_groq_speedup(prompt, context)
            if response: return response
            
        # Fallback chain para todo lo demás
        for method in self.fallback_chain:
            response = await method(prompt, context)
            if response:
                return response
                
        # Si todo falla, usar Groq directo como último recurso
        return await self.groq_fallback(prompt, context)
