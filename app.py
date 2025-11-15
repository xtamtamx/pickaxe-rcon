from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_socketio import SocketIO, emit
from bedrock_simple import BedrockSimpleClient
from bedrock_remote import BedrockRemoteClient
from scheduler import TaskScheduler
from config import get_config
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import json
from threading import Thread
import time
from functools import wraps

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Load configuration
config = get_config()

# Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    admin_user = config.get('admin.username', 'admin')
    if user_id == admin_user:
        return User(user_id)
    return None

# Setup required decorator
def setup_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.is_setup_completed() and request.endpoint != 'setup' and not request.path.startswith('/static'):
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function

# Apply setup_required to all routes except setup
@app.before_request
def check_setup():
    if not config.is_setup_completed() and request.endpoint not in ['setup', 'static'] and not request.path.startswith('/static'):
        if request.endpoint != 'setup':
            return redirect(url_for('setup'))

# Initialize Bedrock client
def initialize_bedrock_client():
    """Initialize or reinitialize the Bedrock client with current config"""
    global bedrock_client, task_scheduler

    server_config = config.get_server_config()
    container_name = server_config.get('container_name', 'minecraft-bedrock')
    server_host = server_config.get('server_host', '192.168.86.149')

    ssh_key_path = os.path.expanduser('~/.ssh/minecraft_panel_rsa')
    if os.path.exists(ssh_key_path):
        print(f"SSH key found, using remote client for {server_host}")
        bedrock_client = BedrockRemoteClient(server_host, container_name)
    else:
        print("No SSH key found, using simple client (limited functionality)")
        bedrock_client = BedrockSimpleClient(server_host, container_name)

    return bedrock_client

# Initialize client
bedrock_client = initialize_bedrock_client()

# Initialize scheduler
task_scheduler = TaskScheduler(bedrock_client)
task_scheduler.start()

def execute_bedrock_command(command):
    """Execute Bedrock console command and return response"""
    # Use the new method that retrieves output from logs
    result = bedrock_client.send_command_with_output(command)
    print(f"Command: {command}, Result: {result}", flush=True)
    return result

def get_server_host():
    """Get current server host from config"""
    return config.get('server.server_host', '127.0.0.1')

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', rcon_host=get_server_host())

@app.route('/server-settings')
@login_required
def server_settings():
    return render_template('server-settings.html', rcon_host=get_server_host())

@app.route('/whitelist')
@login_required
def whitelist_page():
    return render_template('whitelist.html', rcon_host=get_server_host())

@app.route('/players')
@login_required
def players_page():
    return render_template('players.html', rcon_host=get_server_host())

@app.route('/worlds')
@login_required
def worlds_page():
    return render_template('worlds.html', rcon_host=get_server_host(), map_url=config.get('map.url', ''))

@app.route('/performance')
@login_required
def performance_page():
    return render_template('performance.html', rcon_host=get_server_host())

@app.route('/logs')
@login_required
def logs_page():
    return render_template('logs.html', rcon_host=get_server_host())

@app.route('/scheduler')
@login_required
def scheduler_page():
    return render_template('scheduler.html', rcon_host=get_server_host())

@app.route('/server-control')
@login_required
def server_control_page():
    return render_template('server-control.html', rcon_host=get_server_host())

@app.route('/connection-settings')
@login_required
def connection_settings():
    return render_template('connection-settings.html', config=config.config)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup flow for new installations"""
    if config.is_setup_completed():
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get form data
        server_config = {
            'connection_type': request.form.get('connection_type'),
            'ssh_host': request.form.get('ssh_host', ''),
            'ssh_user': request.form.get('ssh_user', ''),
            'container_name': request.form.get('container_name'),
            'server_host': request.form.get('server_host')
        }

        admin_config = {
            'username': request.form.get('admin_user'),
            'password': request.form.get('admin_pass')
        }

        # Validate passwords match
        password_confirm = request.form.get('admin_pass_confirm')
        if admin_config['password'] != password_confirm:
            return render_template('setup.html', error="Passwords do not match")

        # Save configuration
        if config.complete_setup(server_config, admin_config):
            # Reinitialize bedrock client with new config
            initialize_bedrock_client()
            return redirect(url_for('login'))
        else:
            return render_template('setup.html', error="Failed to save configuration")

    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_user = config.get('admin.username', 'admin')
        admin_pass = config.get('admin.password', 'admin')

        print(f"Login attempt for user: {username}")

        if username == admin_user and password == admin_pass:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/command', methods=['POST'])
@login_required
def send_command():
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'success': False, 'error': 'No command provided'})
    
    result = execute_bedrock_command(command)
    
    # Emit to websocket for live console
    socketio.emit('console_output', {
        'timestamp': datetime.now().isoformat(),
        'command': command,
        'response': result.get('response', result.get('error', '')),
        'success': result['success']
    })
    
    return jsonify(result)

@app.route('/api/test-console')
@login_required
def test_console():
    """Test Bedrock console connection"""
    server_config = config.get_server_config()
    result = {
        'container': server_config.get('container_name', 'unknown'),
        'host': server_config.get('server_host', 'unknown'),
        'tests': {}
    }
    
    # Test 1: Container running
    if bedrock_client.is_running():
        result['tests']['container_running'] = {'success': True, 'message': 'Container is running'}
        
        # Test 2: Send test command
        cmd_result = bedrock_client.send_command('help')
        result['tests']['console_command'] = {
            'success': cmd_result['success'], 
            'message': cmd_result['response'][:100] + '...' if len(cmd_result['response']) > 100 else cmd_result['response']
        }
        result['success'] = cmd_result['success']
    else:
        result['tests']['container_running'] = {'success': False, 'message': 'Container not running'}
        result['success'] = False
    
    return jsonify(result)

@app.route('/api/status')
@login_required
def server_status():
    """Get server status"""
    server_config = config.get_server_config()
    print(f"Checking server status - Container: {server_config.get('container_name', 'unknown')}")

    if not bedrock_client.is_running():
        return jsonify({
            'online': False,
            'error': 'Server container not running'
        })

    # Get online players using the log-based method
    player_result = bedrock_client.get_online_players()
    current_players = len(player_result.get('players', [])) if player_result['success'] else 0

    # Get max players from server properties
    props_result = bedrock_client.get_server_properties()
    max_players = 20  # Default
    if props_result['success']:
        max_players = int(props_result['properties'].get('max-players', 20))

    return jsonify({
        'online': True,
        'players': current_players,
        'max_players': max_players
    })

@app.route('/api/players')
@login_required
def get_players():
    """Get online players"""
    # Use the new method that reads from logs since Bedrock doesn't return command output
    result = bedrock_client.get_online_players()

    if result['success']:
        return jsonify({
            'success': True,
            'players': result['players']
        })

    return jsonify({'success': False, 'players': []})

@app.route('/api/stats')
@login_required
def get_stats():
    """Get server performance statistics"""
    result = bedrock_client.get_container_stats()
    return jsonify(result)

@app.route('/api/logs')
@login_required
def get_logs():
    """Get server logs with optional filtering"""
    lines = request.args.get('lines', 100, type=int)
    search = request.args.get('search', '', type=str)
    level = request.args.get('level', '', type=str)  # INFO, WARN, ERROR

    result = bedrock_client.get_logs(lines=min(lines, 1000))  # Cap at 1000 lines

    if result['success']:
        log_lines = result['logs'].split('\n')

        # Filter by search term
        if search:
            log_lines = [line for line in log_lines if search.lower() in line.lower()]

        # Filter by log level
        if level:
            log_lines = [line for line in log_lines if f'[{level}]' in line]

        return jsonify({
            'success': True,
            'logs': '\n'.join(log_lines),
            'line_count': len(log_lines)
        })

    return jsonify(result)

@app.route('/api/scheduler/tasks', methods=['GET'])
@login_required
def get_scheduled_tasks():
    """Get all scheduled tasks"""
    return jsonify({'success': True, 'tasks': task_scheduler.get_tasks()})

@app.route('/api/scheduler/task', methods=['POST'])
@login_required
def create_scheduled_task():
    """Create a new scheduled task"""
    data = request.get_json()
    name = data.get('name')
    command = data.get('command')
    schedule_type = data.get('schedule_type', 'interval')

    if not name or not command:
        return jsonify({'success': False, 'error': 'Name and command required'})

    kwargs = {}
    if schedule_type == 'interval':
        kwargs['interval_minutes'] = data.get('interval_minutes', 60)
    elif schedule_type == 'cron':
        kwargs['cron'] = data.get('cron', '0 * * * *')

    task_id = task_scheduler.add_task(name, command, schedule_type, **kwargs)
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/api/scheduler/task/<task_id>', methods=['DELETE'])
@login_required
def delete_scheduled_task(task_id):
    """Delete a scheduled task"""
    success = task_scheduler.remove_task(task_id)
    return jsonify({'success': success})

@app.route('/api/scheduler/task/<task_id>/toggle', methods=['POST'])
@login_required
def toggle_scheduled_task(task_id):
    """Enable or disable a task"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    success = task_scheduler.toggle_task(task_id, enabled)
    return jsonify({'success': success})

@app.route('/api/quick/<action>')
@login_required
def quick_action(action):
    """Quick actions"""
    commands = {
        'save': 'save-all',
        'whitelist_on': 'whitelist on',
        'whitelist_off': 'whitelist off',
        'weather_clear': 'weather clear',
        'weather_rain': 'weather rain',
        'time_day': 'time set day',
        'time_night': 'time set night'
    }

    if action in commands:
        result = execute_bedrock_command(commands[action])
        return jsonify(result)

    return jsonify({'success': False, 'error': 'Unknown action'})

@app.route('/api/server-properties')
@login_required
def get_server_properties():
    """Get server.properties file contents"""
    result = bedrock_client.get_server_properties()
    return jsonify(result)

@app.route('/api/server-properties', methods=['POST'])
@login_required
def update_server_properties():
    """Update server.properties file"""
    data = request.get_json()
    properties = data.get('properties', {})

    result = bedrock_client.update_server_properties(properties)
    return jsonify(result)

@app.route('/api/whitelist')
@login_required
def get_whitelist():
    """Get whitelist"""
    result = bedrock_client.get_whitelist()
    return jsonify(result)

@app.route('/api/whitelist/add', methods=['POST'])
@login_required
def add_to_whitelist():
    """Add player to whitelist"""
    data = request.get_json()
    player = data.get('player', '')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'whitelist add "{player}"')
    return jsonify(result)

@app.route('/api/whitelist/remove', methods=['POST'])
@login_required
def remove_from_whitelist():
    """Remove player from whitelist"""
    data = request.get_json()
    player = data.get('player', '')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'whitelist remove "{player}"')
    return jsonify(result)

@app.route('/api/ops')
@login_required
def get_ops():
    """Get operator list"""
    result = bedrock_client.get_ops()
    return jsonify(result)

@app.route('/api/player/kick', methods=['POST'])
@login_required
def kick_player():
    """Kick a player"""
    data = request.get_json()
    player = data.get('player', '')
    reason = data.get('reason', '')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    cmd = f'kick "{player}" {reason}' if reason else f'kick "{player}"'
    result = execute_bedrock_command(cmd)
    return jsonify(result)

@app.route('/api/player/op', methods=['POST'])
@login_required
def op_player():
    """Give operator status"""
    data = request.get_json()
    player = data.get('player', '')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'op "{player}"')
    return jsonify(result)

@app.route('/api/player/deop', methods=['POST'])
@login_required
def deop_player():
    """Remove operator status"""
    data = request.get_json()
    player = data.get('player', '')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'deop "{player}"')
    return jsonify(result)

@app.route('/api/player/teleport', methods=['POST'])
@login_required
def teleport_player():
    """Teleport player to coordinates"""
    data = request.get_json()
    player = data.get('player', '')
    x = data.get('x', 0)
    y = data.get('y', 0)
    z = data.get('z', 0)

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'tp "{player}" {x} {y} {z}')
    return jsonify(result)

@app.route('/api/player/give', methods=['POST'])
@login_required
def give_item():
    """Give item to player"""
    data = request.get_json()
    player = data.get('player', '')
    item = data.get('item', '')
    amount = data.get('amount', 1)

    if not player or not item:
        return jsonify({'success': False, 'error': 'Player and item required'})

    result = execute_bedrock_command(f'give "{player}" {item} {amount}')
    return jsonify(result)

@app.route('/api/player/gamemode', methods=['POST'])
@login_required
def change_gamemode():
    """Change player gamemode"""
    data = request.get_json()
    player = data.get('player', '')
    gamemode = data.get('gamemode', 'survival')

    if not player:
        return jsonify({'success': False, 'error': 'No player specified'})

    result = execute_bedrock_command(f'gamemode {gamemode} "{player}"')
    return jsonify(result)

@app.route('/api/player/effect', methods=['POST'])
@login_required
def give_effect():
    """Give effect to player"""
    data = request.get_json()
    player = data.get('player', '')
    effect = data.get('effect', '')
    duration = data.get('duration', 30)

    if not player or not effect:
        return jsonify({'success': False, 'error': 'Player and effect required'})

    result = execute_bedrock_command(f'effect "{player}" {effect} {duration}')
    return jsonify(result)

@app.route('/api/gamerules')
@login_required
def get_gamerules():
    """Get all gamerules"""
    result = execute_bedrock_command('gamerule')
    return jsonify(result)

@app.route('/api/gamerule/set', methods=['POST'])
@login_required
def set_gamerule():
    """Set a gamerule"""
    data = request.get_json()
    rule = data.get('rule', '')
    value = data.get('value', '')

    if not rule:
        return jsonify({'success': False, 'error': 'No rule specified'})

    result = execute_bedrock_command(f'gamerule {rule} {value}')
    return jsonify(result)

@app.route('/api/backups')
@login_required
def list_backups():
    """List all backups"""
    result = bedrock_client.list_backups()
    return jsonify(result)

@app.route('/api/backup/create', methods=['POST'])
@login_required
def create_backup():
    """Create a new backup"""
    data = request.get_json() or {}
    backup_name = data.get('name')

    result = bedrock_client.create_backup(backup_name)
    return jsonify(result)

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def restore_backup():
    """Restore from a backup"""
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': 'No filename specified'})

    result = bedrock_client.restore_backup(filename)
    return jsonify(result)

@app.route('/api/backup/delete', methods=['POST'])
@login_required
def delete_backup():
    """Delete a backup"""
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': 'No filename specified'})

    result = bedrock_client.delete_backup(filename)
    return jsonify(result)

@app.route('/api/world/new', methods=['POST'])
@login_required
def create_new_world():
    """Create a new world"""
    data = request.get_json() or {}
    seed = data.get('seed')

    result = bedrock_client.create_new_world(seed)
    return jsonify(result)

@app.route('/api/server/restart', methods=['POST'])
@login_required
def restart_server():
    """Restart the Minecraft server"""
    try:
        # First save the world
        execute_bedrock_command('save-all')

        # Restart the container
        result = bedrock_client.restart_container()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/server/stop', methods=['POST'])
@login_required
def stop_server():
    """Stop the Minecraft server"""
    try:
        # First save the world
        execute_bedrock_command('save-all')

        # Stop the container
        result = bedrock_client.stop_container()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/connection-settings', methods=['POST'])
@login_required
def update_connection_settings():
    """Update server connection settings"""
    try:
        server_config = {
            'connection_type': request.form.get('connection_type'),
            'ssh_host': request.form.get('ssh_host', ''),
            'ssh_user': request.form.get('ssh_user', ''),
            'container_name': request.form.get('container_name'),
            'server_host': request.form.get('server_host')
        }

        if config.update_server_config(server_config):
            # Reinitialize bedrock client with new config
            initialize_bedrock_client()
            return jsonify({'success': True, 'message': 'Connection settings updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin-credentials', methods=['POST'])
@login_required
def update_admin_credentials():
    """Update admin credentials"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        admin_user = request.form.get('admin_user')

        # Verify current password
        if current_password != config.get('admin.password'):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

        admin_config = {'username': admin_user}

        # Only update password if a new one was provided
        if new_password:
            if len(new_password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            admin_config['password'] = new_password

        if config.update_admin_config(admin_config):
            return jsonify({'success': True, 'message': 'Admin credentials updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/map-settings', methods=['POST'])
@login_required
def update_map_settings():
    """Update map server settings"""
    try:
        map_config = {
            'enabled': 'map_enabled' in request.form,
            'type': request.form.get('map_type', 'unmined'),
            'url': request.form.get('map_url', '')
        }

        # Update config
        current_config = config.config
        current_config['map'] = map_config
        config.config = current_config

        if config.save():
            flash('Map settings updated successfully', 'success')
        else:
            flash('Failed to save map configuration', 'error')

        return redirect(url_for('connection_settings'))
    except Exception as e:
        flash(f'Error updating map settings: {str(e)}', 'error')
        return redirect(url_for('connection_settings'))

@app.route('/api/test-connection')
@login_required
def test_connection_api():
    """Test the current server connection"""
    try:
        if bedrock_client.is_running():
            return jsonify({'success': True, 'message': 'Successfully connected to Minecraft server!'})
        else:
            return jsonify({'success': False, 'message': 'Container is not running or not accessible'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Connection failed: {str(e)}'})

@socketio.on('connect')
@login_required
def handle_connect():
    emit('connected', {'data': 'Connected to console'})

@socketio.on('send_command')
@login_required
def handle_command(data):
    command = data.get('command', '')
    if command:
        result = execute_bedrock_command(command)
        emit('console_output', {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'response': result.get('response', result.get('error', '')),
            'success': result['success']
        })

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)