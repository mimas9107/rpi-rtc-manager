from ds1302 import get_rtc
from datetime import datetime
import time

def test_rtc():
    rtc = get_rtc()
    
    print("--- Phase 2: RTC Read Test ---")
    rtc_time = rtc.read_time()
    if rtc_time == 0:
        print("RTC read failed or invalid.")
    else:
        dt = datetime.fromtimestamp(rtc_time)
        print(f"RTC Current Time: {dt.isoformat()}Z (Epoch: {rtc_time})")

    print("\n--- Phase 3: RTC Write Test ---")
    current_time = int(time.time())
    print(f"Writing current system time to RTC: {datetime.fromtimestamp(current_time).isoformat()}Z")
    rtc.write_time(current_time)
    
    time.sleep(1)
    
    new_rtc_time = rtc.read_time()
    dt_new = datetime.fromtimestamp(new_rtc_time)
    print(f"RTC New Time: {dt_new.isoformat()}Z (Epoch: {new_rtc_time})")
    
    drift = abs(new_rtc_time - (current_time + 1))
    if drift <= 2:
        print(f"SUCCESS: RTC write verified. Drift: {drift}s")
    else:
        print(f"FAILURE: RTC write verification failed. Drift: {drift}s")

if __name__ == "__main__":
    test_rtc()
