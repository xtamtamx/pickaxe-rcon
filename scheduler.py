from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import json
import os
import re

# Allowlist of bedrock console commands that may appear as the first token of a
# scheduled task. The check below is a whole-word match (not startswith), so
# `op` does not also accept `option`, and `tag` does not also accept `tagged`.
SAFE_COMMANDS = frozenset({
    'save-all', 'whitelist', 'op', 'deop', 'kick', 'ban', 'pardon',
    'give', 'tp', 'teleport', 'gamemode', 'gamerule', 'time',
    'weather', 'say', 'tell', 'tellraw', 'tag', 'effect', 'title',
    'kill', 'clear', 'difficulty', 'setworldspawn', 'spawnpoint',
    'xp', 'experience', 'enchant', 'scoreboard', 'team',
})

# Bedrock selectors use `[`, `]`, `!`, `=`, `,`, `@`, and tellraw uses `{}"`.
# The shell layer is already protected by shlex.quote in BedrockRemoteClient
# (bedrock_remote.py:109), so the scheduler only needs to reject newlines
# (which would corrupt the FIFO write) and enforce the command allowlist.
_FIRST_TOKEN = re.compile(r'^(\S+)')

# Player target selectors: @a (all players), @p (nearest), @r (random).
# A scheduled command using one of these does nothing useful when the server
# is empty — running it just spams "No targets matched selector" in the log.
_PLAYER_SELECTOR = re.compile(r'@[apr](?![a-z])')

class TaskScheduler:
    def __init__(self, bedrock_client):
        # Single worker so the bedrock send-command FIFO is hit serially.
        # The bedrock client also holds its own SSH lock for cross-process
        # serialization with request handlers, but limiting the executor
        # avoids piling up jobs behind the lock.
        self.scheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(1)}
        )
        self.bedrock_client = bedrock_client
        os.makedirs('data', exist_ok=True)
        self.tasks_file = 'data/scheduled_tasks.json'
        self.tasks = self.load_tasks()

    def set_bedrock_client(self, bedrock_client):
        """Swap the bedrock client (e.g. after connection settings change)."""
        self.bedrock_client = bedrock_client

    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        # Reload existing tasks
        for task_id, task in self.tasks.items():
            if task.get('enabled', True):
                self._schedule_task(task_id, task)

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()

    def load_tasks(self):
        """Load tasks from JSON file"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Scheduler] Error loading tasks: {e}")
                return {}
        return {}

    def save_tasks(self):
        """Save tasks to JSON file"""
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def _is_safe_command(self, command):
        """Whole-word allowlist check on the first token; reject newlines."""
        cmd = command.strip()
        if not cmd or '\n' in cmd or '\r' in cmd:
            return False
        m = _FIRST_TOKEN.match(cmd)
        if not m:
            return False
        return m.group(1).lower() in SAFE_COMMANDS

    def _players_online(self):
        """Best-effort online-player check.

        On any error / indeterminate result, returns True so a transient SSH
        failure never silently drops a legitimate task.
        """
        try:
            result = self.bedrock_client.get_online_players()
        except Exception as e:
            print(f"[Scheduler] player check failed ({e}); assuming players online")
            return True
        if not result or not result.get('success'):
            return True
        return bool(result.get('players'))

    def _execute_task(self, task_id):
        """Execute a scheduled task"""
        task = self.tasks.get(task_id)
        if not task:
            return

        command = task['command']

        # Check for special @backup action
        if command.strip().lower() == '@backup':
            print(f"[Scheduler] Executing task: {task['name']}")
            self._execute_backup(task)
            task['last_run'] = datetime.now().isoformat()
            self.save_tasks()
            return

        # A command that targets players (@a/@p/@r — e.g. the Welcome Kit's
        # `give @a[tag=!welcomed] ...`) does nothing on an empty server and
        # just spams "No targets matched selector". Skip it when nobody's on.
        if _PLAYER_SELECTOR.search(command) and not self._players_online():
            print(f"[Scheduler] Skipping '{task['name']}': no players online")
            return

        print(f"[Scheduler] Executing task: {task['name']}")

        # Support multiple commands separated by ' && '
        if ' && ' in command:
            commands = command.split(' && ')
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    if self._is_safe_command(cmd):
                        self.bedrock_client.send_command(cmd)
                    else:
                        print(f"[Scheduler] Warning: Skipped potentially unsafe command: {cmd}")
        else:
            if self._is_safe_command(command):
                self.bedrock_client.send_command(command)
            else:
                print(f"[Scheduler] Warning: Skipped potentially unsafe command: {command}")

    def _execute_backup(self, task):
        """Create an automatic backup"""
        try:
            # Generate backup name with timestamp
            backup_name = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            print(f"[Scheduler] Creating automatic backup: {backup_name}")

            # Save world first
            self.bedrock_client.send_command('save-all')

            # Wait a moment for save to complete
            import time
            time.sleep(2)

            # Create the backup
            result = self.bedrock_client.create_backup(backup_name)

            if result.get('success'):
                print(f"[Scheduler] Backup created successfully: {result.get('message', backup_name)}")
            else:
                print(f"[Scheduler] Backup failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"[Scheduler] Error creating backup: {e}")

        # Update last run
        task['last_run'] = datetime.now().isoformat()
        self.save_tasks()

    def _schedule_task(self, task_id, task):
        """Schedule a task with APScheduler"""
        schedule_type = task.get('schedule_type', 'interval')

        try:
            if schedule_type == 'interval':
                # Interval-based (every X minutes/hours)
                minutes = task.get('interval_minutes', 60)
                self.scheduler.add_job(
                    self._execute_task,
                    trigger=IntervalTrigger(minutes=minutes),
                    args=[task_id],
                    id=task_id,
                    replace_existing=True
                )

            elif schedule_type == 'cron':
                # Cron-based (specific times)
                cron_str = task.get('cron', '0 * * * *')  # Default: every hour
                parts = cron_str.split()

                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    self.scheduler.add_job(
                        self._execute_task,
                        trigger=CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=day_of_week
                        ),
                        args=[task_id],
                        id=task_id,
                        replace_existing=True
                    )

            print(f"[Scheduler] Scheduled task: {task['name']}")
        except Exception as e:
            print(f"[Scheduler] Error scheduling task {task_id}: {e}")

    def add_task(self, name, command, schedule_type, **kwargs):
        """Add a new scheduled task"""
        task_id = f"task_{int(datetime.now().timestamp())}"

        task = {
            'name': name,
            'command': command,
            'schedule_type': schedule_type,
            'enabled': True,
            'created': datetime.now().isoformat(),
            'last_run': None
        }

        if schedule_type == 'interval':
            task['interval_minutes'] = kwargs.get('interval_minutes', 60)
        elif schedule_type == 'cron':
            task['cron'] = kwargs.get('cron', '0 * * * *')

        self.tasks[task_id] = task
        self.save_tasks()
        self._schedule_task(task_id, task)

        return task_id

    def remove_task(self, task_id):
        """Remove a scheduled task"""
        if task_id in self.tasks:
            # Remove from scheduler
            try:
                self.scheduler.remove_job(task_id)
            except Exception as e:
                print(f"[Scheduler] Error removing job {task_id}: {e}")

            # Remove from tasks dict
            del self.tasks[task_id]
            self.save_tasks()
            return True
        return False

    def toggle_task(self, task_id, enabled):
        """Enable or disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id]['enabled'] = enabled
            self.save_tasks()

            if enabled:
                self._schedule_task(task_id, self.tasks[task_id])
            else:
                try:
                    self.scheduler.remove_job(task_id)
                except Exception as e:
                    print(f"[Scheduler] Error removing job {task_id}: {e}")
            return True
        return False

    def get_tasks(self):
        """Get all tasks"""
        return self.tasks

    def get_task(self, task_id):
        """Get a specific task"""
        return self.tasks.get(task_id)
