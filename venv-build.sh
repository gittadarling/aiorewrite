#!/usr/bin/env bash
# venv-build.sh
# Creates a Python virtual environment and installs requirements.

set -e

VENV_DIR="venv"

echo "Creating virtual environment in $VENV_DIR..."
python3 -m venv $VENV_DIR

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found!"
fi

echo "Virtual environment setup complete. To activate it, run:"
echo "source $VENV_DIR/bin/activate"
