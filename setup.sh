#!/bin/bash

##############################################################################
# Setup Script for eBPF Graph-Based Intrusion Detection Project
# Automates Python virtual environment creation and dependency installation
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ebpf-ids"
VENV_DIR="venv"
PYTHON_VERSION="3.10"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Python installation
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
    
    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $python_version found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip."
        exit 1
    fi
    
    print_success "pip3 is installed"
}

create_venv() {
    print_step "Creating virtual environment: $VENV_DIR"
    
    if [ -d "$VENV_DIR" ]; then
        print_error "Virtual environment already exists at $VENV_DIR"
        read -p "Do you want to recreate it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
            print_step "Removed existing virtual environment"
        else
            print_success "Using existing virtual environment"
            return
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
}

activate_venv() {
    print_step "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

upgrade_pip() {
    print_step "Upgrading pip, setuptools, and wheel..."
    python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    print_success "pip and tools upgraded"
}

install_requirements() {
    print_step "Installing Python dependencies from requirement.txt..."
    
    if [ ! -f "requirement.txt" ]; then
        print_error "requirement.txt not found in $SCRIPT_DIR"
        exit 1
    fi
    
    pip install -r requirement.txt
    
    if [ $? -eq 0 ]; then
        print_success "All dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

create_env_file() {
    print_step "Creating .env configuration file..."
    
    if [ -f ".env" ]; then
        print_success ".env file already exists"
        return
    fi
    
    cat > .env << 'EOF'
# Tetragon Configuration
TETRAGON_NAMESPACE=tetragon
TETRAGON_POD_SELECTOR=app=tetragon

# Kubernetes Configuration
KUBECONFIG=${HOME}/.kube/config
CLUSTER_NAME=kind-ebpf-ids

# Dashboard Configuration
STREAMLIT_PORT=8501
STREAMLIT_HOST=0.0.0.0

# Data Storage
DATA_DIR=./data
MODELS_DIR=./models
LOGS_DIR=./logs

# Analysis Settings
BASELINE_THRESHOLD=0.8
ANOMALY_THRESHOLD=0.7

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Logging
LOG_LEVEL=INFO
EOF
    
    print_success ".env file created"
}

create_directories() {
    print_step "Creating project directories..."
    
    mkdir -p data models logs
    mkdir -p src/analysis/storage
    
    print_success "Directories created"
}

display_summary() {
    print_header "Setup Complete! 🎉"
    
    echo -e "\n${GREEN}Environment Information:${NC}"
    echo "  Python Version: $(python --version)"
    echo "  Virtual Environment: $VENV_DIR"
    echo "  Project Directory: $SCRIPT_DIR"
    
    echo -e "\n${GREEN}Next Steps:${NC}"
    echo "  1. Activate the virtual environment:"
    echo "     source $VENV_DIR/bin/activate"
    echo ""
    echo "  2. Verify installation:"
    echo "     python -c 'import streamlit; import networkx; print(\"✓ Setup OK\")'"
    echo ""
    echo "  3. Deploy Tetragon:"
    echo "     kubectl apply -f infra/tetragon/"
    echo ""
    echo "  4. Start the dashboard:"
    echo "     streamlit run dashboard/app.py"
    echo ""
    echo "  5. Check configuration in .env file"
    echo ""
    
    echo -e "${YELLOW}Project Structure:${NC}"
    echo "  docs/       - Documentation & research"
    echo "  infra/      - Kubernetes & eBPF policies"
    echo "  src/        - Backend (ingestion & analysis)"
    echo "  dashboard/  - Frontend visualization"
    echo "  red_team/   - Attack simulation scripts"
    echo ""
}

main() {
    print_header "eBPF Graph-Based Intrusion Detection - Setup Script"
    
    cd "$SCRIPT_DIR"
    
    check_requirements
    create_venv
    activate_venv
    upgrade_pip
    install_requirements
    create_env_file
    create_directories
    display_summary
}

# Run main function
main

print_success "Setup script completed successfully!"
