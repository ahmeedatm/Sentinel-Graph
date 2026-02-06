#!/usr/bin/env python3
"""
Setup Script for eBPF Graph-Based Intrusion Detection Project
Automates virtual environment creation and dependency installation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    RESET = '\033[0m'


class SetupManager:
    """Manages project setup and environment configuration"""
    
    def __init__(self):
        self.script_dir = Path(__file__).resolve().parent
        self.venv_dir = self.script_dir / "venv"
        self.python_exe = str(self.venv_dir / "bin" / "python")
        self.pip_exe = str(self.venv_dir / "bin" / "pip")
        self.os_type = platform.system()
        
    def print_header(self, title: str) -> None:
        """Print formatted header"""
        border = "━" * 70
        print(f"\n{Colors.BLUE}{border}{Colors.RESET}")
        print(f"{Colors.BLUE}{title}{Colors.RESET}")
        print(f"{Colors.BLUE}{border}{Colors.RESET}\n")
    
    def print_step(self, message: str) -> None:
        """Print step indicator"""
        print(f"{Colors.YELLOW}▶ {message}{Colors.RESET}")
    
    def print_success(self, message: str) -> None:
        """Print success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    
    def print_error(self, message: str) -> None:
        """Print error message"""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    
    def run_command(self, cmd: List[str], description: str = "") -> Tuple[int, str]:
        """Execute shell command and return exit code and output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            return 1, str(e)
    
    def check_python(self) -> bool:
        """Check Python installation and version"""
        self.print_step("Checking Python installation...")
        
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip() or result.stderr.strip()
            self.print_success(f"{version} found")
            
            # Check Python 3.9+
            parts = version.split()
            if len(parts) >= 2:
                try:
                    version_str = parts[1].split('.')
                    major = int(version_str[0])
                    minor = int(version_str[1])
                    version_num = float(f"{major}.{minor}")
                    
                    if version_num < 3.9:
                        self.print_error(f"Python 3.9+ required (found {version_num})")
                        return False
                except (ValueError, IndexError):
                    # If parsing fails, assume it's acceptable
                    pass
            
            return True
        except Exception as e:
            self.print_error(f"Failed to check Python: {e}")
            return False
    
    def check_pip(self) -> bool:
        """Check pip installation"""
        self.print_step("Checking pip installation...")
        
        returncode, _ = self.run_command([sys.executable, "-m", "pip", "--version"])
        if returncode == 0:
            self.print_success("pip is available")
            return True
        else:
            self.print_error("pip is not available")
            return False
    
    def create_venv(self) -> bool:
        """Create Python virtual environment"""
        self.print_step(f"Creating virtual environment: {self.venv_dir.name}")
        
        if self.venv_dir.exists():
            self.print_error(f"Virtual environment already exists at {self.venv_dir}")
            response = input("Recreate it? (y/n): ").strip().lower()
            
            if response != 'y':
                self.print_success("Using existing virtual environment")
                return True
            
            import shutil
            shutil.rmtree(self.venv_dir)
            self.print_step("Removed existing virtual environment")
        
        returncode, output = self.run_command(
            [sys.executable, "-m", "venv", str(self.venv_dir)]
        )
        
        if returncode == 0:
            self.print_success("Virtual environment created")
            return True
        else:
            self.print_error(f"Failed to create virtual environment: {output}")
            return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip, setuptools, and wheel"""
        self.print_step("Upgrading pip and build tools...")
        
        returncode, _ = self.run_command(
            [self.python_exe, "-m", "pip", "install", "--upgrade", 
             "pip", "setuptools", "wheel"]
        )
        
        if returncode == 0:
            self.print_success("pip and tools upgraded")
            return True
        else:
            self.print_error("Failed to upgrade pip")
            return False
    
    def install_requirements(self) -> bool:
        """Install Python dependencies"""
        self.print_step("Installing Python dependencies from requirement.txt...")
        
        req_file = self.script_dir / "requirement.txt"
        if not req_file.exists():
            self.print_error(f"requirement.txt not found at {req_file}")
            return False
        
        returncode, output = self.run_command(
            [self.pip_exe, "install", "-r", str(req_file)]
        )
        
        if returncode == 0:
            self.print_success("All dependencies installed successfully")
            return True
        else:
            self.print_error(f"Failed to install dependencies:\n{output}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env configuration file"""
        self.print_step("Creating .env configuration file...")
        
        env_file = self.script_dir / ".env"
        if env_file.exists():
            self.print_success(".env file already exists")
            return True
        
        env_content = """# Tetragon Configuration
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
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            self.print_success(".env file created")
            return True
        except Exception as e:
            self.print_error(f"Failed to create .env file: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary project directories"""
        self.print_step("Creating project directories...")
        
        try:
            directories = [
                self.script_dir / "data",
                self.script_dir / "models",
                self.script_dir / "logs",
                self.script_dir / "src" / "analysis" / "storage",
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            self.print_success("Directories created")
            return True
        except Exception as e:
            self.print_error(f"Failed to create directories: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify critical packages are installed"""
        self.print_step("Verifying installation...")
        
        test_code = """
import streamlit
import networkx
import pandas
import yaml
print("✓ Core packages verified")
"""
        
        returncode, output = self.run_command(
            [self.python_exe, "-c", test_code]
        )
        
        if returncode == 0:
            self.print_success("Installation verified")
            return True
        else:
            self.print_error(f"Installation verification failed:\n{output}")
            return False
    
    def display_summary(self) -> None:
        """Display setup summary and next steps"""
        self.print_header("Setup Complete! 🎉")
        
        # Get Python version
        python_version = subprocess.run(
            [self.python_exe, "--version"],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        print(f"{Colors.GREEN}Environment Information:{Colors.RESET}")
        print(f"  Python Version: {python_version}")
        print(f"  Virtual Environment: {self.venv_dir.name}")
        print(f"  Project Directory: {self.script_dir}\n")
        
        print(f"{Colors.GREEN}Next Steps:{Colors.RESET}")
        print(f"  1. Activate the virtual environment:")
        
        if self.os_type == "Windows":
            print(f"     {self.venv_dir}\\Scripts\\activate")
        else:
            print(f"     source {self.venv_dir}/bin/activate")
        
        print(f"\n  2. Verify installation:")
        print(f"     python -c 'import streamlit; import networkx; print(\"✓ Setup OK\")'")
        print(f"\n  3. Deploy Tetragon:")
        print(f"     kubectl apply -f infra/tetragon/")
        print(f"\n  4. Start the dashboard:")
        print(f"     streamlit run dashboard/app.py")
        print(f"\n  5. Check configuration in .env file\n")
        
        print(f"{Colors.YELLOW}Project Structure:{Colors.RESET}")
        print(f"  docs/       - Documentation & research")
        print(f"  infra/      - Kubernetes & eBPF policies")
        print(f"  src/        - Backend (ingestion & analysis)")
        print(f"  dashboard/  - Frontend visualization")
        print(f"  red_team/   - Attack simulation scripts\n")
    
    def run(self) -> bool:
        """Execute full setup process"""
        self.print_header("eBPF Graph-Based Intrusion Detection - Setup")
        
        os.chdir(self.script_dir)
        
        steps = [
            ("Check Python", self.check_python),
            ("Check pip", self.check_pip),
            ("Create Virtual Environment", self.create_venv),
            ("Upgrade pip", self.upgrade_pip),
            ("Install Requirements", self.install_requirements),
            ("Create .env File", self.create_env_file),
            ("Create Directories", self.create_directories),
            ("Verify Installation", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                self.print_error(f"Setup failed at: {step_name}")
                return False
        
        self.display_summary()
        self.print_success("Setup completed successfully!")
        return True


if __name__ == "__main__":
    manager = SetupManager()
    success = manager.run()
    sys.exit(0 if success else 1)
