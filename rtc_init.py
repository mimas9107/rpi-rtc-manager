import os
import sys
import subprocess
import logging
import signal
from datetime import datetime
from ds1302 import get_rtc
from config import config

# Setup logging
os.makedirs(os.path.dirname(config['LOG_FILE']), exist_ok=True)
logging.basicConfig(
    filename=config['LOG_FILE'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global Timeout Handler (Safety first)
def timeout_handler(signum, frame):
    logging.error("RTC initialization timed out (5s limit). Exiting to avoid blocking boot.")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5) # Give it 5 seconds max (Spec target is < 50ms)

def set_system_time(epoch_sec):
    try:
        dt = datetime.fromtimestamp(epoch_sec)
        # Using -u to ensure UTC if specified, or default local
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        subprocess.run(['date', '-s', time_str], check=True, timeout=2)
        logging.info(f"System time set to: {time_str}")
        return True
    except subprocess.TimeoutExpired:
        logging.error("Subprocess 'date -s' timed out.")
        return False
    except Exception as e:
        logging.error(f"Failed to set system time: {e}")
        return False

def main():
    try:
        logging.info("Starting rtc_init...")
        rtc = get_rtc()
        rtc_time = rtc.read_time()
        
        if rtc_time == 0:
            logging.warning("RTC read failed or returned invalid time (0).")
            return

        dt = datetime.fromtimestamp(rtc_time)
        logging.info(f"RTC read: {dt.isoformat()}Z")

        # Validation: year >= 2022
        if dt.year < 2022:
            logging.warning(f"RTC time {dt.year} is invalid (before 2022). Ignoring.")
            return

        # Set system clock
        set_system_time(rtc_time)
        
    except Exception as e:
        logging.error(f"Unexpected error in rtc_init main: {e}")
    finally:
        signal.alarm(0) # Disable alarm

if __name__ == "__main__":
    main()
