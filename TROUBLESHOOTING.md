# Minecraft Bedrock Panel Troubleshooting Guide

## Common Issues and Solutions

### Panel shows "Container not running"

1. **Verify Bedrock server is running on QNAP**
   ```bash
   ssh user@qnap-ip
   docker ps | grep minecraft-bedrock-server
   ```

2. **Check container name in .env**
   Make sure `CONTAINER_NAME` matches your actual container name

3. **Test SSH connection**
   ```bash
   ssh -i ~/.ssh/minecraft_panel_rsa user@qnap-ip
   ```

### Commands not working

1. **Check Docker path on QNAP**
   The panel uses: `/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker`
   
2. **Verify send-command utility**
   Bedrock servers use `send-command` not `mc-send-to-console`

### SSH Authentication Issues

1. **Generate SSH key if missing**
   ```bash
   ./setup-ssh.sh
   ```

2. **Copy key to QNAP**
   ```bash
   ssh-copy-id -i ~/.ssh/minecraft_panel_rsa user@qnap-ip
   ```

3. **Test SSH access**
   ```bash
   ssh -i ~/.ssh/minecraft_panel_rsa user@qnap-ip "echo SSH works"
   ```

### Panel not accessible

1. **Check if container is running**
   ```bash
   docker ps | grep minecraft-rcon-panel
   ```

2. **View logs**
   ```bash
   docker logs minecraft-rcon-panel
   ```

3. **Verify port mapping**
   Panel should be accessible at http://localhost:41114

### Login issues

1. **Check credentials in .env**
   Default: admin / password from ADMIN_PASS

2. **Restart panel after .env changes**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Testing the Connection

Use the test endpoint to diagnose issues:
```bash
curl http://localhost:41114/api/test-console
```

This shows:
- Container running status
- SSH connection status
- Command execution test

## Docker Network Issues

If the panel can't reach the QNAP:
1. Check SSH_HOST in .env (should be QNAP's IP)
2. Ensure Docker container can reach external networks
3. Try using host network mode if needed

## Logs Location

- Panel logs: `docker logs minecraft-rcon-panel`
- Bedrock server logs: Available via "Get Logs" button in panel