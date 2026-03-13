# RPI-RTC-MANAGER-SPEC.md

## 1. Overview

`rpi-rtc-manager` 是一個 **輕量級 RTC 管理工具**，用於在 Raspberry Pi 系統中利用 RTC 模組提供開機時間備援，並在網路可用時自動將 RTC 校正為網路時間。

本專案的設計原則是 **簡單、可靠、低耦合**，RTC 僅作為 **備援時間來源 (backup time source)**，而非系統權威時間來源。

系統主要依賴 NTP 作為精確時間來源，而 RTC 僅在以下情境發揮作用：

* 開機時提供初始時間
* NTP 成功同步後更新 RTC

---

## 2. Design Goals

### 2.1 Primary Goals

1. 在 **無網路環境下提供合理的系統時間**
2. 在 **有網路時使用 NTP 修正系統時間**
3. 在 **NTP 成功同步後更新 RTC**
4. 保持 **系統設計簡單且可靠**

### 2.2 Non-Goals

以下功能 **不在 Lite 版本範圍內**：

* RTC 漂移統計模型
* 長期 drift 預測
* RTC 健康監測系統
* MQTT metrics
* 複雜的狀態機

---

## 3. System Architecture

時間來源優先順序：

```
1. Network NTP
2. RTC (DS1302)
3. System Clock fallback
```

系統運作流程：

```
Boot
 │
Read RTC
 │
Set system clock
 │
System continues boot
 │
Network available
 │
NTP synchronization
 │
Update RTC
```

---

## 4. Hardware Target

本專案主要針對以下硬體：

* Raspberry Pi 4
* DS1302 RTC module
* CR2032 backup battery

RTC 角色：

```
backup boot time source
```

---

## 5. Time Format Specification

為避免時間格式混亂，系統定義三種時間格式。

### 5.1 Internal Time Format

系統內部計算使用：

```
type: int64
unit: nanoseconds
origin: Unix Epoch
name: epoch_ns
```

Example

```
1710301205123456789
```

---

### 5.2 RTC Time Format

RTC 讀寫使用：

```
type: int64
unit: seconds
name: epoch_sec
```

Example

```
1710301205
```

原因：

* DS1302 解析度為 1 秒
* 整數計算簡單
* 轉換成本低

---

### 5.3 External Time Format

Logs 或外部輸出使用：

```
ISO8601 UTC
```

Example

```
2026-03-13T12:00:05Z
```

---

## 6. Project Structure

```
rpi-rtc-manager/
│
├─ ds1302.py
├─ rtc_init.py
├─ rtc_sync.py
│
├─ config/
│   └─ rtc.conf
│
├─ logs/
│
└─ systemd/
    ├─ rtc-init.service
    └─ rtc-sync.timer
```

---

## 7. Module Specifications

### 7.1 ds1302.py

RTC driver abstraction。

Responsibilities

```
read_time()
write_time()
```

Return format

```
epoch_sec
```

Latency target

```
< 5 ms
```

---

### 7.2 rtc_init.py

系統開機時初始化系統時間。

Execution stage

```
systemd early boot
```

Flow

```
read RTC
   │
validate time
   │
set system clock
```

Validation rules

| Condition   | Result  |
| ----------- | ------- |
| year ≥ 2022 | valid   |
| year < 2022 | invalid |

Invalid RTC time → ignore。

---

### 7.3 rtc_sync.py

當網路可用時同步 RTC。

Trigger

```
network-online.target
```

或 systemd timer。

Flow

```
wait network
 │
wait NTP sync
 │
read system time
 │
read RTC
 │
calculate drift
 │
update RTC
```

---

## 8. Drift Handling (Simplified)

Drift 計算：

```
drift_sec = abs(system_time - rtc_time)
```

Threshold

| Drift    | Action      |
| -------- | ----------- |
| <30 sec  | ignore      |
| ≥120 sec | log warning |

僅記錄 log，不進行統計。

---

## 9. RTC Write Policy

RTC 僅在以下情況寫入：

```
NTP sync successful
```

Write logic

```
system_time → RTC
```

避免不必要寫入。

---

## 10. Boot Behaviour

Boot 時：

```
Boot
 │
rtc_init
 │
read RTC
 │
if valid
     set system clock
else
     ignore
```

Execution time target

```
< 50 ms
```

---

## 11. Runtime Behaviour

當網路可用時：

```
Network up
 │
NTP sync
 │
rtc_sync
 │
write RTC
```

建議使用：

```
chrony
```

作為 NTP client。

---

## 12. systemd Integration

### rtc-init.service

```
[Unit]
Description=Initialize system time from RTC
Before=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/rpi-rtc-manager/rtc_init.py

[Install]
WantedBy=multi-user.target
```

---

### rtc-sync.timer

建議定期同步 RTC：

```
OnBootSec=5min
OnUnitActiveSec=6h
```

---

## 13. Failure Handling

| Failure          | Action      |
| ---------------- | ----------- |
| RTC read fail    | log warning |
| RTC invalid time | ignore      |
| NTP unavailable  | retry later |
| RTC write fail   | log error   |

---

## 14. Performance Targets

| Operation | Target |
| --------- | ------ |
| RTC read  | <5 ms  |
| RTC write | <10 ms |
| Boot init | <50 ms |

---

## 15. Operational Summary

系統時間策略：

```
RTC → boot baseline
NTP → authoritative time
RTC ← updated after NTP sync
```

確保：

```
offline boot still has usable time
```

---

## 16. Future Extensions (Optional)

可能的未來擴充：

```
MQTT notification
RTC drift statistics
support additional RTC chips
LAN NTP server integration
```

此功能不屬於 Lite 版本範圍。

