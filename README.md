# Agent Zero - Enterprise System Agent for Arch Linux

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux-blue.svg)](https://archlinux.org/)

**Agent Zero** is an enterprise-grade autonomous system agent designed for Arch Linux environments. It combines multiple AI models through a sophisticated pipeline to provide intelligent system administration, code analysis, web automation, and problem-solving capabilities with root/admin privileges.

## 🚀 **Features**

- **Multi-Model Intelligence Pipeline:** Combines Groq (fast inference), Mistral Codestral (code expertise), Kimi K2 (problem solving), and HuggingFace (web automation)
- **Claude-like Interface:** Free alternatives to Anthropic's Claude API through community solutions
- **System Native Integration:** Direct Arch Linux integration with systemd services
- **Root/Admin Capabilities:** Secure execution of system-level commands with safety constraints
- **MCP Protocol Support:** Extensible tool integration via Model Context Protocol
- **Graceful Degradation:** Functions optimally with available APIs, degrades gracefully when services unavailable
- **Enterprise Security:** Comprehensive audit trails, risk assessment, and rollback capabilities

## 📋 **Prerequisites**

### System Requirements
- **OS:** Arch Linux (kernel 5.15+)
- **Python:** 3.11 or higher
- **RAM:** Minimum 4GB (8GB recommended)
- **Storage:** 2GB available space
- **Network:** Stable internet connection for API access

### Required Packages
```bash
sudo pacman -S python python-pip python-aiohttp python-asyncio git nodejs npm
```

## 🔑 **API Keys Setup**

Agent Zero supports multiple AI providers with graceful fallbacks. **Not all APIs are required** - the system will adapt based on available services.

### Required APIs (Minimum Setup)
1. **Groq API** (Primary - Free Tier)
   - Visit: https://console.groq.com/
   - Register and create API key
   - Free tier: 30 requests/minute, 6,000 tokens/minute

2. **OpenRouter API** (Secondary - $1 initial credit)
   - Visit: https://openrouter.ai/
   - Register and create API key
   - Provides access to Kimi K2 and other models

### Optional APIs (Enhanced Capabilities)
3. **Mistral Codestral API** (Code Specialisation)
   - Visit: https://console.mistral.ai/
   - Apply for Codestral API access (often free for developers)
   - Specialised for code analysis and generation

4. **HuggingFace API** (Web Automation)
   - Visit: https://huggingface.co/settings/tokens
   - Create read token
   - Enables browser automation via browser-use

5. **Claude API Alternatives** (Premium Experience)
   - **Option A:** Community Claude Proxies (if available)
   - **Option B:** Local Claude-compatible models via Ollama
   - **Option C:** Use Groq's Llama models as Claude substitute

### API Keys Configuration

Create `/opt/agentzero/.env`:
```env
# Primary APIs (Required)
GROQ_API_KEY=gsk_your_groq_api_key_here
OPENROUTER_API_KEY=sk-or-your_openrouter_key_here

# Optional APIs (Enhanced capabilities)
MISTRAL_API_KEY=your_mistral_codestral_key_here
HUGGINGFACE_API_KEY=hf_your_huggingface_key_here

# Claude Alternatives (Optional)
CLAUDE_PROXY_URL=https://your-claude-proxy.com/v1
CLAUDE_API_KEY=sk-ant-your_key_if_available

# System Configuration
AGENT_LOG_LEVEL=INFO
AGENT_MAX_TOKENS=8192
AGENT_TEMPERATURE=0.3
```

## 📦 **Installation**

### Method 1: Quick Install (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/agent-zero.git
cd agent-zero

# Run installation script
sudo chmod +x install.sh
sudo ./install.sh
```

### Method 2: Manual Installation
```bash
# Create directory structure
sudo mkdir -p /opt/agentzero/{core,interfaces,intelligence,system,web,config,logs}
cd /opt/agentzero

# Clone repository
git clone https://github.com/yourusername/agent-zero.git .

# Install Python dependencies
pip install -r requirements.txt

# Set up configuration
sudo cp config/agent-zero.service /etc/systemd/system/
sudo cp config/.env.example .env

# Edit configuration
sudo nano .env  # Add your API keys

# Set permissions
sudo chown -R root:root /opt/agentzero
sudo chmod +x core/main.py

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable agent-zero.service
sudo systemctl start agent-zero.service
```

## ⚙️ **Configuration**

### Basic Configuration
Edit `/opt/agentzero/config/agent_config.json`:
```json
{
  "system": {
    "log_level": "INFO",
    "max_concurrent_tasks": 5,
    "safety_mode": true,
    "auto_approve_safe_commands": false
  },
  "models": {
    "primary_provider": "groq",
    "fallback_providers": ["openrouter", "huggingface"],
    "code_specialist": "mistral",
    "problem_solver": "kimi_k2"
  },
  "security": {
    "max_risk_level": 7,
    "require_confirmation_above_risk": 5,
    "blocked_commands": ["rm -rf /", "mkfs", "dd if=/dev/zero"],
    "allowed_sudo_commands": ["pacman", "systemctl", "journalctl"]
  }
}
```

### Mistral Codestral Integration

Mistral Codestral requires special configuration due to its code-specific nature:

1. **Obtain Codestral API Key:**
   ```bash
   # Visit https://console.mistral.ai/
   # Navigate to "API Keys" section
   # Create new key with "Codestral" model access
   # Note: Codestral may require application/approval process
   ```

2. **Codestral Configuration:**
   ```json
   {
     "mistral_codestral": {
       "api_key": "your_codestral_key",
       "endpoint": "https://codestral.mistral.ai/v1",
       "model": "codestral-latest",
       "max_tokens": 8192,
       "use_for_tasks": ["code_analysis", "code_generation", "debugging", "refactoring"]
     }
   }
   ```

3. **Integration Differences:**
   - Codestral uses different endpoint than standard Mistral API
   - Optimised for code-related tasks only
   - May have different rate limits and token costs
   - Requires specific model parameter (`codestral-latest` vs `mistral-7b`)

## 🖥️ **Usage**

### Starting Agent Zero
```bash
# Check service status
sudo systemctl status agent-zero.service

# View real-time logs
sudo journalctl -u agent-zero.service -f

# Interactive mode
sudo /opt/agentzero/core/main.py --interactive
```

### Basic Commands
```bash
# System health check
echo '{"type": "system_health", "action": "full_scan"}' > /opt/agentzero/tasks/health_check.json

# Code analysis
echo '{"type": "code_analysis", "file": "/path/to/code.py", "action": "analyse"}' > /opt/agentzero/tasks/code_check.json

# Web research
echo '{"type": "web_research", "query": "Arch Linux security updates", "depth": "comprehensive"}' > /opt/agentzero/tasks/research.json

# System update
echo '{"type": "system_update", "action": "check_and_prompt", "auto_approve": false}' > /opt/agentzero/tasks/update.json
```

### Web Interface (Optional)
Access the web dashboard at `http://localhost:8080` after starting the web service:
```bash
sudo systemctl start agent-zero-web.service
```

## 🛡️ **Security Features**

### Risk Assessment Matrix
- **Level 1-3:** Safe operations (file reading, system status)
- **Level 4-6:** Moderate risk (package installation, service restart)
- **Level 7-8:** High risk (system configuration changes)
- **Level 9-10:** Critical risk (filesystem operations, kernel changes)

### Safety Mechanisms
- **Command Whitelisting:** Only approved commands executed
- **Audit Trail:** Complete logging of all actions
- **Rollback Capability:** Automatic system snapshots via Timeshift
- **User Confirmation:** Required for operations above configured risk threshold
- **Resource Limits:** Prevents system overload

## 🔧 **Troubleshooting**

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs for errors
   sudo journalctl -u agent-zero.service --no-pager
   
   # Verify configuration
   python -m json.tool /opt/agentzero/config/agent_config.json
   
   # Test API connectivity
   /opt/agentzero/tools/test_apis.py
   ```

2. **API Key Issues**
   ```bash
   # Verify environment variables
   sudo -u root printenv | grep -E "(GROQ|OPENROUTER|MISTRAL|HUGGINGFACE)_API_KEY"
   
   # Test individual APIs
   /opt/agentzero/tools/test_groq.py
   /opt/agentzero/tools/test_mistral_codestral.py
   ```

3. **Permission Errors**
   ```bash
   # Fix ownership
   sudo chown -R root:root /opt/agentzero
   
   # Fix permissions
   sudo chmod -R 755 /opt/agentzero
   sudo chmod +x /opt/agentzero/core/main.py
   ```

### Model Fallback Behaviour

When APIs are unavailable, Agent Zero follows this hierarchy:

1. **Code Tasks:** Mistral Codestral → Groq Llama → OpenRouter DeepSeek
2. **Fast Tasks:** Groq Llama → OpenRouter Llama → HuggingFace
3. **Problem Solving:** Kimi K2 → Groq Mixtral → Groq Llama
4. **Web Automation:** HuggingFace browser-use → Manual fallback notification

## 📊 **Monitoring & Maintenance**

### Health Monitoring
```bash
# System status
/opt/agentzero/tools/system_status.py

# Performance metrics
/opt/agentzero/tools/performance_report.py

# API usage statistics
/opt/agentzero/tools/api_usage.py
```

### Log Analysis
```bash
# Error analysis
grep -E "(ERROR|CRITICAL)" /opt/agentzero/logs/agent.log

# Task completion rates
/opt/agentzero/tools/task_analytics.py

# Resource usage
/opt/agentzero/tools/resource_monitor.py
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 **Links**

- **Documentation:** [Wiki](https://github.com/yourusername/agent-zero/wiki)
- **Issues:** [GitHub Issues](https://github.com/yourusername/agent-zero/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/agent-zero/discussions)
- **Security:** [Security Policy](SECURITY.md)

## ⚠️ **Disclaimer**

Agent Zero operates with root privileges and can make system-level changes. Always review actions before approval and maintain system backups. Use responsibly and in accordance with your organisation's security policies.

---

**Agent Zero** - *Autonomous Intelligence for System Administration*
