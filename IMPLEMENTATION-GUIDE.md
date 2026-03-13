# IMPLEMENTATION-GUIDE.md

Guide for Implementing `rpi-rtc-manager` (Lite)

---

# 1. Purpose

本文件提供 **實作順序、測試流程與除錯方法**，供工程師或 AI agent 依照 `RPI-RTC-MANAGER-SPEC.md` 進行開發與驗證。

目標：

* 讓 `rpi-rtc-manager` **快速可用**
* 減少實作過程中的錯誤
* 提供一致的測試流程

---

# 2. Implementation Strategy

建議採用 **分階段實作 (incremental implementation)**。

避免一次完成所有功能。

實作順序：

```
Phase 1  DS1302 Driver
Phase 2  RTC Read Test
Phase 3  RTC Write Test
Phase 4  rtc_init boot restore
Phase 5  rtc_sync NTP update
Phase 6  systemd integration
Phase 7  reliability testing
```

---

# 3. Development Environment

Target platform:

* Raspberry Pi 4
* Debian / Raspberry Pi OS
* Python 3.10+

Required tools:

```
python3
chrony
systemd
```

RTC module:

* DS1302
* CR2032 battery

---

# 4. Phase 1 — Implement DS1302 Driver

File:

```
ds1302.py
```

Required functions:

```
read_time()
write_time()
```

Return format:

```
epoch_sec (int)
```

Driver responsibilities:

* GPIO communication
* BCD ↔ decimal conversion
* register read/write

Validation:

```
read_time() returns plausible timestamp
```

---

# 5. Phase 2 — RTC Read Test

Create a small test script.

Goal:

```
verify RTC communication works
```

Test procedure:

```
1 connect RTC module
2 run read_time()
3 print timestamp
4 convert to ISO time
```

Expected result:

```
reasonable date/time
```

Common problems:

| Problem       | Cause                |
| ------------- | -------------------- |
| read failure  | wiring               |
| wrong time    | BCD conversion error |
| random values | CLK timing issue     |

---

# 6. Phase 3 — RTC Write Test

Goal:

```
verify write_time() works
```

Procedure:

```
1 set known timestamp
2 write RTC
3 read RTC again
4 compare values
```

Expected:

```
written time ≈ read time
```

Acceptable tolerance:

```
≤ 1 second
```

---

# 7. Phase 4 — Implement rtc_init

File:

```
rtc_init.py
```

Purpose:

```
restore system time from RTC at boot
```

Flow:

```
read RTC
validate time
set system clock
```

Validation rules:

```
year >= 2022
year <= current_year + 1
```

If invalid:

```
do nothing
```

Command used to set system clock:

```
date -s
```

---

# 8. Phase 5 — Implement rtc_sync

File:

```
rtc_sync.py
```

Purpose:

```
update RTC after NTP synchronization
```

Flow:

```
wait NTP stable
read system time
read RTC
calculate drift
write RTC
```

Drift calculation:

```
drift_sec = abs(system_time - rtc_time)
```

Log drift value.

---

# 9. Detecting NTP Synchronization

Use `chrony` status.

Command:

```
chronyc tracking
```

Valid state example:

```
Leap status     : Normal
```

If status is not normal:

```
retry later
```

---

# 10. Phase 6 — systemd Integration

Install service files.

Directory:

```
/etc/systemd/system/
```

Services:

```
rtc-init.service
rtc-sync.timer
```

---

## rtc-init.service

Runs once at boot.

```
Before=network.target
```

Purpose:

```
restore system clock early
```

---

## rtc-sync.timer

Purpose:

```
periodically update RTC
```

Suggested schedule:

```
OnBootSec=5min
OnUnitActiveSec=6h
```

---

# 11. Phase 7 — Reliability Testing

Run several tests.

---

## Test 1 — Offline Boot

Procedure:

```
disable internet
reboot system
```

Expected:

```
system clock ≈ RTC
```

Tolerance:

```
≤ 2 sec
```

---

## Test 2 — NTP Correction

Procedure:

```
set RTC time wrong
reboot
enable internet
```

Expected:

```
system corrected by NTP
RTC updated
```

---

## Test 3 — RTC Battery Failure

Procedure:

```
remove RTC battery
reboot
```

Expected:

```
RTC invalid
system ignores RTC
```

---

## Test 4 — Multiple Reboots

Procedure:

```
reboot system 10 times
```

Expected:

```
stable time initialization
```

---

# 12. Logging

All modules should log to:

```
/var/log/rpi-rtc-manager.log
```

Log examples:

```
RTC read: 2026-03-13T10:12:04Z
RTC drift: 3 seconds
RTC updated
```

---

# 13. Debugging Guide

Common debugging steps.

---

## Check RTC

```
python3 ds1302_test.py
```

---

## Check NTP

```
chronyc tracking
```

---

## Check system time

```
date
```

---

## Check logs

```
journalctl -u rtc-init
```

---

# 14. Performance Expectations

Typical timings:

| Operation | Expected Time |
| --------- | ------------- |
| RTC read  | <5 ms         |
| RTC write | <10 ms        |
| rtc_init  | <50 ms        |

---

# 15. Deployment Layout

Suggested install location:

```
/opt/rpi-rtc-manager
```

Directory layout:

```
/opt/rpi-rtc-manager/
    ds1302.py
    rtc_init.py
    rtc_sync.py
    config/
```

---

# 16. Operational Summary

Normal lifecycle:

```
Boot
 │
RTC → system clock
 │
System runs
 │
Internet available
 │
NTP sync
 │
RTC updated
```

---

# 17. Future Improvements (Optional)

Possible upgrades after Lite version stabilizes:

```
LAN NTP server
MQTT notifications
RTC drift statistics
support additional RTC chips
```

These improvements are outside the scope of the Lite implementation.

