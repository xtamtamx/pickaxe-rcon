# Minecraft Bedrock Admin Panel

A comprehensive web-based administration panel for Minecraft Bedrock Edition servers running in Docker containers. Built with Flask and designed for both local and remote server management.

## Features

- **Real-time Console** - Execute commands with live output via WebSocket
- **Player Management** - View online players, kick, OP/De-OP, teleport, and more
- **Server Control** - Start, stop, restart server with status monitoring
- **World Management** - Backup/restore worlds, create new worlds with custom seeds
- **Whitelist & Operators** - Full CRUD operations for whitelist and operator management
- **Server Configuration** - Edit server.properties and gamerules through the UI
- **Performance Monitoring** - Real-time server metrics and resource usage
- **Log Viewer** - Searchable, filterable server logs with auto-refresh
- **Task Scheduler** - Automated commands on intervals or cron schedules
- **Map Integration** - Optional integration with map visualization tools (uNmINeD, etc.)
- **Secure Authentication** - Login system with session management
- **Setup Wizard** - First-run configuration wizard for easy setup

## Requirements

- Docker (for running the admin panel)
- Minecraft Bedrock Server running in a Docker container
- SSH access to the server (for remote management)
- Python 3.11+ (if running without Docker)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/xtamtamx/minecraft-rcon-panel.git
cd minecraft-rcon-panel
```

### 2. Configuration

The panel uses a configuration wizard on first run. You can also set up environment variables:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run with Docker (Recommended)

```bash
docker build -t minecraft-rcon-panel:latest .
docker run -d \
  --name minecraft-rcon-panel \
  --restart unless-stopped \
  -e ADMIN_USER="admin" \
  -e ADMIN_PASS="your-secure-password" \
  -e SECRET_KEY="your-secret-key" \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./data:/app/data \
  -p 5000:5000 \
  minecraft-rcon-panel:latest
```

Access the panel at `http://localhost:5000`

### 4. First-Time Setup

1. Navigate to the admin panel URL
2. Complete the setup wizard:
   - Choose connection type (SSH for remote, Local for same machine)
   - Enter server connection details
   - Set admin credentials
3. Start managing your server!

## Configuration

### Connection Types

**SSH (Remote Server)**
- Connects to a Minecraft server running on a different machine
- Requires SSH access with key-based authentication
- Ideal for QNAP NAS, dedicated servers, or remote hosts

**Local (Same Machine)**
- Connects to a Minecraft server on the same host
- Requires Docker socket access
- Ideal for running admin panel alongside your server

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_USER` | Admin panel username | `admin` |
| `ADMIN_PASS` | Admin panel password | (required) |
| `SECRET_KEY` | Flask secret key for sessions | (required) |
| `CONTAINER_NAME` | Minecraft container name | (configured via UI) |
| `SERVER_HOST` | Minecraft server IP | (configured via UI) |
| `SSH_HOST` | SSH host for remote access | (configured via UI) |
| `SSH_USER` | SSH username | (configured via UI) |

### Generating a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Deployment Options

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

### Docker Compose

```yaml
version: '3'
services:
  admin-panel:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ADMIN_USER=admin
      - ADMIN_PASS=your-password
      - SECRET_KEY=your-secret-key
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/app/data
    restart: unless-stopped
```

### Remote Deployment (QNAP/NAS)

1. Copy `update-and-deploy.sh.example` to `update-and-deploy.sh`
2. Edit the script with your server details
3. Run `./update-and-deploy.sh`

## SSH Setup for Remote Management

1. Generate an SSH key pair:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/minecraft_panel_rsa
```

2. Copy the public key to your remote server:
```bash
ssh-copy-id -i ~/.ssh/minecraft_panel_rsa.pub user@your-server-ip
```

3. Mount the SSH key in the Docker container:
```bash
-v ~/.ssh/minecraft_panel_rsa:/root/.ssh/minecraft_panel_rsa:ro
```

## Map Integration

The panel supports integration with map visualization tools:

1. **uNmINeD** - Self-hosted web-based map renderer
2. **Chunkbase** - Online seed map viewer
3. **Custom** - Any other map solution with a web interface

Configure map settings in Connection Settings → Map Server Settings.

## Security Considerations

⚠️ **Important Security Notes:**

1. **Change Default Credentials** - Always change the default admin password
2. **Use Strong Passwords** - Use a password manager to generate secure passwords
3. **Secure Secret Key** - Generate a random secret key for Flask sessions
4. **HTTPS in Production** - Use a reverse proxy (nginx, Caddy) with SSL/TLS
5. **Firewall Rules** - Restrict access to the admin panel port (5000 or custom)
6. **SSH Keys** - Use key-based authentication, not passwords
7. **Keep Updated** - Regularly update the panel and dependencies

### Recommended Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name admin.yourserver.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Troubleshooting

### Container Can't Connect to Minecraft Server

- Verify Docker socket is mounted correctly
- Check SSH keys have correct permissions (600)
- Test SSH connection manually: `ssh -i /path/to/key user@host`

### Map Not Loading

- Ensure map server URL is configured in Connection Settings
- Check map server is running and accessible
- Verify firewall allows connections to map port

### Commands Not Executing

- Check server is running
- Verify container name matches your Minecraft container
- Review container logs: `docker logs minecraft-rcon-panel`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your chosen license here - e.g., MIT, GPL, etc.]

## Credits

Built with:
- Flask - Web framework
- Flask-SocketIO - WebSocket support
- Flask-Login - Authentication
- Docker - Containerization

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
