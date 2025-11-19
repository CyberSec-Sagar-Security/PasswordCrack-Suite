#!/bin/bash
# GPX Setup Script for Linux/macOS
# This script installs all GPU detection dependencies

echo "============================================"
echo "  PasswordCrack GPX Setup"
echo "  Installing GPU/CPU Detection Packages"
echo "============================================"
echo ""

echo "[1/3] Installing GPUtil (Cross-platform GPU detection)..."
pip install gputil>=1.4.0
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install gputil"
    exit 1
fi
echo "   >> GPUtil installed successfully!"
echo ""

echo "[2/3] Installing pynvml (NVIDIA GPU support)..."
pip install pynvml>=11.5.0
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install pynvml"
    exit 1
fi
echo "   >> pynvml installed successfully!"
echo ""

echo "[3/3] Installing psutil (System information)..."
pip install psutil>=5.9.0
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install psutil"
    exit 1
fi
echo "   >> psutil installed successfully!"
echo ""

echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Run: python -m passwordcrack"
echo "  2. Click 'Diagnostics' button to verify GPU detection"
echo "  3. Click 'Rescan Devices' to detect your GPU"
echo ""
echo "For troubleshooting, see: GPX_TROUBLESHOOTING.md"
echo ""
