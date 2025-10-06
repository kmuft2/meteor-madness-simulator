#!/bin/bash
echo "=========================================="
echo "🚀 Installing React + Three.js App"
echo "=========================================="
echo ""

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo ""
    echo "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "✓ Node version: $(node --version)"
echo "✓ NPM version: $(npm --version)"
echo ""

echo "📦 Installing dependencies..."
npm install

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "🎬 To run the app:"
echo ""
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "=========================================="
