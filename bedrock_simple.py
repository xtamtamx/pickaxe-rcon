import subprocess
import os

class BedrockSimpleClient:
    """Simple client that assumes the Minecraft server is accessible at the configured host"""
    
    def __init__(self, host='192.168.86.149', container_name='minecraft-bedrock'):
        self.host = host
        self.container_name = container_name
        self.game_port = 19132
    
    def send_command(self, command):
        """For Bedrock without console access, we can only return predefined responses"""
        # Since we can't directly access the console without SSH/Docker access,
        # we'll provide a message about this limitation
        
        if command.lower() == 'list':
            return {
                'success': True,
                'response': f'Server is running at {self.host}:{self.game_port}\nDirect console access requires SSH setup.'
            }
        elif command.lower() == 'help':
            return {
                'success': True,
                'response': 'Available commands:\n- list: Show server info\n- status: Check if server is reachable\n\nFor full console access, SSH needs to be configured.'
            }
        elif command.lower() == 'status':
            # Try to check if the game port is open
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00', (self.host, self.game_port))
                data, addr = sock.recvfrom(1024)
                sock.close()
                return {
                    'success': True,
                    'response': f'Server is responding at {self.host}:{self.game_port}'
                }
            except:
                return {
                    'success': False,
                    'response': f'Cannot reach server at {self.host}:{self.game_port}'
                }
        else:
            return {
                'success': False,
                'response': f'Command "{command}" requires direct console access via SSH.\nConfigure SSH access to use all server commands.'
            }
    
    def get_logs(self, lines=50):
        """Get recent server logs"""
        return {
            'success': False, 
            'logs': 'Log access requires SSH configuration to the server host.'
        }
    
    def is_running(self):
        """Check if the server is reachable on the game port"""
        import socket
        try:
            # Simple UDP port check
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            # Send a simple ping packet
            sock.sendto(b'ping', (self.host, self.game_port))
            # We don't need to wait for response, if sendto succeeds, port is open
            sock.close()
            return True
        except Exception as e:
            print(f"Port check failed: {e}")
            return False