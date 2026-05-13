# Cloudflare Tunnel Setup Guide

This guide will help you expose both your Minecraft admin panel and the Minecraft server itself through Cloudflare Tunnel, allowing you to:
- Manage your server from anywhere at `https://admin.yourdomain.com`
- Play Minecraft remotely at `play.yourdomain.com:19132`

## Prerequisites

- Domain `yourdomain.com` configured in Cloudflare
- QNAP NAS with Minecraft server running at `your.server.ip:19132`
- Admin panel running at `localhost:41114` on QNAP

---

## Step 1: Install cloudflared on QNAP

SSH into your QNAP:
```bash
ssh xtamtamx@192.168.86.82
```

Download and install cloudflared:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
cloudflared --version
```

---

## Step 2: Authenticate with Cloudflare

Login to Cloudflare (this will open a browser):
```bash
cloudflared tunnel login
```

This creates a certificate at `~/.cloudflared/cert.pem`

---

## Step 3: Create the Tunnel

Create a named tunnel:
```bash
cloudflared tunnel create pickaxe-rcon
```

This will output:
- Tunnel ID (save this!)
- Credentials file location (e.g., `~/.cloudflared/<UUID>.json`)

Example output:
```
Tunnel credentials written to /root/.cloudflared/abc123-def456-ghi789.json
Created tunnel pickaxe-rcon with id abc123-def456-ghi789
```

---

## Step 4: Create Configuration File

Create the config directory:
```bash
mkdir -p ~/.cloudflared
```

Edit the config file:
```bash
nano ~/.cloudflared/config.yml
```

Paste this content (replace `<TUNNEL-ID>` with your actual tunnel ID from Step 3):
```yaml
tunnel: <TUNNEL-ID>
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json

ingress:
  # Admin Panel - Web interface
  - hostname: admin.yourdomain.com
    service: http://localhost:41114

  # Minecraft Bedrock Server - Game server
  - hostname: play.yourdomain.com
    service: tcp://your.server.ip:19132

  # Catch-all
  - service: http_status:404
```

---

## Step 5: Route DNS Records

Create DNS records pointing to your tunnel:
```bash
cloudflared tunnel route dns pickaxe-rcon admin.yourdomain.com
cloudflared tunnel route dns pickaxe-rcon play.yourdomain.com
```

This automatically creates CNAME records in Cloudflare DNS.

---

## Step 6: Test the Tunnel

Start the tunnel manually to test:
```bash
cloudflared tunnel run pickaxe-rcon
```

You should see:
```
Connection registered for admin.yourdomain.com
Connection registered for play.yourdomain.com
```

**Test the admin panel:**
- Open browser: `https://admin.yourdomain.com`
- You should see the login page (HTTPS is automatic!)

**Test Minecraft connection:**
- Open Minecraft Bedrock Edition
- Add server: `play.yourdomain.com` port `19132`
- Try to connect

Press `Ctrl+C` to stop the tunnel.

---

## Step 7: Install as a Service (Auto-start)

Install cloudflared as a system service:
```bash
sudo cloudflared service install
```

Enable and start the service:
```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Check status:
```bash
sudo systemctl status cloudflared
```

View logs:
```bash
sudo journalctl -u cloudflared -f
```

---

## Important Notes

### Minecraft Bedrock and TCP Tunnels

**IMPORTANT:** Minecraft Bedrock uses **UDP port 19132**, but Cloudflare Tunnel only supports TCP. This means:

1. **TCP tunneling will work** for the initial connection handshake
2. **Some features may not work perfectly** due to UDP limitations
3. **Alternative approach:** Use Cloudflare Spectrum (paid feature) for full UDP support

### Better Alternative for Minecraft Game Server

If you experience connection issues with the game server, consider these options:

**Option A: Use Cloudflare Spectrum (Paid)**
- Full UDP support
- Better for gaming
- Requires Cloudflare Pro plan ($20/month)

**Option B: Traditional Port Forwarding**
- Forward UDP port 19132 on your router to `your.server.ip:19132`
- Use dynamic DNS (like DuckDNS) if you don't have a static IP
- Free, but requires router configuration

**Option C: Keep Admin Panel on Cloudflare Tunnel, Port Forward Game**
- Use Cloudflare Tunnel for admin panel only (HTTPS works great)
- Port forward UDP 19132 for Minecraft server
- Best of both worlds!

---

## Recommended Setup

I recommend **Option C**:

### For Admin Panel (Keep Cloudflare Tunnel):
- `https://admin.yourdomain.com` → Pickaxe RCON panel
- Secure, HTTPS, works perfectly

### For Minecraft Server (Use Port Forwarding):
- Forward UDP port 19132 on your router
- Connect via: `your-home-ip:19132` or use DuckDNS for a friendly name
- Proper UDP support for gaming

### Updated config.yml (Admin panel only):
```yaml
tunnel: <TUNNEL-ID>
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json

ingress:
  # Admin Panel only
  - hostname: admin.yourdomain.com
    service: http://localhost:41114

  # Catch-all
  - service: http_status:404
```

Then just route the DNS:
```bash
cloudflared tunnel route dns pickaxe-rcon admin.yourdomain.com
```

---

## Troubleshooting

### Admin panel not accessible
```bash
# Check tunnel status
sudo systemctl status cloudflared

# Check logs
sudo journalctl -u cloudflared -f

# Verify admin panel is running
curl http://localhost:41114
```

### Minecraft connection fails
- Remember: TCP tunnel has limitations with Bedrock
- Check server is running: `docker ps | grep minecraft`
- Verify server IP: `your.server.ip:19132`
- Consider using port forwarding instead

### DNS not resolving
- Check Cloudflare DNS dashboard
- CNAME records should point to `<TUNNEL-ID>.cfargotunnel.com`
- Wait a few minutes for DNS propagation

---

## Required: Put Cloudflare Access in front of the panel

**Do not run this tunnel without Access.** The panel's login page is fully
exposed to the internet via the tunnel. Without Access, anyone on the internet
can hit `/login` and brute-force credentials (the rate limiter caps attempts
per IP, not globally — a botnet trivially defeats it). Access enforces
identity *before* a request ever reaches the Flask app.

Access is free for up to 50 users in Cloudflare Zero Trust.

### Step-by-step

1. Open https://one.dash.cloudflare.com → pick the account that owns the
   tunnel's domain. (First visit asks you to create a free Zero Trust team
   — pick a short slug; it appears in OAuth redirect URLs.)

2. **Settings → Authentication → Login methods → Add new**. Pick a provider:
   - **One-time PIN** (built-in; emails a code) — zero setup.
   - **Google** — most convenient if your panel logins are tied to a Gmail.

3. **Access → Applications → Add an application → Self-hosted**.
   - Application name: `pickaxe-rcon`
   - Session duration: `24 hours` (or shorter)
   - Application domain: `admin.yourdomain.com` (the tunnel's hostname)
   - Click **Next**.

4. Configure the policy:
   - Policy name: `Allow Tom`
   - Action: `Allow`
   - Configure rules → **Include → Emails** → enter your email address(es).
   - Click **Next**, then **Add application**.

5. Test from a logged-out browser (or incognito):
   - Visit `https://admin.yourdomain.com` — you should see the Cloudflare
     Access challenge (not the Pickaxe login).
   - Complete identity verification → you're now at the Pickaxe login.
   - Wrong identity → blocked at the Cloudflare layer, panel never sees the
     request.

6. **Headers (optional but recommended)** — Application → Settings → CORS
   off, **HTTP Only Cookie Attribute: on**, **Same Site Attribute: Strict**.

### What this changes for the panel

The panel still requires its own admin login on top of Access — that's
deliberate, two layers of auth. Access prevents drive-by traffic; the
panel's `flask-login` + bcrypt session is the second factor for an
authenticated Cloudflare identity.

### Bypass for service accounts (if you ever need one)

If you script the panel from another tool, you can add a **Service Token**
policy: `Access → Service Auth → Service Tokens → Create`. Send the
`CF-Access-Client-Id` and `CF-Access-Client-Secret` headers on requests.
Don't enable this until you actually need it.

## Operational notes

- **Monitor the logs** regularly: `sudo journalctl -u cloudflared -f` on
  the QNAP, plus the Access logs in Cloudflare Zero Trust → Logs.
- **Rotate the admin password** if you ever suspect compromise.
- **Keep the panel updated** — rebuild and redeploy after pulling from main.

---

## Useful Commands

```bash
# View tunnel info
cloudflared tunnel info pickaxe-rcon

# List all tunnels
cloudflared tunnel list

# View tunnel routes
cloudflared tunnel route dns

# Restart service
sudo systemctl restart cloudflared

# Stop service
sudo systemctl stop cloudflared

# View real-time logs
sudo journalctl -u cloudflared -f
```
