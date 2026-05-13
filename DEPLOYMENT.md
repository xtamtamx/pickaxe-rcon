# Deployment Guide

## Quick Deployment to QNAP

### Method 1: Redeploy script (recommended)

```sh
ssh <user>@<qnap-host>
cd /share/Container/minecraft-rcon-panel
./redeploy.sh
```

Access at `http://<qnap-host>:41114` with the credentials configured in your
`.env`.

### Method 2: Manual docker run

```sh
# Build on a host with Docker Desktop (QNAP Container Station can't build),
# save, pipe to QNAP, load, and run.

docker build --platform linux/amd64 -t minecraft-rcon-panel:latest .

docker save minecraft-rcon-panel:latest \
  | ssh <user>@<qnap-host> 'docker load'

ssh <user>@<qnap-host> '
  docker rm -f minecraft-rcon-panel 2>/dev/null
  docker run -d \
    --name minecraft-rcon-panel \
    --restart unless-stopped \
    --env-file /share/Container/minecraft-rcon-panel/.env \
    -v ~/.ssh/minecraft_panel_rsa:/home/app/.ssh/minecraft_panel_rsa:ro \
    -v ~/.ssh/minecraft_panel_rsa.pub:/home/app/.ssh/minecraft_panel_rsa.pub:ro \
    -v /share/Container/minecraft-rcon-panel/data:/app/data \
    -p 41114:5000 \
    minecraft-rcon-panel:latest
'
```

The `.env` file (untracked) on the QNAP holds `ADMIN_USER`, `ADMIN_PASS`,
`SECRET_KEY`, `CONTAINER_NAME`, `SERVER_HOST`, `SSH_HOST`, `SSH_USER`. See
`.env.example` for the schema.

The container no longer mounts `/var/run/docker.sock` — all control happens via
SSH. The container runs as a non-root user (`app`); SSH keys are mounted into
`/home/app/.ssh/`, not `/root/.ssh/`.

## Updating after code changes

```sh
# Build locally, ship, redeploy
docker build --platform linux/amd64 -t minecraft-rcon-panel:latest .
docker save minecraft-rcon-panel:latest \
  | ssh <user>@<qnap-host> 'docker load'
ssh <user>@<qnap-host> 'docker restart minecraft-rcon-panel'
```

## Verify

```sh
ssh <user>@<qnap-host> 'docker ps | grep minecraft-rcon-panel'
ssh <user>@<qnap-host> 'docker logs -f minecraft-rcon-panel'
curl -sIo /dev/null -w "%{http_code}\n" http://<qnap-host>:41114/login
```

## Troubleshooting

- **Login fails** — verify `ADMIN_USER`/`ADMIN_PASS` in `.env`; on first run the
  config wizard at `/setup` lets you set them via UI.
- **"Server unreachable"** — confirm `SERVER_HOST` and `CONTAINER_NAME` match
  the bedrock server's actual host and container name; `ssh <SSH_USER>@<SSH_HOST>
  docker ps` should list it.
- **SSH key permission errors** — `chmod 600 ~/.ssh/minecraft_panel_rsa` on the
  QNAP; inside the container the key must be readable by the `app` user.

## Security

- `SECRET_KEY` is auto-generated on first run and stored in
  `data/server_config.json`. If you must override via `.env`, generate with
  `python -c "import secrets; print(secrets.token_hex(32))"`.
- The panel is intended to sit behind a reverse proxy (nginx or Cloudflare
  Tunnel + Zero Trust Access). Do not expose port 41114 to the internet
  directly.
- Brute-force protection: `Flask-Limiter` caps login attempts to 5/min per IP.

## Ports

| Port  | Use                                  |
| ----- | ------------------------------------ |
| 41114 | Admin panel HTTP                     |
| 19132 | Bedrock game port (UDP)              |
| 22    | SSH (the panel SSHs into the host)   |

## Restart server after config changes

Edits to `server.properties` (seed, difficulty, etc.) need a bedrock-server
restart to take effect:

```sh
ssh <user>@<qnap-host> 'docker restart minecraft-bedrock-server'
```
