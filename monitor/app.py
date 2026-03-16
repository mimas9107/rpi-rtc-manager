from flask import Flask, render_template, jsonify
import subprocess
import time
from datetime import datetime, timezone
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ds1302 import get_rtc

LOG_PATH = "/opt/rpi-rtc-manager/logs/rpi-rtc-manager.log"

app = Flask(__name__)


def systemctl_show(unit):

    props = [
        "ActiveState",
        "SubState",
        "Result",
        "ExecMainStatus",
        "ExecMainStartTimestamp",
        "ExecMainExitTimestamp",
        "NextElapseUSecRealtime",
        "NextElapseUSecMonotonic",
        "LastTriggerUSec",
    ]

    cmd = ["systemctl", "show", unit, "--no-page"]

    out = subprocess.check_output(cmd, text=True)

    data = {}

    for line in out.splitlines():
        for p in props:
            if line.startswith(p + "="):
                k, v = line.split("=", 1)
                data[k] = v

    return data


def get_timer_next_run():
    try:
        out = subprocess.check_output(
            ["systemctl", "list-timers", "--no-page", "-all"],
            text=True
        )
        for line in out.splitlines():
            if "rtc-sync.timer" in line:
                parts = line.split()
                if len(parts) >= 4:
                    # Format: Mon 2026-03-16 18:10:42 CST 11min left    Mon 2026-03-16 14:10:42 CST 3h 48min ago  rtc-sync.timer               rtc-sync.service
                    # We want: Mon 2026-03-16 18:10:42 CST (first 4 parts)
                    next_run = parts[0] + " " + parts[1] + " " + parts[2] + " " + parts[3]
                    return next_run
    except:
        pass
    return None


def system_time():
    print(f"[sys_time] datetime.utcnow().strftime= {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def rtc_time():
    try:
        rtc = get_rtc()
        epoch = rtc.read_time()
        if epoch == 0:
            return "RTC clock halted"
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        print(f"[rtc_time] dt= {dt}")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"RTC read error: {e}"


def compute_drift():
    try:
        rtc = get_rtc()
        rtc_epoch = rtc.read_time()
        if rtc_epoch == 0:
            return None
        sys_epoch = int(time.time())
        return rtc_epoch - sys_epoch
    except:
        return None


def last_logs(lines=10):

    if not os.path.exists(LOG_PATH):
        return []

    with open(LOG_PATH) as f:
        return f.readlines()[-lines:]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():

    rtc_init = systemctl_show("rtc-init.service")
    rtc_sync = systemctl_show("rtc-sync.service")
    rtc_timer = systemctl_show("rtc-sync.timer")

    data = {
        "services": {"rtc-init.service": rtc_init, "rtc-sync.service": rtc_sync},
        "timer": rtc_timer,
        "timer_next_run": get_timer_next_run(),
        "system_time": system_time(),
        "rtc_time": rtc_time(),
        "drift": compute_drift(),
        "logs": last_logs(),
    }

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8011)
