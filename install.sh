#!/bin/bash

# Agent Zero Installation Script
# Enterprise System Agent for Arch Linux

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/agentzero"
SERVICE_NAME="agent-zero"
USER_HOME="$HOME"

# Logging function
log() {
    echo -e "${GREEN}[INSTALL]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Please use sudo."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check if Arch Linux
    if [[ ! -f /etc/arch-release ]]; then
        error "This installer is designed for Arch Linux only."
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed."
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    local required_version="3.11"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        error "Python 3.11+ is required. Current version: $python_version"
    fi
    
    # Check available space (2GB minimum)
    local available_space=$(df /opt --output=avail | tail -n1 | tr -d '[:space:]')
    local required_space=2097152  # 2GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        error "Insufficient disk space. Required: 2GB, Available: $((available_space / 1024 / 1024))GB"
    fi
    
    info "System requirements check passed"
}

# Install system packages
install_packages() {
    log "Installing required system packages..."
    
    # Update package database
    pacman -Sy
    
    # Install required packages
    pacman -S --needed --noconfirm \
        python \
        python-pip \
        python-aiohttp \
        python-asyncio \
        git \
        nodejs \
        npm \
        systemd \
        logrotate \
        cronie \
        timeshift \
        wget \
        curl \
        jq
    
    info "System packages installed successfully"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install core dependencies
    pip install \
        aiohttp \
        asyncio \
        requests \
        python-dotenv \
        pyyaml \
        psutil \
        schedule \
        watchdog \
        cryptography \
        packaging
    
    # Install optional dependencies for enhanced functionality
    pip install \
        playwright \
        beautifulsoup4 \
        selenium \
        pandas \
        numpy \
        matplotlib \
        seaborn
    
    # Install browser-use if available
    pip install browser-use || warn "browser-use not available, web automation will be limited"
    
    info "Python dependencies installed successfully"
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    # Create main directories
    mkdir -p "$INSTALL_DIR"/{core,interfaces,intelligence,system,web,config,logs,tasks,backup,cache}
    
    # Create subdirectories
    mkdir -p "$INSTALL_DIR"/logs/{api,system,security,tasks}
    mkdir -p "$INSTALL_DIR"/tasks/{pending,completed,failed}
    mkdir -p "$INSTALL_DIR"/backup/{configs,snapshots}
    mkdir -p "$INSTALL_DIR"/config/{templates,custom}
    
    info "Directory structure created"
}

# Copy application files
copy_files() {
    log "Copying application files..."
    
    # Copy core files (these would be from the repository)
    # Note: In actual deployment, these would come from git clone
    
    # Create placeholder files for demonstration
    cat > "$INSTALL_DIR/core/__init__.py" << 'EOF'
"""
Agent Zero Core Package
"""
__version__ = "1.0.0"
EOF

    # Copy main application file
    if [[ -f "core/main.py" ]]; then
        cp core/main.py "$INSTALL_DIR/core/"
    else
        warn "main.py not found in current directory, using template"
    fi
    
    # Copy configuration files
    if [[ -f "config/agent_config.json" ]]; then
        cp config/agent_config.json "$INSTALL_DIR/config/"
    fi
    
    # Copy service file
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Agent Zero - Enterprise System Agent
After=network.target multi-user.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/core/main.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=false
ProtectSystem=false
ProtectHome=true
PrivateTmp=true
PrivateDevices=false

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
EOF
    
    info "Application files copied"
}

# Set up configuration
setup_configuration() {
    log "Setting up configuration..."
    
    # Create default .env file
    cat > "$INSTALL_DIR/.env.example" << 'EOF'
# Agent Zero Configuration
# Copy this file to .env and configure your API keys

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
AGENT_SAFETY_MODE=true
AGENT_AUTO_APPROVE_SAFE=false

# Web Interface (Optional)
WEB_INTERFACE_ENABLED=false
WEB_INTERFACE_HOST=127.0.0.1
WEB_INTERFACE_PORT=8080
WEB_INTERFACE_AUTH=true

# Security Settings
MAX_RISK_LEVEL=7
REQUIRE_CONFIRMATION_ABOVE=5
AUDIT_LOGGING=true
BACKUP_BEFORE_CRITICAL=true
EOF

    # Create default agent configuration
    cat > "$INSTALL_DIR/config/agent_config.json" << 'EOF'
{
  "system": {
    "version": "1.0.0",
    "log_level": "INFO",
    "max_concurrent_tasks": 5,
    "task_poll_interval": 10,
    "safety_mode": true,
    "auto_approve_safe_commands": false,
    "auto_security_updates": false,
    "backup_before_changes": true
  },
  "models": {
    "primary_provider": "groq",
    "fallback_providers": ["openrouter", "huggingface"],
    "code_specialist": "mistral_codestral",
    "problem_solver": "kimi_k2"
  },
  "security": {
    "max_risk_level": 7,
    "require_confirmation_above_risk": 5,
    "blocked_commands": ["rm -rf /", "mkfs", "dd if=/dev/zero"],
    "allowed_sudo_commands": ["pacman", "systemctl", "journalctl"],
    "audit_logging": true,
    "backup_before_critical": true
  },
  "logging": {
    "level": "INFO",
    "max_file_size": "10MB",
    "backup_count": 5,
    "log_to_syslog": true,
    "log_api_calls": true
  },
  "interfaces": {
    "claude": {
      "enabled": true,
      "mode": "fallback_chain"
    },
    "web": {
      "enabled": false,
      "host": "127.0.0.1",
      "port": 8080
    }
  }
}
EOF

    info "Configuration files created"
}

# Set permissions
set_permissions() {
    log "Setting file permissions..."
    
    # Set ownership
    chown -R root:root "$INSTALL_DIR"
    
    # Set directory permissions
    find "$INSTALL_DIR" -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find "$INSTALL_DIR" -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    find "$INSTALL_DIR" -name "*.py" -exec chmod +x {} \;
    find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \;
    
    # Secure sensitive files
    chmod 600 "$INSTALL_DIR/.env.example"
    
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        chmod 600 "$INSTALL_DIR/.env"
    fi
    
    info "Permissions set correctly"
}

# Configure system services
configure_services() {
    log "Configuring system services..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable Agent Zero service
    systemctl enable "$SERVICE_NAME.service"
    
    # Configure logrotate
    cat > "/etc/logrotate.d/agent-zero" << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload-or-restart $SERVICE_NAME || true
    endscript
}
EOF

    # Configure log directory in syslog
    echo "# Agent Zero logs" >> /etc/rsyslog.conf
    echo "if \$programname == 'agent-zero' then $INSTALL_DIR/logs/system.log" >> /etc/rsyslog.conf
    echo "& stop" >> /etc/rsyslog.conf
    
    # Restart rsyslog
    systemctl restart rsyslog
    
    info "System services configured"
}

# Install additional tools
install_tools() {
    log "Installing additional tools..."
    
    # Create management scripts
    cat > "$INSTALL_DIR/tools/azcli" << 'EOF'
#!/bin/bash
# Agent Zero CLI Tool

INSTALL_DIR="/opt/agentzero"

case "$1" in
    start)
        systemctl start agent-zero
        ;;
    stop)
        systemctl stop agent-zero
        ;;
    restart)
        systemctl restart agent-zero
        ;;
    status)
        systemctl status agent-zero
        ;;
    logs)
        journalctl -u agent-zero -f
        ;;
    health)
        curl -s http://localhost:8080/api/health 2>/dev/null || echo "Health check unavailable"
        ;;
    config)
        nano "$INSTALL_DIR/.env"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health|config}"
        exit 1
        ;;
esac
EOF

    chmod +x "$INSTALL_DIR/tools/azcli"
    ln -sf "$INSTALL_DIR/tools/azcli" "/usr/local/bin/azcli"
    
    # Create backup script
    cat > "$INSTALL_DIR/tools/backup.sh" << 'EOF'
#!/bin/bash
# Agent Zero Backup Script

INSTALL_DIR="/opt/agentzero"
BACKUP_DIR="$INSTALL_DIR/backup/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/"
cp "$INSTALL_DIR/.env" "$BACKUP_DIR/" 2>/dev/null || true

# Backup logs (last 7 days)
find "$INSTALL_DIR/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# Create system snapshot with timeshift
if command -v timeshift &> /dev/null; then
    timeshift --create --comments "Agent Zero backup $(date)"
fi

echo "Backup created: $BACKUP_DIR"
EOF

    chmod +x "$INSTALL_DIR/tools/backup.sh"
    
    info "Additional tools installed"
}

# Perform security hardening
security_hardening() {
    log "Applying security hardening..."
    
    # Create dedicated user for Agent Zero (optional, for non-root mode)
    if ! id "agentzero" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" agentzero
    fi
    
    # Configure firewall rules
    if command -v ufw &> /dev/null; then
        # Allow SSH (assumed needed for administration)
        ufw allow ssh
        
        # Allow web interface if enabled
        # ufw allow 8080/tcp
        
        # Enable firewall
        # ufw --force enable
    fi
    
    # Set up audit logging
    if command -v auditctl &> /dev/null; then
        # Monitor Agent Zero directory
        auditctl -w "$INSTALL_DIR" -p wa -k agent-zero
        
        # Monitor system commands
        auditctl -w /bin/su -p x -k privilege-elevation
        auditctl -w /usr/bin/sudo -p x -k privilege-elevation
        auditctl -w /bin/mount -p x -k mount
    fi
    
    info "Security hardening applied"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check directory structure
    if [[ ! -d "$INSTALL_DIR/core" ]]; then
        error "Core directory not found"
    fi
    
    # Check Python environment
    if [[ ! -f "$INSTALL_DIR/venv/bin/python" ]]; then
        error "Python virtual environment not found"
    fi
    
    # Check service file
    if [[ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        error "Service file not found"
    fi
    
    # Test Python import
    cd "$INSTALL_DIR"
    if ! source venv/bin/activate && python -c "import aiohttp, asyncio, json"; then
        error "Python dependencies check failed"
    fi
    
    # Check service status
    if ! systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        error "Service not enabled"
    fi
    
    info "Installation verification passed"
}

# Display post-installation instructions
show_instructions() {
    log "Installation completed successfully!"
    
    echo
    echo -e "${BLUE}=== POST-INSTALLATION INSTRUCTIONS ===${NC}"
    echo
    echo "1. Configure API Keys:"
    echo "   sudo nano $INSTALL_DIR/.env"
    echo "   (Copy from .env.example and add your actual API keys)"
    echo
    echo "2. Start Agent Zero:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo
    echo "3. Check status:"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo
    echo "4. View logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
    echo
    echo "5. Use CLI tool:"
    echo "   azcli status"
    echo "   azcli logs"
    echo "   azcli health"
    echo
    echo -e "${YELLOW}=== REQUIRED APIS ===${NC}"
    echo "Minimum setup (required):"
    echo "  - Groq API: https://console.groq.com/"
    echo "  - OpenRouter API: https://openrouter.ai/"
    echo
    echo "Enhanced capabilities (optional):"
    echo "  - Mistral Codestral: https://console.mistral.ai/"
    echo "  - HuggingFace: https://huggingface.co/settings/tokens"
    echo
    echo -e "${GREEN}Agent Zero is ready to serve!${NC}"
    echo
}

# Main installation function
main() {
    log "Starting Agent Zero installation..."
    
    check_root
    check_requirements
    install_packages
    create_directories
    install_python_deps
    copy_files
    setup_configuration
    set_permissions
    configure_services
    install_tools
    security_hardening
    verify_installation
    show_instructions
    
    log "Installation completed successfully!"
}

# Run main function
main "$@"
