# rpi-rtc-manager (Lite)

`rpi-rtc-manager` 是一個專為 Raspberry Pi 4 設計的輕量級 RTC 管理工具，使用 DS1302 模組在無網路環境下提供可靠的系統時間備援。

## 核心功能

*   **開機自動恢復**：在系統啟動早期從 RTC 讀取時間並設定系統時鐘。
*   **NTP 自動校準**：當網路可用且 NTP 同步成功後，自動更新 RTC 時間。
*   **低耗損寫入策略**：僅在時間偏差大於 30 秒時才寫入 RTC，延長硬體壽命。
*   **輕量化設計**：純 Python 實作，不依賴複雜的外部函式庫（僅需 `RPi.GPIO`）。

## 硬體需求

*   Raspberry Pi 4 (或相容型號)
*   DS1302 RTC 模組
*   CR2032 備用電池
*   **優化接線 (BCM 腳位)**:
    *   VCC -> Pin 1 (3.3V) 或 Pin 4 (5V)
    *   GND -> Pin 20 (GND)
    *   **CLK** -> GPIO 23 (Pin 16)
    *   **DAT** -> GPIO 24 (Pin 18)
    *   **RST/CE** -> GPIO 25 (Pin 22)

## 安裝步驟

### 1. 複製檔案
建議安裝路徑為 `/opt/rpi-rtc-manager`：

```bash
sudo mkdir -p /opt/rpi-rtc-manager
sudo cp -r . /opt/rpi-rtc-manager/
sudo chown -R root:root /opt/rpi-rtc-manager
```

### 2. 設定組態
編輯 `/opt/rpi-rtc-manager/config/rtc.conf` 調整 GPIO 腳位：

```conf
CLK=17
DAT=27
RST=22
```

### 3. 硬體驗證
執行測試程式確認讀寫正常：

```bash
sudo python3 /opt/rpi-rtc-manager/ds1302_test.py
```

### 4. 啟用系統服務
連結並啟動 systemd 服務：

```bash
# 連結服務檔案
sudo ln -s /opt/rpi-rtc-manager/systemd/rtc-init.service /etc/systemd/system/
sudo ln -s /opt/rpi-rtc-manager/systemd/rtc-sync.service /etc/systemd/system/
sudo ln -s /opt/rpi-rtc-manager/systemd/rtc-sync.timer /etc/systemd/system/

# 重新載入並啟用
sudo systemctl daemon-reload
sudo systemctl enable rtc-init.service
sudo systemctl enable rtc-sync.timer
sudo systemctl start rtc-sync.timer
```

## 操作說明

### 查看日誌
所有活動皆記錄於：
`tail -f /opt/rpi-rtc-manager/logs/rpi-rtc-manager.log`

### 手動同步 RTC
若想立即將當前系統時間寫入 RTC：
`sudo python3 /opt/rpi-rtc-manager/rtc_sync.py`

### 檢查服務狀態
*   開機初始化：`systemctl status rtc-init`
*   定時同步器：`systemctl status rtc-sync.timer`

## 疑難排解與電池優化

### 電池壽命優化 (Battery Optimization)
DS1302 模組在搭配非充電電池（如 AAA 或 CR2032）時，常因模組硬體設計缺陷導致耗電過快。本專案已實作以下優化：
1.  **軟體禁用涓流充電 (Trickle Charge Disable)**：驅動程式會在初始化時強制關閉內部充電功能，防止對一般電池進行錯誤充電。
2.  **時鐘停止偵測 (Clock Halt Detection)**：自動偵測電力流失狀態。

**硬體建議 (進階)**：
*   **物理切斷充電路徑**：若電池依然耗電過快，建議將模組上的 `R1` 電阻或 `D1` 二極體解焊或挑斷，防止 VCC 斷電時發生逆流漏電。
*   **電壓檢查**：AAA 電池組應維持在 3.0V 以上，若低於 2.8V 可能導致 RTC 運作不穩。

| 現象 | 可能原因 | 對策 |
| :--- | :--- | :--- |
| RTC read failed | 接線鬆脫或腳位錯誤 | 檢查 `rtc.conf` 與物理接線 |
| Year is invalid | 電池沒電或首次使用 | 待網路同步後執行 `rtc_sync.py` 或更換電池 |
| Drift ignored | 偏差小於 30 秒 | 正常現象，系統不需頻繁寫入 |

## 授權
MIT License
