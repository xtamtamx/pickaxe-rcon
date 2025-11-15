# <img src="Iron_Pickaxe_JE3_BE2.webp" width="32" height="32" alt="Pickaxe" /> Pickaxe RCON

> Mine deep into your Minecraft Bedrock server management - A powerful, user-friendly web-based admin panel

[![Docker Pulls](https://img.shields.io/docker/pulls/xtamtamx/pickaxe-rcon)](https://hub.docker.com/r/xtamtamx/pickaxe-rcon)
[![GitHub Stars](https://img.shields.io/github/stars/xtamtamx/pickaxe-rcon)](https://github.com/xtamtamx/pickaxe-rcon/stargazers)
[![License](https://img.shields.io/github/license/xtamtamx/pickaxe-rcon)](LICENSE)

![Screenshot](https://via.placeholder.com/800x400?text=Admin+Panel+Screenshot)

## ✨ Features

- 🎮 **Real-time Console** - Execute commands with live WebSocket output
- 👥 **Player Management** - View, kick, OP, teleport, give items, and more
- ⚙️ **Server Configuration** - Edit server.properties and gamerules in the UI
- 💾 **World Management** - Backup, restore, and create new worlds with custom seeds
- 📋 **Whitelist & Operators** - Full CRUD operations for access control
- 📊 **Performance Monitoring** - Real-time server metrics and resource usage
- 📜 **Log Viewer** - Searchable, filterable logs with auto-refresh
- ⏰ **Task Scheduler** - Automate commands with intervals or cron schedules
- 🗺️ **Map Integration** - Optional integration with uNmINeD and other map tools
- 🔒 **Secure** - Login system, session management, and security best practices
- 🚀 **Easy Setup** - First-run wizard, Docker support, works locally or remotely

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
docker run -d \
  --name pickaxe-rcon \
  -p 5000:5000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=YourSecurePassword \
  -e SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  -v pickaxe-data:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  xtamtamx/pickaxe-rcon:latest
```

Then open `http://localhost:5000` and complete the setup wizard!

### Using Docker Compose

```bash
# Download example compose file
curl -O https://raw.githubusercontent.com/xtamtamx/pickaxe-rcon/main/docker-compose.yml.example
mv docker-compose.yml.example docker-compose.yml

# Edit configuration
nano docker-compose.yml

# Start
docker-compose up -d
```

📖 **[Full Quick Start Guide](QUICK_START.md)**

## 📸 Screenshots

<details>
<summary>Click to expand</summary>

### Live Console
![Console](https://via.placeholder.com/600x300?text=Console+Screenshot)

### Player Management
![Players](https://via.placeholder.com/600x300?text=Player+Management)

### Server Settings
![Settings](https://via.placeholder.com/600x300?text=Server+Settings)

### World Backups
![Backups](https://via.placeholder.com/600x300?text=World+Backups)

</details>

## 🎯 Use Cases

### Home Server
Perfect for managing your home Minecraft server from a web interface

### QNAP/Synology NAS
Remotely manage Minecraft servers running on NAS devices via SSH

### Multiple Servers
Manage several Minecraft instances from one central panel

### Shared Hosting
Give server admins a friendly UI without SSH access

## 📋 Requirements

- Docker (for running the panel)
- Minecraft Bedrock Server in a Docker container
- SSH access (for remote servers)
- Modern web browser

## 🔧 Configuration

The panel supports two connection modes:

### Local Mode
For Minecraft servers on the same machine as the admin panel. Requires Docker socket access.

### SSH Mode
For Minecraft servers on remote machines (QNAP, Synology, dedicated servers). Requires SSH key authentication.

All configuration is done through the web UI - no manual file editing required!

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get running in 5 minutes
- **[Full Documentation](README_DISTRIBUTION.md)** - Complete setup and configuration
- **[Security Guide](SECURITY.md)** - Best practices and security checklist

## 🛠️ Development

### Run from Source

```bash
git clone https://github.com/xtamtamx/pickaxe-rcon.git
cd pickaxe-rcon

cp .env.example .env
# Edit .env with your settings

pip install -r requirements.txt
python app.py
```

### Build Docker Image

```bash
docker build -t pickaxe-rcon:latest .
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Issues & Support

- **[Report a Bug](https://github.com/xtamtamx/pickaxe-rcon/issues/new?template=bug_report.md)**
- **[Request a Feature](https://github.com/xtamtamx/pickaxe-rcon/issues/new?template=feature_request.md)**
- **[Ask a Question](https://github.com/xtamtamx/pickaxe-rcon/discussions)**

## 🔒 Security

Please review our **[Security Policy](SECURITY.md)** before deploying to production.

To report a security vulnerability, please email [your-email@example.com] instead of opening a public issue.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Star History

If you find this project useful, please consider giving it a star! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=xtamtamx/pickaxe-rcon&type=Date)](https://star-history.com/#xtamtamx/pickaxe-rcon&Date)

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- WebSocket support via [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- Authentication via [Flask-Login](https://flask-login.readthedocs.io/)
- Inspired by the Minecraft community

## 📞 Connect

- **GitHub:** [@xtamtamx](https://github.com/xtamtamx)
- **Discord:** [Join our community](#) (optional)
- **Twitter:** [@yourhandle](https://twitter.com/yourhandle) (optional)

---

Made with ❤️ for the Minecraft Bedrock community
