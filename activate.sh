#!/bin/bash
# Quick activation script for the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR"
    echo "Run 'bash setup.sh' or 'python3 setup.py' first"
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Display activation info
echo "Virtual environment activated!"
echo "Python: $(python --version)"
echo "Location: $VENV_DIR"
echo ""
echo "Available commands:"
echo "  - streamlit run dashboard/app.py    (start dashboard)"
echo "  - deactivate                         (exit virtual environment)"
