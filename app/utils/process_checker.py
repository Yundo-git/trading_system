import psutil
import os

def is_live_trading_bot_running() -> bool:
    """Check if live_trading_bot.py is running as a separate process"""
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip the current process
            if proc.info['pid'] == current_pid:
                continue
                
            # Check if this is a Python process with live_trading_bot.py
            cmdline = proc.info.get('cmdline', [])
            if (len(cmdline) >= 2 and 
                'python' in cmdline[0].lower() and 
                'live_trading_bot.py' in ' '.join(cmdline[1:])):
                return True
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return False
