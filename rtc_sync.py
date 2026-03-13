import os
import subprocess
import logging
import time
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

def is_ntp_synced():
    try:
        result = subprocess.run(['chronyc', 'tracking'], capture_output=True, text=True, check=True)
        if 'Leap status     : Normal' in result.stdout:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking NTP status: {e}")
        return False

def main():
    logging.info("Starting rtc_sync...")
    
    if not is_ntp_synced():
        logging.info("NTP not synced. Skipping RTC update.")
        return

    rtc = get_rtc()
    rtc_time = rtc.read_time()
    system_time = int(time.time())

    drift = abs(system_time - rtc_time)
    logging.info(f"Drift detected: {drift} seconds")

    if drift < 30:
        logging.info("Drift is within acceptable range (< 30s). No update needed.")
        return

    if drift >= 120:
        logging.warning(f"Significant drift detected: {drift} seconds.")

    logging.info("Updating RTC with system time...")
    rtc.write_time(system_time)
    logging.info("RTC updated successfully.")

if __name__ == "__main__":
    main()
