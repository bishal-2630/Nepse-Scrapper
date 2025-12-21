# mobile_config.py
"""
Android mobile-specific configuration
"""

import os
import sys
from pathlib import Path

def is_android():
    """Check if running on Android/Termux"""
    return 'com.termux' in os.environ.get('PREFIX', '')

def get_android_storage_path():
    """Get Android shared storage path"""
    if is_android():
        # Termux shared storage
        storage = Path('/data/data/com.termux/files/home/storage/shared')
        if storage.exists():
            return storage / 'NEPSE-Server'
    
    # Fallback to project directory
    return Path(__file__).resolve().parent.parent

def optimize_for_mobile():
    """Apply mobile-specific optimizations"""
    optimizations = {
        'database_timeout': 30,
        'max_upload_size': 5242880,  # 5MB
        'staticfiles_compress': True,
        'disable_admin_actions': False,
        'reduce_log_verbosity': True,
        'cache_backend': 'locmem',
        'cache_size': 100,
    }
    
    if is_android():
        # Additional Android optimizations
        optimizations.update({
            'worker_threads': 1,
            'database_connections': 2,
            'disable_debug_toolbar': True,
            'minimize_memory_usage': True,
        })
    
    return optimizations

def get_public_url():
    """Try to detect ngrok/public URL"""
    try:
        import requests
        # Try to get ngrok tunnel info
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            if tunnels:
                return tunnels[0].get('public_url')
    except:
        pass
    
    return None

# Export configuration
ANDROID_MODE = is_android()
STORAGE_PATH = get_android_storage_path()
MOBILE_OPTIMIZATIONS = optimize_for_mobile()
PUBLIC_URL = get_public_url()