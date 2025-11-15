#!/bin/bash
# Setup script for publishing Pickaxe RCON to GitHub
# Run this after creating the repo at https://github.com/new

set -e

echo "🪓  Pickaxe RCON - GitHub Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Before running this script:"
echo "1. Go to https://github.com/new"
echo "2. Create a repository named: pickaxe-rcon
   Description: "Mine your way to better Minecraft Bedrock server management""
echo "3. Make it Public"
echo "4. Do NOT initialize with README, .gitignore, or license"
echo ""
read -p "Have you created the GitHub repo? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please create the GitHub repo first, then run this script again."
    exit 1
fi

echo ""
echo "📋 Verifying files..."

# Check for sensitive files that should NOT be committed
if [ -f .env ]; then
    echo "⚠️  Found .env file (will be ignored by .gitignore)"
fi

if [ -f update-and-deploy.sh ]; then
    echo "⚠️  Found update-and-deploy.sh (will be ignored by .gitignore)"
fi

echo ""
echo "🔍 Files that will be committed:"
git add -A --dry-run
echo ""

read -p "Does this look correct? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted. Please review files and try again."
    exit 1
fi

echo ""
echo "🚀 Initializing Git repository..."
git init

echo ""
echo "📝 Adding files..."
git add .

echo ""
echo "✅ Creating initial commit..."
git commit -m "🪓 Initial release: Pickaxe RCON v1.0.0

A powerful, user-friendly web-based admin panel for Minecraft Bedrock Edition servers.

Features:
- Real-time console with WebSocket support
- Player management (kick, OP, teleport, items)
- Server configuration editor
- World backup and restore
- Whitelist and operator management
- Performance monitoring
- Log viewer with search
- Task scheduler
- Map integration support
- Setup wizard for easy configuration"

echo ""
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/xtamtamx/pickaxe-rcon.git

echo ""
echo "📤 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Successfully published to GitHub!"
echo ""
echo "🎉 Your repository is now live at:"
echo "   https://github.com/xtamtamx/pickaxe-rcon"
echo ""
echo "📋 Next steps:"
echo "   1. Update README.md badges (replace 'xtamtamx' with 'xtamtamx')"
echo "   2. Take screenshots and update README.md"
echo "   3. Publish to Docker Hub: ./publish-docker.sh 1.0.0"
echo "   4. Create a GitHub release (tag: v1.0.0)"
echo ""
