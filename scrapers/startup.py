# scrapers/startup.py - Auto-start script for Termux
import os
import sys
import subprocess
import time
import signal
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/data/com.termux/files/home/nepse_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_if_running(process_name):
    """Check if a process is already running"""
    try:
        output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
        return process_name in output
    except:
        return False

def start_celery():
    """Start Celery worker and beat"""
    # Check if already running
    if check_if_running('celery'):
        logger.info("Celery is already running")
        return True
    
    # Start Celery worker
    celery_cmd = [
        'celery', '-A', 'nepse_scraper', 'worker',
        '--loglevel=info',
        '--concurrency=1',  # Single worker for mobile
        '--without-mingle',
        '--without-gossip',
        '--beat'  # Run beat scheduler in same process
    ]
    
    try:
        # Run in background
        process = subprocess.Popen(
            celery_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        logger.info(f"Started Celery with PID: {process.pid}")
        
        # Save PID to file for later management
        with open('/data/data/com.termux/files/home/celery.pid', 'w') as f:
            f.write(str(process.pid))
        
        # Wait a bit to see if it starts successfully
        time.sleep(5)
        
        # Check if still running
        if process.poll() is None:
            logger.info("✅ Celery started successfully")
            return True
        else:
            logger.error("❌ Celery failed to start")
            return False
            
    except Exception as e:
        logger.error(f"Error starting Celery: {e}")
        return False

def start_django():
    """Start Django server"""
    # Check if already running
    if check_if_running('runserver'):
        logger.info("Django is already running")
        return True
    
    # Start Django
    django_cmd = [
        'python', 'manage.py', 'runserver',
        '0.0.0.0:8000',
        '--noreload'  # No reload for mobile
    ]
    
    try:
        process = subprocess.Popen(
            django_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        logger.info(f"Started Django with PID: {process.pid}")
        
        # Save PID
        with open('/data/data/com.termux/files/home/django.pid', 'w') as f:
            f.write(str(process.pid))
        
        time.sleep(5)
        
        if process.poll() is None:
            logger.info("✅ Django started successfully")
            return True
        else:
            logger.error("❌ Django failed to start")
            return False
            
    except Exception as e:
        logger.error(f"Error starting Django: {e}")
        return False

def run_initial_scrape():
    """Run initial data scrape"""
    logger.info("Running initial data scrape...")
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'scrape_data'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Initial scrape successful")
            logger.info(result.stdout)
        else:
            logger.error("❌ Initial scrape failed")
            logger.error(result.stderr)
            
    except subprocess.TimeoutExpired:
        logger.error("Initial scrape timed out")
    except Exception as e:
        logger.error(f"Error during initial scrape: {e}")

def main():
    """Main startup function"""
    logger.info("=" * 50)
    logger.info(f"NEPSE Scraper Startup - {datetime.now()}")
    logger.info("=" * 50)
    
    # Change to project directory
    project_dir = '/data/data/com.termux/files/home/nepse_scraper'
    os.chdir(project_dir)
    
    # Activate virtual environment if exists
    venv_path = os.path.join(project_dir, 'venv')
    if os.path.exists(venv_path):
        activate_script = os.path.join(venv_path, 'bin', 'activate_this.py')
        if os.path.exists(activate_script):
            with open(activate_script) as f:
                exec(f.read(), {'__file__': activate_script})
            logger.info("Activated virtual environment")
    
    # Start services
    django_ok = start_django()
    celery_ok = start_celery()
    
    if django_ok and celery_ok:
        logger.info("✅ All services started successfully")
        
        # Run initial scrape after a delay
        time.sleep(10)
        run_initial_scrape()
        
        # Keep script running to monitor services
        try:
            while True:
                time.sleep(60)
                # Check if services are still running
                if not check_if_running('celery'):
                    logger.warning("Celery stopped, restarting...")
                    start_celery()
                
                if not check_if_running('runserver'):
                    logger.warning("Django stopped, restarting...")
                    start_django()
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            
    else:
        logger.error("Failed to start services")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())