import subprocess
import os
import shlex
import re

# QNAP-specific Docker path (can be overridden via environment variable)
DOCKER_PATH = os.getenv('DOCKER_PATH', '/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker')

class BedrockRemoteClient:
    """Client for interacting with Minecraft Bedrock server on remote host via SSH"""

    def __init__(self, host='localhost', container_name=None, ssh_host=None, ssh_user=None):
        self.game_host = host  # Where the game is accessible
        self.ssh_host = ssh_host or os.getenv('SSH_HOST', 'localhost')  # Where to SSH to
        self.container_name = container_name or os.getenv('CONTAINER_NAME', 'minecraft-bedrock-server')
        self.ssh_user = ssh_user or os.getenv('SSH_USER', 'admin')  # Default QNAP user

    def _ssh_command(self, command, timeout=30):
        """Execute command on remote host via SSH"""
        ssh_key = os.path.expanduser('~/.ssh/minecraft_panel_rsa')
        ssh_cmd = [
            'ssh',
            '-i', ssh_key,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',
            f'{self.ssh_user}@{self.ssh_host}',
            command
        ]
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"SSH command timed out after {timeout}s: {command[:50]}...")
            return None
        except Exception as e:
            print(f"SSH command failed: {e}")
            return None
    
    def send_command(self, command):
        """Send a command to the Minecraft server console"""
        # QNAP has docker in /share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker
        # Bedrock server uses 'send-command' instead of 'mc-send-to-console'
        # Use shlex.quote to prevent command injection
        safe_command = shlex.quote(command)
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} send-command {safe_command}'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            return {
                'success': True,
                'response': result.stdout.strip()
            }
        else:
            error_msg = result.stderr if result else "SSH connection failed"
            return {
                'success': False,
                'response': f'Error: {error_msg}'
            }

    def send_command_with_output(self, command):
        """Send command and retrieve output from logs"""
        import time

        # Special handling for common commands that have specific output
        cmd_lower = command.lower().strip()

        # For 'list' command, use the dedicated method
        if cmd_lower == 'list':
            player_result = self.get_online_players()
            if player_result['success']:
                players = player_result['players']
                if players:
                    return {
                        'success': True,
                        'response': f"There are {len(players)}/20 players online:\n" + '\n'.join(players)
                    }
                else:
                    return {
                        'success': True,
                        'response': 'There are 0/20 players online'
                    }

        # For 'seed' command, get from server properties and try logs
        if cmd_lower == 'seed':
            # First send the command to the server
            self.send_command(command)
            time.sleep(0.7)

            # Try to get from logs
            docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker logs --tail 30 {self.container_name} 2>&1'
            result = self._ssh_command(docker_cmd)

            if result and result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in reversed(lines):
                    if 'Seed' in line:
                        if 'INFO]' in line:
                            parts = line.split('INFO]', 1)
                            if len(parts) > 1:
                                return {
                                    'success': True,
                                    'response': parts[1].strip()
                                }

            # Fallback: get seed from server.properties
            props_result = self.get_server_properties()
            if props_result['success']:
                seed = props_result['properties'].get('level-seed', 'Not set')
                return {
                    'success': True,
                    'response': f"Seed from server.properties: {seed}"
                }

        # For other commands, just send and confirm
        self.send_command(command)

        # Wait longer for output to appear
        time.sleep(0.7)

        # Get recent logs to try to capture any relevant output
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker logs --tail 30 {self.container_name} 2>&1'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            logs = result.stdout
            lines = logs.split('\n')

            # Look for seed output specifically
            if 'seed' in cmd_lower:
                # First try to find any line with "Seed" (capital S)
                for line in reversed(lines):
                    if 'Seed' in line:
                        # Try to extract just the seed info
                        if 'INFO]' in line:
                            parts = line.split('INFO]', 1)
                            if len(parts) > 1:
                                return {
                                    'success': True,
                                    'response': parts[1].strip()
                                }
                        else:
                            # If no INFO marker, just return the line
                            return {
                                'success': True,
                                'response': line.strip()
                            }

            # For time queries
            if 'time query' in cmd_lower:
                for line in reversed(lines):
                    if 'time is' in line.lower() and 'INFO]' in line:
                        parts = line.split('INFO]', 1)
                        if len(parts) > 1:
                            return {
                                'success': True,
                                'response': parts[1].strip()
                            }

            # For other commands, return a simple confirmation
            return {
                'success': True,
                'response': f'✓ Command "{command}" executed'
            }
        else:
            return {
                'success': False,
                'response': 'Command sent but could not verify execution'
            }
    
    def get_logs(self, lines=50):
        """Get recent server logs"""
        # Use 2>&1 to capture stderr (where startup/version info goes) along with stdout
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker logs --tail {lines} {self.container_name} 2>&1'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            return {'success': True, 'logs': result.stdout}
        else:
            return {'success': False, 'logs': 'Failed to retrieve logs'}

    def get_container_stats(self):
        """Get Docker container performance statistics"""
        # Get stats in JSON format (no-stream means get one reading and exit)
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker stats {self.container_name} --no-stream --format "{{{{json .}}}}"'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            import json
            try:
                stats = json.loads(result.stdout.strip())

                # Parse CPU percentage (remove %)
                cpu_percent = float(stats.get('CPUPerc', '0%').replace('%', ''))

                # Parse memory usage
                mem_usage = stats.get('MemUsage', '0B / 0B')
                mem_parts = mem_usage.split(' / ')
                mem_used = mem_parts[0] if len(mem_parts) > 0 else '0B'
                mem_limit = mem_parts[1] if len(mem_parts) > 1 else '0B'
                mem_percent = float(stats.get('MemPerc', '0%').replace('%', ''))

                # Network I/O
                net_io = stats.get('NetIO', '0B / 0B')

                # Block I/O (disk)
                block_io = stats.get('BlockIO', '0B / 0B')

                return {
                    'success': True,
                    'cpu_percent': cpu_percent,
                    'memory_used': mem_used,
                    'memory_limit': mem_limit,
                    'memory_percent': mem_percent,
                    'network_io': net_io,
                    'block_io': block_io,
                    'raw_stats': stats
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to parse stats: {str(e)}'
                }
        else:
            return {
                'success': False,
                'error': 'Failed to retrieve container stats'
            }

    def get_online_players(self):
        """Get list of online players by sending command and reading logs"""
        import time

        # Send the list command
        self.send_command('list')

        # Wait a moment for the output to appear in logs
        time.sleep(0.5)

        # Get recent logs
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker logs --tail 20 {self.container_name} 2>&1'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            logs = result.stdout
            players = []

            # Look for the player list in logs
            # Format: "There are X/Y players online:" followed by player names on separate lines
            lines = logs.split('\n')
            found_player_line = False

            for i, line in enumerate(lines):
                if 'players online:' in line.lower():
                    found_player_line = True
                    # Get the lines after this one until we hit an empty line or different log entry
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Stop if we hit a log timestamp or empty line
                        if not next_line or '[' in next_line or 'INFO' in next_line:
                            break
                        players.append(next_line)
                    break

            return {'success': True, 'players': players}
        else:
            return {'success': False, 'players': []}
    
    def is_running(self):
        """Check if the container is running"""
        # Use double braces to escape the format string for SSH
        docker_cmd = f"/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker ps --filter name={self.container_name} --format '{{{{.Status}}}}'"
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            output = result.stdout.strip()
            return 'Up' in output and len(output) > 0
        return False

    def get_server_properties(self):
        """Read server.properties file from container"""
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} cat /data/server.properties'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            properties = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
            return {'success': True, 'properties': properties}
        else:
            return {'success': False, 'error': 'Failed to read server.properties'}

    def update_server_properties(self, properties):
        """Update server.properties file in container"""
        import tempfile
        import os as os_module

        # First, read the current file to preserve comments and structure
        result = self.get_server_properties()
        if not result['success']:
            return result

        # Build the updated properties content
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} cat /data/server.properties'
        read_result = self._ssh_command(docker_cmd)

        if not read_result or read_result.returncode != 0:
            return {'success': False, 'error': 'Failed to read current properties'}

        # Update the properties
        lines = read_result.stdout.split('\n')
        updated_lines = []
        updated_keys = set()

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in properties:
                    updated_lines.append(f"{key}={properties[key]}")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        # Add any new properties that weren't in the file
        for key, value in properties.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}")

        # Write via base64 encoding to avoid shell escaping issues
        properties_content = '\n'.join(updated_lines)

        # Use base64 to safely transfer the content
        import base64
        encoded_content = base64.b64encode(properties_content.encode('utf-8')).decode('ascii')

        # Write using base64 decode - split into chunks if too long
        max_chunk = 50000  # Safe chunk size for command line
        if len(encoded_content) > max_chunk:
            # For very large files, write in chunks
            write_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "rm -f /data/server.properties.new"'
            self._ssh_command(write_cmd)

            for i in range(0, len(encoded_content), max_chunk):
                chunk = encoded_content[i:i+max_chunk]
                append_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "echo {chunk} >> /data/server.properties.new"'
                result = self._ssh_command(append_cmd)
                if not result or result.returncode != 0:
                    return {'success': False, 'error': 'Failed to write properties chunk'}

            # Decode and move
            decode_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "base64 -d /data/server.properties.new > /data/server.properties && rm /data/server.properties.new"'
            write_result = self._ssh_command(decode_cmd)
        else:
            # Single command for smaller files
            write_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "echo {encoded_content} | base64 -d > /data/server.properties"'
            write_result = self._ssh_command(write_cmd)

        if write_result and write_result.returncode == 0:
            return {'success': True, 'message': 'Server properties updated. Restart server for changes to take effect.'}
        else:
            error_msg = write_result.stderr if write_result else 'Unknown error'
            return {'success': False, 'error': f'Failed to write server.properties: {error_msg}'}

    def get_whitelist(self):
        """Read allowlist.json from container (Bedrock uses allowlist not whitelist)"""
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec {self.container_name} cat /data/allowlist.json'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            try:
                import json
                whitelist = json.loads(result.stdout)
                return {'success': True, 'whitelist': whitelist}
            except json.JSONDecodeError as e:
                return {'success': False, 'error': f'JSON decode error: {str(e)}'}
        else:
            # Check if file doesn't exist
            if result and 'No such file or directory' in result.stderr:
                # Create empty allowlist file
                import base64
                empty_whitelist = '[]'
                encoded = base64.b64encode(empty_whitelist.encode('utf-8')).decode('ascii')
                create_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec {self.container_name} sh -c "echo {encoded} | base64 -d > /data/allowlist.json"'
                create_result = self._ssh_command(create_cmd)

                if create_result and create_result.returncode == 0:
                    return {'success': True, 'whitelist': []}
                else:
                    return {'success': False, 'error': 'Could not create allowlist.json'}

            error_msg = result.stderr if result else 'SSH command failed'
            return {'success': False, 'error': f'Docker exec failed: {error_msg}'}

    def get_ops(self):
        """Read permissions.json from container"""
        docker_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec {self.container_name} cat /data/permissions.json'
        result = self._ssh_command(docker_cmd)

        if result and result.returncode == 0:
            try:
                import json
                ops = json.loads(result.stdout)
                return {'success': True, 'ops': ops}
            except json.JSONDecodeError as e:
                return {'success': False, 'error': f'JSON decode error: {str(e)}'}
        else:
            # Check if file doesn't exist
            if result and 'No such file or directory' in result.stderr:
                # Create empty permissions file
                import base64
                empty_permissions = '[]'
                encoded = base64.b64encode(empty_permissions.encode('utf-8')).decode('ascii')
                create_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec {self.container_name} sh -c "echo {encoded} | base64 -d > /data/permissions.json"'
                create_result = self._ssh_command(create_cmd)

                if create_result and create_result.returncode == 0:
                    return {'success': True, 'ops': []}
                else:
                    return {'success': False, 'error': 'Could not create permissions.json'}

            error_msg = result.stderr if result else 'SSH command failed'
            return {'success': False, 'error': f'Docker exec failed: {error_msg}'}

    def list_backups(self):
        """List all world backups"""
        # List all files in /data/backups directory (not just .tar.gz)
        list_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "ls -lt /data/backups/ 2>/dev/null | grep -v ^d || echo NO_BACKUPS"'
        result = self._ssh_command(list_cmd)

        if result and result.returncode == 0:
            backups = []
            for line in result.stdout.split('\n'):
                if line and not line.startswith('total') and 'NO_BACKUPS' not in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        # Extract filename, size, and date
                        filename = parts[-1]
                        size = parts[4]
                        date = ' '.join(parts[5:8])
                        backups.append({
                            'filename': filename,
                            'size': size,
                            'date': date
                        })
            return {'success': True, 'backups': backups}
        else:
            return {'success': False, 'error': 'Failed to list backups'}

    def create_backup(self, backup_name=None):
        """Create a backup of the current world"""
        from datetime import datetime

        if not backup_name:
            backup_name = f"world_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        else:
            # Ensure custom backup names have .tar.gz extension
            if not backup_name.endswith('.tar.gz'):
                backup_name = f"{backup_name}.tar.gz"

        # Get world name from server.properties
        props_result = self.get_server_properties()
        if not props_result['success']:
            return {'success': False, 'error': 'Failed to read world name'}

        world_name = props_result['properties'].get('level-name', 'Bedrock level')

        # Create backups directory if it doesn't exist
        mkdir_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} mkdir -p /data/backups'
        self._ssh_command(mkdir_cmd)

        # Create backup (tar the world folder)
        backup_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "cd /data/worlds && tar -czf /data/backups/{backup_name} \\"{world_name}\\""'
        result = self._ssh_command(backup_cmd)

        if result and result.returncode == 0:
            return {'success': True, 'message': f'Backup created: {backup_name}', 'filename': backup_name}
        else:
            error_msg = result.stderr if result else 'Unknown error'
            return {'success': False, 'error': f'Failed to create backup: {error_msg}'}

    def restore_backup(self, backup_filename):
        """Restore a world from backup"""
        # Validate filename to prevent path traversal
        if not re.match(r'^[\w\-\.]+\.tar\.gz$', backup_filename):
            return {'success': False, 'error': 'Invalid backup filename'}
        if '..' in backup_filename or '/' in backup_filename:
            return {'success': False, 'error': 'Invalid backup filename'}

        # Get world name from server.properties
        props_result = self.get_server_properties()
        if not props_result['success']:
            return {'success': False, 'error': 'Failed to read world name'}

        world_name = props_result['properties'].get('level-name', 'Bedrock level')

        # Remove current world
        remove_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "rm -rf /data/worlds/\\"{world_name}\\""'
        remove_result = self._ssh_command(remove_cmd)

        if not remove_result or remove_result.returncode != 0:
            return {'success': False, 'error': 'Failed to remove current world'}

        # Extract backup
        restore_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "cd /data/worlds && tar -xzf /data/backups/{backup_filename}"'
        result = self._ssh_command(restore_cmd)

        if result and result.returncode == 0:
            return {'success': True, 'message': f'World restored from {backup_filename}. Restart server to load.'}
        else:
            error_msg = result.stderr if result else 'Unknown error'
            return {'success': False, 'error': f'Failed to restore backup: {error_msg}'}

    def delete_backup(self, backup_filename):
        """Delete a backup file"""
        # Validate filename to prevent path traversal
        if not re.match(r'^[\w\-\.]+\.tar\.gz$', backup_filename):
            return {'success': False, 'error': 'Invalid backup filename'}
        if '..' in backup_filename or '/' in backup_filename:
            return {'success': False, 'error': 'Invalid backup filename'}

        delete_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} rm /data/backups/{backup_filename}'
        result = self._ssh_command(delete_cmd)

        if result and result.returncode == 0:
            return {'success': True, 'message': f'Backup {backup_filename} deleted'}
        else:
            return {'success': False, 'error': 'Failed to delete backup'}

    def create_new_world(self, world_seed=None, auto_restart=True):
        """Delete current world and create a new one with optional seed"""
        print(f"[create_new_world] Called with seed: {world_seed}, auto_restart: {auto_restart}", flush=True)

        # Get world name from server.properties
        props_result = self.get_server_properties()
        if not props_result['success']:
            return {'success': False, 'error': 'Failed to read world name'}

        world_name = props_result['properties'].get('level-name', 'Bedrock level')

        # If a seed is provided, update server.properties FIRST
        if world_seed:
            print(f"[create_new_world] Updating seed to: {world_seed}", flush=True)
            # Update the level-seed property
            update_result = self.update_server_properties({'level-seed': str(world_seed)})
            print(f"[create_new_world] Update result: {update_result}", flush=True)
            if not update_result['success']:
                return {'success': False, 'error': f'Failed to update seed in server.properties: {update_result.get("error", "Unknown error")}'}

        # Remove current world
        print(f"[create_new_world] Deleting world: {world_name}", flush=True)
        remove_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker exec -i {self.container_name} sh -c "rm -rf /data/worlds/\\"{world_name}\\""'
        result = self._ssh_command(remove_cmd)

        if result and result.returncode == 0:
            # If auto_restart is enabled, restart the server to generate new world
            if auto_restart:
                print(f"[create_new_world] Auto-restarting server...", flush=True)
                restart_result = self.restart_container()
                if restart_result['success']:
                    message = 'World deleted and server restarted! New world is generating...'
                    if world_seed:
                        message += f' With seed: {world_seed}'
                    return {'success': True, 'message': message}
                else:
                    message = 'World deleted but failed to restart server. Please restart manually.'
                    if world_seed:
                        message += f' Seed {world_seed} is set and ready.'
                    return {'success': False, 'error': message}
            else:
                message = 'Current world deleted. New world will generate on next server start.'
                if world_seed:
                    message += f' With seed: {world_seed}'
                return {'success': True, 'message': message}
        else:
            error_msg = result.stderr if result else 'Unknown error'
            return {'success': False, 'error': f'Failed to delete world: {error_msg}'}

    def restart_container(self):
        """Restart the Minecraft server container"""
        restart_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker restart {self.container_name}'
        result = self._ssh_command(restart_cmd, timeout=120)  # 2 min timeout for restart

        if result and result.returncode == 0:
            return {'success': True, 'message': 'Server container restarted successfully'}
        else:
            error_msg = result.stderr if result else 'Command timed out or SSH failed'
            return {'success': False, 'error': f'Failed to restart container: {error_msg}'}

    def stop_container(self):
        """Stop the Minecraft server container"""
        stop_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker stop {self.container_name}'
        result = self._ssh_command(stop_cmd, timeout=60)  # 1 min timeout for stop

        if result and result.returncode == 0:
            return {'success': True, 'message': 'Server container stopped successfully'}
        else:
            error_msg = result.stderr if result else 'Unknown error'
            return {'success': False, 'error': f'Failed to stop container: {error_msg}'}

    def start_container(self):
        """Start the Minecraft server container"""
        start_cmd = f'/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker start {self.container_name}'
        result = self._ssh_command(start_cmd, timeout=60)

        if result and result.returncode == 0:
            return {'success': True, 'message': 'Server container started successfully'}
        else:
            error_msg = result.stderr if result else 'Unknown error'
            return {'success': False, 'error': f'Failed to start container: {error_msg}'}

    def update_server(self):
        """Update the Minecraft Bedrock server by removing cached binary and restarting"""
        docker_path = '/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker'

        # Step 1: Get the data volume path from container
        inspect_cmd = f'{docker_path} inspect {self.container_name} --format "{{{{range .Mounts}}}}{{{{if eq .Destination \\"/data\\"}}}}{{{{.Source}}}}{{{{end}}}}{{{{end}}}}"'
        inspect_result = self._ssh_command(inspect_cmd, timeout=30)

        if not inspect_result or inspect_result.returncode != 0 or not inspect_result.stdout.strip():
            return {'success': False, 'error': 'Failed to find data volume path', 'step': 'inspect'}

        data_path = inspect_result.stdout.strip()

        # Step 2: Get current version before update
        version_cmd = f'{docker_path} logs --tail 100 {self.container_name} 2>&1 | grep -o "Version: [0-9.]*" | tail -1'
        version_result = self._ssh_command(version_cmd, timeout=15)
        old_version = version_result.stdout.strip() if version_result else 'Unknown'

        # Step 3: Stop the container
        stop_cmd = f'{docker_path} stop {self.container_name}'
        stop_result = self._ssh_command(stop_cmd, timeout=60)

        if not stop_result or stop_result.returncode != 0:
            return {'success': False, 'error': 'Failed to stop container', 'step': 'stop'}

        # Step 4: Remove the cached bedrock_server binary to force re-download
        rm_cmd = f'rm -f {data_path}/bedrock_server-*'
        rm_result = self._ssh_command(rm_cmd, timeout=30)

        # Step 5: Pull latest Docker image (in case there are container updates)
        pull_cmd = f'{docker_path} pull itzg/minecraft-bedrock-server:latest'
        self._ssh_command(pull_cmd, timeout=300)  # Best effort, continue even if fails

        # Step 6: Start the container (it will download the latest Bedrock server)
        start_cmd = f'{docker_path} start {self.container_name}'
        start_result = self._ssh_command(start_cmd, timeout=60)

        if not start_result or start_result.returncode != 0:
            return {'success': False, 'error': 'Failed to start container after update', 'step': 'start'}

        # Step 7: Wait for server to download and start, then get new version
        import time
        time.sleep(45)  # Give it time to download and start

        new_version_cmd = f'{docker_path} logs --tail 100 {self.container_name} 2>&1 | grep -o "Version: [0-9.]*" | tail -1'
        new_version_result = self._ssh_command(new_version_cmd, timeout=15)
        new_version = new_version_result.stdout.strip() if new_version_result else 'Unknown'

        if old_version != new_version and new_version != 'Unknown':
            return {'success': True, 'message': f'Updated from {old_version} to {new_version}', 'updated': True, 'old_version': old_version, 'new_version': new_version}
        elif new_version != 'Unknown':
            return {'success': True, 'message': f'Server restarted with {new_version} (was already latest)', 'updated': False, 'version': new_version}
        else:
            return {'success': True, 'message': 'Server restarted, check logs for version', 'updated': True}

    def get_server_version(self):
        """Get the current Minecraft Bedrock server version from logs"""
        docker_path = '/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker'
        # Look for version in recent logs
        logs_cmd = f'{docker_path} logs --tail 50 {self.container_name} 2>&1 | grep -i "Version"'
        result = self._ssh_command(logs_cmd, timeout=15)

        if result and result.returncode == 0 and result.stdout.strip():
            # Parse version from log line
            for line in result.stdout.split('\n'):
                if 'Version' in line:
                    return {'success': True, 'version': line.strip()}
        return {'success': False, 'version': 'Unknown'}

# For local testing without SSH (when running on same host)
class BedrockLocalClient:
    """Fallback client for local Docker access"""
    
    def __init__(self, container_name=None):
        self.container_name = container_name or os.getenv('CONTAINER_NAME', 'minecraft-bedrock-server')
    
    def send_command(self, command):
        """Send a command to the Minecraft server console"""
        try:
            docker_cmd = [
                'docker', 'exec', '-i', self.container_name,
                'mc-send-to-console', command
            ]
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                'success': result.returncode == 0,
                'response': result.stdout.strip() if result.stdout else result.stderr.strip()
            }
        except Exception as e:
            return {
                'success': False,
                'response': f'Error: {str(e)}'
            }
    
    def get_logs(self, lines=50):
        """Get recent server logs"""
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(lines), self.container_name],
                capture_output=True,
                text=True
            )
            return {
                'success': result.returncode == 0,
                'logs': result.stdout
            }
        except Exception as e:
            return {'success': False, 'logs': str(e)}
    
    def is_running(self):
        """Check if the container is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True
            )
            return 'Up' in result.stdout
        except:
            return False

    def get_server_properties(self):
        """Read server.properties file from container"""
        try:
            result = subprocess.run(
                ['docker', 'exec', '-i', self.container_name, 'cat', '/data/server.properties'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                properties = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
                return {'success': True, 'properties': properties}
            else:
                return {'success': False, 'error': 'Failed to read server.properties'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_server_properties(self, properties):
        """Update server.properties file in container"""
        try:
            # First, read the current file
            read_result = subprocess.run(
                ['docker', 'exec', '-i', self.container_name, 'cat', '/data/server.properties'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if read_result.returncode != 0:
                return {'success': False, 'error': 'Failed to read current properties'}

            # Update the properties
            lines = read_result.stdout.split('\n')
            updated_lines = []
            updated_keys = set()

            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in properties:
                        updated_lines.append(f"{key}={properties[key]}")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            # Add any new properties
            for key, value in properties.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}")

            # Write back to container
            properties_content = '\n'.join(updated_lines)
            write_result = subprocess.run(
                ['docker', 'exec', '-i', self.container_name, 'sh', '-c',
                 f'cat > /data/server.properties'],
                input=properties_content,
                capture_output=True,
                text=True,
                timeout=5
            )

            if write_result.returncode == 0:
                return {'success': True, 'message': 'Server properties updated. Restart server for changes to take effect.'}
            else:
                return {'success': False, 'error': f'Failed to write: {write_result.stderr}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_whitelist(self):
        """Read allowlist.json from container (Bedrock uses allowlist not whitelist)"""
        try:
            import json
            result = subprocess.run(
                ['docker', 'exec', '-i', self.container_name, 'cat', '/data/allowlist.json'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                try:
                    whitelist = json.loads(result.stdout)
                    return {'success': True, 'whitelist': whitelist}
                except json.JSONDecodeError:
                    return {'success': True, 'whitelist': []}
            else:
                return {'success': False, 'error': f'Failed to read whitelist: {result.stderr}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_ops(self):
        """Read permissions.json from container"""
        try:
            import json
            result = subprocess.run(
                ['docker', 'exec', '-i', self.container_name, 'cat', '/data/permissions.json'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                try:
                    ops = json.loads(result.stdout)
                    return {'success': True, 'ops': ops}
                except json.JSONDecodeError:
                    return {'success': True, 'ops': []}
            else:
                return {'success': False, 'error': f'Failed to read permissions: {result.stderr}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def restart_container(self):
        """Restart the Minecraft server container"""
        try:
            result = subprocess.run(
                ['docker', 'restart', self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return {'success': True, 'message': 'Server container restarted successfully'}
            else:
                return {'success': False, 'error': f'Failed to restart: {result.stderr}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop_container(self):
        """Stop the Minecraft server container"""
        try:
            result = subprocess.run(
                ['docker', 'stop', self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return {'success': True, 'message': 'Server container stopped successfully'}
            else:
                return {'success': False, 'error': f'Failed to stop: {result.stderr}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}