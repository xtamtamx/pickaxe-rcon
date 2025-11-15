# Minecraft Bedrock Admin Panel

A comprehensive, Minecraft-themed web interface for managing your Minecraft Bedrock server running on QNAP NAS.

## Features

### Core Features
- 🎮 **Minecraft-themed UI** with pixel fonts and game-inspired design
- 📟 **Live console** for sending commands to your server with real-time output
- 💚 **Server status monitoring** with player count and auto-refresh
- 🔐 **Secure login** with admin credentials
- 🐳 **Docker-based** for easy deployment

### Management Features
- ⚙️ **Server Properties Editor** - Edit seed, difficulty, gamemode, performance settings
- 📋 **Whitelist Management** - Add/remove players, enable/disable whitelist mode
- 👥 **Player Management** - Kick players, grant/remove OP status
- 📜 **Gamerules Editor** - Toggle common game rules with easy buttons
- ⚡ **Quick Actions** - Common commands accessible via buttons

## Prerequisites

- Docker and Docker Compose installed on your Mac Mini
- SSH access to your QNAP NAS
- Minecraft Bedrock server running in a Docker container on QNAP

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd minecraft-rcon-panel
   ```

2. **Configure environment variables**
   Edit `.env` file with your settings:
   ```env
   # Bedrock Server Settings
   CONTAINER_NAME=minecraft-bedrock-server
   SERVER_HOST=192.168.86.149
   SSH_HOST=192.168.86.82
   SSH_USER=xtamtamx
   
   # Admin Panel Credentials
   ADMIN_USER=admin
   ADMIN_PASS=YourPassword
   ```

3. **Set up SSH key authentication**
   ```bash
   ./setup-ssh.sh
   ```

4. **Start the panel**
   ```bash
   docker-compose up -d
   ```

5. **Access the panel**
   Open http://localhost:41114 in your browser

## Panel Pages

### 📟 Console (Homepage)
- Live server console with command history
- Real-time output via WebSocket
- Quick action buttons for common commands:
  - 💾 **Save World** - Saves the game
  - 👥 **List Players** - Shows online players
  - ☀️ **Set Day** - Changes time to day
  - 🌙 **Set Night** - Changes time to night
  - 🌤️ **Clear Weather** - Stops rain/thunder
  - 🌧️ **Make it Rain** - Starts rain
- Command reference guide

### ⚙️ Server Settings
Edit server.properties including:
- **Server name** - Display name
- **World seed** - For world generation (requires restart)
- **Difficulty** - Peaceful, Easy, Normal, Hard
- **Game mode** - Survival, Creative, Adventure
- **Max players** - Connection limit
- **Allow cheats** - Enable/disable commands
- **Force gamemode** - Lock all players to server's gamemode
- **Player idle timeout** - Auto-kick idle players
- **View distance** - Chunk render distance
- **Tick distance** - Simulation distance

### 👥 Players
- View **online players** (auto-refreshing every 10 seconds)
- View **server operators** list
- **Grant/Remove OP** status
- **Kick players** with optional reason
- **Gamerules editor** with toggle buttons:
  - PVP on/off
  - Keep Inventory on death
  - Mob Griefing (creepers, endermen)
  - Fire Spread
  - Show Death Messages
  - Natural Health Regeneration

### 📋 Whitelist
- View all whitelisted players with their XUID
- Add players to whitelist
- Remove players from whitelist
- Enable/disable whitelist mode globally

## Console Commands

You can type any Bedrock server command in the console. Common commands include:
- `list` - Show online players
- `op [player]` - Give operator privileges
- `deop [player]` - Remove operator privileges
- `kick [player] [reason]` - Kick a player
- `whitelist add [player]` - Add player to whitelist
- `whitelist remove [player]` - Remove from whitelist
- `save-all` - Save the world
- `time set [value]` - Change time (day, night, 0-24000)
- `weather [type]` - Change weather (clear, rain, thunder)
- `gamerule [rule] [value]` - Modify game rules
- `difficulty [level]` - Change difficulty
- `gamemode [mode] [player]` - Change player's gamemode

## Stopping the Panel

```bash
docker-compose down
```

## Troubleshooting

If the panel shows "Container not running":
1. Verify your Bedrock server is running on the QNAP
2. Check the container name matches in `.env`
3. Ensure SSH authentication is working: `ssh -i ~/.ssh/minecraft_panel_rsa user@qnap-ip`
4. Check Docker logs: `docker logs minecraft-rcon-panel`

## Architecture

The panel uses SSH to connect to your QNAP and execute Docker commands to control the Minecraft server. Commands are sent using the Bedrock server's `send-command` utility.