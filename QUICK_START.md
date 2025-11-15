# <img src="Iron_Pickaxe_JE3_BE2.webp" width="24" height="24" alt="Pickaxe" /> Pickaxe RCON - Quick Start Guide

> "Mine your way to better server management!"

Get your Minecraft Bedrock Admin Panel running in under 5 minutes!

## Option 1: Docker Compose (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Minecraft Bedrock server running in Docker

### Steps

1. **Create a directory for the panel:**
```bash
mkdir minecraft-admin && cd minecraft-admin
```

2. **Download docker-compose.yml:**
```bash
curl -O https://raw.githubusercontent.com/xtamtamx/pickaxe-rcon/main/docker-compose.yml.example
mv docker-compose.yml.example docker-compose.yml
```

3. **Edit the configuration:**
```bash
nano docker-compose.yml
# Change ADMIN_PASS and SECRET_KEY
```

4. **Start the panel:**
```bash
docker-compose up -d
```

5. **Access the panel:**
Open `http://localhost:5000` in your browser

6. **Complete setup wizard:**
- Choose connection type (Local or SSH)
- Enter your Minecraft container name
- Set admin credentials

That's it! You're ready to manage your server.

---

## Option 2: Docker Run (One-liner)

### For Local Minecraft Server (Same Machine)

```bash
docker run -d \
  --name pickaxe-rcon \
  --restart unless-stopped \
  -p 5000:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=YourSecurePassword123 \
  -e SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  -v minecraft-admin-data:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  xtamtamx/pickaxe-rcon:latest
```

### For Remote Minecraft Server (SSH)

```bash
docker run -d \
  --name pickaxe-rcon \
  --restart unless-stopped \
  -p 5000:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=YourSecurePassword123 \
  -e SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  -v minecraft-admin-data:/app/data \
  -v ~/.ssh/minecraft_rsa:/root/.ssh/minecraft_panel_rsa:ro \
  xtamtamx/pickaxe-rcon:latest
```

---

## Option 3: Build from Source

```bash
# Clone repository
git clone https://github.com/xtamtamx/pickaxe-rcon.git
cd pickaxe-rcon

# Build image
docker build -t pickaxe-rcon:latest .

# Run container
docker run -d \
  --name pickaxe-rcon \
  -p 5000:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=YourPassword \
  -e SECRET_KEY=your-secret-key \
  -v ./data:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  pickaxe-rcon:latest
```

---

## Option 4: Portainer Deploy

If you use Portainer, you can deploy with one click:

1. Go to **Stacks** → **Add Stack**
2. Name it `minecraft-admin`
3. Paste this docker-compose.yml:

```yaml
version: '3.8'
services:
  admin-panel:
    image: xtamtamx/pickaxe-rcon:latest
    container_name: pickaxe-rcon
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - ADMIN_USER=admin
      - ADMIN_PASS=ChangeThisPassword
      - SECRET_KEY=ChangeThisSecretKey
    volumes:
      - admin-data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro

volumes:
  admin-data:
```

4. Click **Deploy the stack**

---

## First-Time Setup

After starting the container:

1. **Open your browser** to `http://YOUR_SERVER_IP:5000`

2. **Complete the setup wizard:**
   - **Connection Type:**
     - Choose "Local" if Minecraft runs on the same machine
     - Choose "SSH" if Minecraft runs on a different server

   - **Server Details:**
     - Container name (e.g., `minecraft-bedrock-server`)
     - Server host IP (e.g., `192.168.1.100`)
     - SSH host/user (if using SSH mode)

   - **Admin Credentials:**
     - Set your admin username and password

3. **Start managing!**
   - View live console
   - Manage players
   - Configure server settings
   - Create world backups

---

## Common Scenarios

### Scenario 1: Both Containers on Same Machine

```bash
docker run -d --name pickaxe-rcon \
  -p 5000:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=SecurePass123 \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -v minecraft-admin:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --network bridge \
  xtamtamx/pickaxe-rcon:latest
```

Then in setup wizard:
- Connection Type: **Local**
- Container Name: `minecraft-bedrock-server` (or whatever your container is named)

### Scenario 2: Minecraft on QNAP/Synology NAS

```bash
# On your local machine or NAS
docker run -d --name pickaxe-rcon \
  -p 41114:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=SecurePass123 \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -v minecraft-admin:/app/data \
  -v ~/.ssh/nas_key:/root/.ssh/minecraft_panel_rsa:ro \
  xtamtamx/pickaxe-rcon:latest
```

Then in setup wizard:
- Connection Type: **SSH**
- SSH Host: Your NAS IP (e.g., `192.168.1.100`)
- SSH User: Your NAS username
- Container Name: `minecraft-bedrock-server`

### Scenario 3: Behind Reverse Proxy (Production)

```yaml
version: '3.8'
services:
  minecraft-admin:
    image: xtamtamx/pickaxe-rcon:latest
    container_name: pickaxe-rcon
    restart: unless-stopped
    expose:
      - "5000"
    environment:
      - ADMIN_USER=admin
      - ADMIN_PASS=${ADMIN_PASS}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - admin-data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - proxy-network

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - proxy-network
    depends_on:
      - minecraft-admin

volumes:
  admin-data:

networks:
  proxy-network:
```

---

## Troubleshooting

### Can't access panel at http://localhost:5000

**Check if container is running:**
```bash
docker ps | grep pickaxe-rcon
```

**Check logs:**
```bash
docker logs pickaxe-rcon
```

**Check port binding:**
```bash
docker port pickaxe-rcon
```

### Panel can't connect to Minecraft server

**For local mode:**
- Ensure Docker socket is mounted
- Check Minecraft container name is correct
- Verify both containers are running

**For SSH mode:**
- Test SSH connection manually
- Check SSH key permissions (should be 600)
- Verify SSH host/user are correct

### Setup wizard not appearing

Delete the config file and restart:
```bash
docker exec pickaxe-rcon rm /app/data/server_config.json
docker restart pickaxe-rcon
```

---

## Next Steps

- 📖 Read the [Full Documentation](README.md)
- 🔒 Review [Security Best Practices](SECURITY.md)
- 🐛 [Report Issues](https://github.com/xtamtamx/pickaxe-rcon/issues)
- ⭐ Star the project if you find it useful!

---

## Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/xtamtamx/pickaxe-rcon/issues)
- **Discussions:** [Ask questions and share tips](https://github.com/xtamtamx/pickaxe-rcon/discussions)
- **Discord:** [Join our community](#) (optional)

---

**Enjoy managing your Minecraft Bedrock server!** 🎮
