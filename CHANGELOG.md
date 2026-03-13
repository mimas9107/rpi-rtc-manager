# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-13

### Added
- **Initial Release (Lite version)**
- **DS1302 Driver**: Low-level GPIO bit-banging implementation with BCD support and **Trickle Charge Disable** to protect non-rechargeable batteries.
- **rtc_init**: Boot-time script to restore system clock from RTC (Phase 4) with **Battery Failure detection**.
- **rtc_sync**: Periodic synchronization script to update RTC from NTP/System clock (Phase 5).
- **Configuration System**: Centralized GPIO and log management via `config/rtc.conf`.
- **Systemd Integration**: Added service and timer files for automated operation.
- **Test Suite**: `ds1302_test.py` for hardware validation (Phase 2 & 3).
- **Logging**: Integrated logging to `/opt/rpi-rtc-manager/logs/rpi-rtc-manager.log`.
- **Documentation**: Added `README.md`, `CHANGELOG.md`, `RPI-RTC-MANAGER-SPEC.md`, and `IMPLEMENTATION-GUIDE.md`.
- **Validation**: Successfully verified on RPi4 (Hardware & Offline Recovery tests). See `reports/TEST-20260313.md`.
