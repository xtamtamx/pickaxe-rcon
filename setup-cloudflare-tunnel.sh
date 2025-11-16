#!/bin/bash
# Cloudflare Tunnel Setup for Pickaxe RCON
# This script sets up a secure tunnel from Cloudflare to your admin panel

set -e

echo "🌐 Cloudflare Tunnel Setup for Pickaxe RCON"
echo "============================================"
echo ""

# Check if cloudflared is already installed
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared is already installed"
    cloudflared --version
else
    echo "📥 Installing cloudflared..."

    # Download cloudflared for Linux x86_64
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/

    echo "✓ cloudflared installed successfully"
fi

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Login to Cloudflare:"
echo "   cloudflared tunnel login"
echo ""
echo "2. Create a tunnel:"
echo "   cloudflared tunnel create pickaxe-rcon"
echo ""
echo "3. Create tunnel config file at ~/.cloudflared/config.yml:"
echo "   ---"
echo "   tunnel: <TUNNEL-ID-FROM-STEP-2>"
echo "   credentials-file: /root/.cloudflared/<TUNNEL-ID>.json"
echo "   ingress:"
echo "     # Admin Panel (HTTPS)"
echo "     - hostname: admin.yourdomain.com"
echo "       service: http://localhost:41114"
echo "     # Minecraft Bedrock Server (UDP + TCP)"
echo "     - hostname: play.yourdomain.com"
echo "       service: tcp://your.server.ip:19132"
echo "     # Catch-all"
echo "     - service: http_status:404"
echo ""
echo "4. Route your domains:"
echo "   cloudflared tunnel route dns pickaxe-rcon admin.yourdomain.com"
echo "   cloudflared tunnel route dns pickaxe-rcon play.yourdomain.com"
echo ""
echo "5. Run the tunnel:"
echo "   cloudflared tunnel run pickaxe-rcon"
echo ""
echo "6. (Optional) Install as a service:"
echo "   cloudflared service install"
echo ""
