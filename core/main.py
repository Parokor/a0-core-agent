#!/usr/bin/env python3
"""
Agent Zero - Enterprise System Agent
Core Application Entry Point

This module initialises and runs the Agent Zero system with multi-model
intelligence pipeline, system integration, and enterprise security features.
"""

import asyncio
import logging
import os
import sys
import signal
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Import core modules
from interfaces.claude_interface import ClaudeInterface
from interfaces.web_interface import WebInterface
from intelligence.model_pipeline import MultiModelPipeline
from system.native_integration import SystemIntegration
from system.security_manager import SecurityManager
from system.task_manager import TaskManager
from core.config_manager import ConfigManager
from core.logging_manager import LoggingManager

@dataclass
class AgentZeroConfig:
    """Main configuration structure for Agent Zero"""
    system: Dict[str, Any]
    models: Dict[str, Any]
    security: Dict[str, Any]
    logging: Dict[str, Any]
    interfaces: Dict[str, Any]

class AgentZero:
    """
    Main Agent Zero application class
    
    Coordinates all subsystems including model pipeline, system integration,
    security management, and user interfaces.
    """
    
    def __init__(self):
        self.base_path = Path("/opt/agentzero")
        self.config_manager = ConfigManager(self.base_path)
        self.logging_manager = LoggingManager(self.base_path)
        
        # Initialise logging first
        self.logger = self.logging_manager.get_logger(__name__)
        self.logger.info("Initialising Agent Zero...")
        
        # Load configuration
        self.config = self.config_manager.load_config()
        self.logger.info(f"Configuration loaded: {self.config.system['version']}")
        
        # Initialise core components
        self.model_pipeline = None
        self.system_integration = None
        self.security_manager = None
        self.task_manager = None
        self.claude_interface = None
        self.web_interface = None
        
        # Runtime state
        self.running = False
        self.startup_time = None
        
    async def initialise_components(self) -> bool:
        """
        Initialise all Agent Zero components
        
        Returns:
            bool: True if all components initialised successfully
        """
        try:
            self.logger.info("Initialising core components...")
            
            # Security manager (first for safety)
            self.security_manager = SecurityManager(
                self.config.security,
                self.logger
            )
            await self.security_manager.initialise()
            self.logger.info("Security manager initialised")
            
            # Model pipeline
            self.model_pipeline = MultiModelPipeline(
                self.config.models,
                self.logger
            )
            await self.model_pipeline.initialise()
            self.logger.info("Model pipeline initialised")
            
            # System integration
            self.system_integration = SystemIntegration(
                self.config.system,
                self.security_manager,
                self.logger
            )
            await self.system_integration.initialise()
            self.logger.info("System integration initialised")
            
            # Task manager
            self.task_manager = TaskManager(
                self.base_path / "tasks",
                self.model_pipeline,
                self.system_integration,
                self.security_manager,
                self.logger
            )
            await self.task_manager.initialise()
            self.logger.info("Task manager initialised")
            
            # Claude interface
            self.claude_interface = ClaudeInterface(
                self.config.interfaces.get("claude", {}),
                self.model_pipeline,
                self.logger
            )
            await self.claude_interface.initialise()
            self.logger.info("Claude interface initialised")
            
            # Web interface (optional)
            if self.config.interfaces.get("web", {}).get("enabled", False):
                self.web_interface = WebInterface(
                    self.config.interfaces["web"],
                    self.task_manager,
                    self.system_integration,
                    self.logger
                )
                await self.web_interface.initialise()
                self.logger.info("Web interface initialised")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Component initialisation failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check
        
        Returns:
            Dict containing health status of all components
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "system_resources": {},
            "api_status": {}
        }
        
        try:
            # Check component health
            if self.model_pipeline:
                health_status["components"]["model_pipeline"] = await self.model_pipeline.health_check()
            
            if self.system_integration:
                health_status["components"]["system_integration"] = await self.system_integration.health_check()
            
            if self.security_manager:
                health_status["components"]["security_manager"] = await self.security_manager.health_check()
            
            if self.task_manager:
                health_status["components"]["task_manager"] = await self.task_manager.health_check()
            
            # Check system resources
            health_status["system_resources"] = await self.system_integration.get_system_resources()
            
            # Check API connectivity
            health_status["api_status"] = await self.model_pipeline.check_api_connectivity()
            
            # Determine overall status
            component_failures = [
                comp for comp, status in health_status["components"].items()
                if status.get("status") != "healthy"
            ]
            
            if component_failures:
                health_status["overall_status"] = "degraded"
                health_status["failures"] = component_failures
                
            api_failures = [
                api for api, status in health_status["api_status"].items()
                if not status.get("connected", False)
            ]
            
            if api_failures:
                health_status["api_failures"] = api_failures
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "limited"
            
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status
    
    async def process_task_queue(self):
        """
        Main task processing loop
        """
        self.logger.info("Starting task processing loop...")
        
        while self.running:
            try:
                # Process pending tasks
                await self.task_manager.process_pending_tasks()
                
                # Perform periodic maintenance
                if datetime.now().minute % 30 == 0:  # Every 30 minutes
                    await self.perform_maintenance()
                
                # Sleep before next iteration
                await asyncio.sleep(self.config.system.get("task_poll_interval", 10))
                
            except Exception as e:
                self.logger.error(f"Task processing error: {e}")
                await asyncio.sleep(30)  # Extended sleep on error
    
    async def perform_maintenance(self):
        """
        Perform periodic system maintenance
        """
        self.logger.info("Performing maintenance cycle...")
        
        try:
            # Health check
            health = await self.health_check()
            self.logger.info(f"Health status: {health['overall_status']}")
            
            # Clean up old logs
            await self.logging_manager.cleanup_old_logs()
            
            # Update system information
            await self.system_integration.update_system_info()
            
            # Check for security updates
            if self.config.system.get("auto_security_updates", False):
                await self.system_integration.check_security_updates()
            
        except Exception as e:
            self.logger.error(f"Maintenance cycle failed: {e}")
    
    async def shutdown(self):
        """
        Graceful shutdown of all components
        """
        self.logger.info("Initiating shutdown sequence...")
        self.running = False
        
        try:
            # Stop task processing
            if self.task_manager:
                await self.task_manager.shutdown()
            
            # Close interfaces
            if self.web_interface:
                await self.web_interface.shutdown()
            
            if self.claude_interface:
                await self.claude_interface.shutdown()
            
            # Close system integration
            if self.system_integration:
                await self.system_integration.shutdown()
            
            # Close model pipeline
            if self.model_pipeline:
                await self.model_pipeline.shutdown()
            
            self.logger.info("Shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def run(self):
        """
        Main application run method
        """
        try:
            # Set up signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Initialise components
            if not await self.initialise_components():
                self.logger.error("Component initialisation failed")
                return False
            
            # Mark as running
            self.running = True
            self.startup_time = datetime.now()
            self.logger.info(f"Agent Zero started successfully at {self.startup_time}")
            
            # Initial health check
            health = await self.health_check()
            self.logger.info(f"Initial health status: {health['overall_status']}")
            
            # Start task processing
            await self.process_task_queue()
            
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
            return False
        
        finally:
            await self.shutdown()
        
        return True

async def main():
    """Main entry point"""
    try:
        # Check if running as root
        if os.geteuid() != 0:
            print("Agent Zero requires root privileges. Please run with sudo.")
            sys.exit(1)
        
        # Create Agent Zero instance
        agent = AgentZero()
        
        # Run the agent
        success = await agent.run()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
