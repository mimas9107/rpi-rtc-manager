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

# Global Timeout Handler
def timeout_handler(signum, frame):
    logging.error("RTC initialization timed out (5s limit). Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)

def set_system_time(epoch_sec):
    try:
        # Use '@timestamp' syntax to set system time directly from Unix Epoch
        # This is the most robust way as it avoids any timezone string parsing
        subprocess.run(['date', '-s', f'@{epoch_sec}'], check=True, timeout=2)
        
        # Log the local time for human readability
        dt_local = datetime.fromtimestamp(epoch_sec)
        logging.info(f"System time set to: {dt_local.strftime('%Y-%m-%d %H:%M:%S')} (from epoch @{epoch_sec})")
        return True
    except Exception as e:
        logging.error(f"Failed to set system time: {e}")
        return False

def main():
    try:
        logging.info("Starting rtc_init...")
        rtc = get_rtc()
        
        # Check for power loss (Clock Halt)
        if rtc.is_clock_halted():
            logging.error("RTC Battery Failure: Clock Halt (CH) bit detected. Time is invalid. Please check batteries.")
            return

        rtc_time = rtc.read_time()
        if rtc_time == 0:
            logging.warning("RTC read returned 0. Ignoring.")
            return

        dt = datetime.fromtimestamp(rtc_time)
        logging.info(f"RTC read successful: {dt.isoformat()}Z")

        if dt.year < 2022:
            logging.warning(f"RTC time {dt.year} is too old. Ignoring.")
            return

        set_system_time(rtc_time)
        
    except Exception as e:
        logging.error(f"Error in rtc_init: {e}")
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    main()
