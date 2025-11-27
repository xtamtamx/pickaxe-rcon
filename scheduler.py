from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import os

# Common safe Minecraft commands for scheduled tasks
SAFE_COMMANDS = [
    'save-all', 'whitelist', 'op', 'deop', 'kick', 'ban', 'pardon',
    'give', 'tp', 'teleport', 'gamemode', 'gamerule', 'time',
    'weather', 'say', 'tell', 'tellraw', 'tag', 'effect', 'title',
    'kill', 'clear', 'difficulty', 'setworldspawn', 'spawnpoint',
    'xp', 'experience', 'enchant', 'scoreboard', 'team'
]

class TaskScheduler:
    def __init__(self, bedrock_client):
        self.scheduler = BackgroundScheduler()
        self.bedrock_client = bedrock_client
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.tasks_file = 'data/scheduled_tasks.json'
        self.tasks = self.load_tasks()

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
        """Validate that command is safe to execute"""
        cmd = command.strip()
        cmd_lower = cmd.lower()

        # Check for shell injection attempts
        dangerous_chars = [';', '|', '`', '$', '>', '<', '\\', '\n', '\r']
        for char in dangerous_chars:
            if char in cmd:
                print(f"[Scheduler] Blocked: command contains dangerous character '{char}'")
                return False

        # Check if command starts with any safe command
        for safe_cmd in SAFE_COMMANDS:
            if cmd_lower.startswith(safe_cmd.lower()):
                return True

        return False

    def _execute_task(self, task_id):
        """Execute a scheduled task"""
        task = self.tasks.get(task_id)
        if not task:
            return

        print(f"[Scheduler] Executing task: {task['name']}")

        # Execute the command(s)
        command = task['command']

        # Check for special @backup action
        if command.strip().lower() == '@backup':
            self._execute_backup(task)
            task['last_run'] = datetime.now().isoformat()
            self.save_tasks()
            return

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
