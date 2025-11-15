# Deployment Guide - Minecraft Bedrock Admin Panel

## Quick Deployment to QNAP

### Method 1: Using the Redeploy Script (Recommended)

1. **SSH into your QNAP NAS:**
   ```bash
   ssh xtamtamx@192.168.86.82
   ```

2. **Navigate to project directory:**
   ```bash
   cd /path/to/minecraft-rcon-panel
   ```

3. **Run the redeploy script:**
   ```bash
   ./redeploy.sh
   ```

4. **Access the panel:**
   - URL: http://192.168.86.82:41114
   - Username: `admin`
   - Password: `That'sCharlie's`

### Method 2: Manual Docker Commands

```bash
# SSH into QNAP
ssh xtamtamx@192.168.86.82

# Navigate to project
cd /path/to/minecraft-rcon-panel

# Build image
docker build -t minecraft-rcon-panel:latest .

# Stop and remove old container
docker stop minecraft-rcon-panel 2>/dev/null || true
docker rm minecraft-rcon-panel 2>/dev/null || true

# Start new container
docker run -d \
  --name minecraft-rcon-panel \
  --restart unless-stopped \
  -e CONTAINER_NAME="minecraft-bedrock-server" \
  -e SERVER_HOST="192.168.86.149" \
  -e SSH_HOST="192.168.86.82" \
  -e SSH_USER="xtamtamx" \
  -e ADMIN_USER="admin" \
  -e ADMIN_PASS="That'sCharlie's" \
  -e SECRET_KEY="your-secret-key-change-this" \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ~/.ssh/minecraft_panel_rsa:/root/.ssh/minecraft_panel_rsa:ro \
  -v ~/.ssh/minecraft_panel_rsa.pub:/root/.ssh/minecraft_panel_rsa.pub:ro \
  -p 41114:5000 \
  minecraft-rcon-panel:latest
```

## Updating After Code Changes

1. **Copy files to QNAP** (from your Mac):
   ```bash
   # From your Mac in the project directory
   scp -r ./* xtamtamx@192.168.86.82:/path/to/minecraft-rcon-panel/
   ```

2. **Redeploy on QNAP:**
   ```bash
   ssh xtamtamx@192.168.86.82
   cd /path/to/minecraft-rcon-panel
   ./redeploy.sh
   ```

## Verifying Deployment

### Check Container Status
```bash
docker ps | grep minecraft-rcon-panel
```

### View Logs
```bash
docker logs -f minecraft-rcon-panel
```

### Test Connection
1. Visit: http://192.168.86.82:41114/api/debug-env
2. Should show environment variables (remove this endpoint in production!)

## Troubleshooting

### Login Issues
- Verify credentials in `.env` file
- Check logs: `docker logs minecraft-rcon-panel`
- Visit debug endpoint: http://192.168.86.82:41114/api/debug-env

### Server Connection Issues
- Verify Bedrock server is running: `docker ps | grep bedrock`
- Check SERVER_HOST is correct: `192.168.86.149`
- Verify container name matches: `minecraft-bedrock-server`
- Check SSH key exists: `ls ~/.ssh/minecraft_panel_rsa`

### Permission Issues
- Ensure Docker socket is accessible: `ls -la /var/run/docker.sock`
- Verify SSH key permissions: `chmod 600 ~/.ssh/minecraft_panel_rsa`

## Configuration Files

### .env File Location
`/path/to/minecraft-rcon-panel/.env`

### Important Settings
- `SERVER_HOST` - Where Bedrock server is accessible (192.168.86.149)
- `SSH_HOST` - Where to SSH for Docker commands (192.168.86.82)
- `CONTAINER_NAME` - Docker container name (minecraft-bedrock-server)
- `ADMIN_USER` / `ADMIN_PASS` - Panel login credentials

## Security Notes

1. **Remove Debug Endpoint** in production:
   - Edit `app.py` and remove the `/api/debug-env` route

2. **Change SECRET_KEY**:
   - Generate a secure random key
   - Update in `.env` file

3. **Firewall**:
   - Ensure port 41114 is only accessible from trusted networks
   - Consider using QNAP's reverse proxy with SSL

## Port Information

- **41114** - Admin panel web interface
- **19132** - Bedrock server game port (UDP)
- **22** - SSH for Docker commands

## Restart Server for Settings Changes

When you change server.properties (seed, difficulty, etc.), you must restart the Bedrock server:

```bash
# SSH into QNAP
ssh xtamtamx@192.168.86.82

# Restart Bedrock server container
docker restart minecraft-bedrock-server
```

Or use Container Station GUI to restart the Bedrock container.
