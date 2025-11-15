# How to Redeploy the Admin Panel

## Quick Instructions

Open your terminal and run these commands:

```bash
# Navigate to the project directory
cd /Volumes/Satechi/Code/Minecraft/minecraft-rcon-panel

# Stop the current container
docker compose down

# Rebuild with new changes
docker compose build

# Start the container
docker compose up -d

# Check if it's running
docker compose ps
```

## Access Your Panel

Once deployed, open your browser:
- **URL**: http://localhost:41114
- **Username**: admin
- **Password**: That'sCharlie's

## New Features Available

After redeploying, you'll see a new navigation menu with:

1. **📟 Console** - The original console page
2. **⚙️ Settings** - NEW! Server properties editor
   - Change world seed
   - Switch difficulty (Survival to Peaceful)
   - Edit gamemode, max players, etc.
3. **👥 Players** - NEW! Player & gamerule management
   - View online players
   - Kick players
   - Grant/remove OP
   - Toggle gamerules (PVP, keep inventory, etc.)
4. **📋 Whitelist** - NEW! Whitelist management
   - Add/remove players
   - Enable/disable whitelist

## Troubleshooting

### If you see errors about port already in use:
```bash
# Find and stop the old container
docker ps
docker stop minecraft-rcon-panel
docker rm minecraft-rcon-panel

# Then try again
docker compose up -d
```

### View logs to debug:
```bash
docker compose logs -f
```

### Completely restart:
```bash
docker compose down
docker compose up -d --build
```

## Need Help?

If you encounter any issues, share the error message and I'll help you fix it!
