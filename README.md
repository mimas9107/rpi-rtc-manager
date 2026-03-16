# rpi-rtc-manager (Lite)

`rpi-rtc-manager` 是一個專為 Raspberry Pi 4 設計的輕量級 RTC 管理工具，使用 DS1302 模組在無網路環境下提供可靠的系統時間備援。

---

## 1. 檔案結構 (File Structure)

```text
/opt/rpi-rtc-manager/
├── config.py           # 配置載入器 (GPIO、日誌路徑)
├── ds1302.py           # DS1302 底層驅動 (Bit-banging SPI)
├── rtc_init.py         # 開機初始化腳本 (讀取 RTC 並設定系統時間)
├── rtc_sync.py         # 時間同步腳本 (當 NTP 同步後校正 RTC)
├── ds1302_test.py      # 硬體測試與讀寫驗證工具
├── config/
│   └── rtc.conf        # 硬體腳位配置檔
├── logs/
│   └── rpi-rtc-manager.log # 系統運作日誌
└── systemd/            # systemd 服務與計時器設定檔
    ├── rtc-init.service
    ├── rtc-sync.service
    └── rtc-sync.timer
```

---

## 2. 模組功能說明 (Modules)

### 2.1 ds1302.py (Core Driver)
*   **功能**：提供與 DS1302 晶片的底層通訊。
*   **特性**：
    *   **Burst Mode**：採用連讀/連寫模式，確保時間資料的原子性（避免讀到一半跨秒出錯）。
    *   **WP/CH 管理**：自動處理寫入保護 (Write Protect) 與時鐘停止 (Clock Halt) 位元。
    *   **涓流充電保護**：自動關閉 Trickle Charge 功能，避免對非充電電池（如 CR2032）錯誤充電。

### 2.2 rtc_init.py (Boot Init)
*   **執行時機**：開機早期 (Network 啟動前)。
*   **功能**：檢查 RTC 電量，若時間有效（年份 ≥ 2022），則強制將系統時間設定為 RTC 時間。

### 2.3 rtc_sync.py (Runtime Sync)
*   **執行時機**：由 `systemd timer` 定期觸發（建議每 4-6 小時）。
*   **功能**：
    *   **NTP 檢查**：透過 `chronyc` 確認系統時間是否已由網路校準。
    *   **偏差處理**：偏差 < 30 秒時忽略（減少硬體寫入），偏差 ≥ 30 秒時才校正 RTC。
    *   **互斥鎖保護**：內建文件鎖 (`/tmp/rtc_sync.lock`)，防止多個實例同時執行導致訊號干擾。
    *   **寫入驗證**：寫入後立即讀回驗證，確保同步成功。

---

## 3. 安裝方法 (Installation)

### 3.1 準備工作
將專案放置於 `/opt/rpi-rtc-manager`，並將所有權交給 root：
```bash
sudo chown -R root:root /opt/rpi-rtc-manager/
sudo chmod 755 /opt/rpi-rtc-manager/logs
```

### 3.2 設定腳位
編輯 `/opt/rpi-rtc-manager/config/rtc.conf` 確保與物理接線一致：
```conf
CLK=17
DAT=27
RST=22
```

### 3.3 註冊系統服務
```bash
# 複製服務檔
sudo cp /opt/rpi-rtc-manager/systemd/*.service /etc/systemd/system/
sudo cp /opt/rpi-rtc-manager/systemd/*.timer /etc/systemd/system/

# 重新載入並啟用
sudo systemctl daemon-reload
sudo systemctl enable rtc-init.service
sudo systemctl enable rtc-sync.timer
sudo systemctl start rtc-sync.timer
```

---

## 4. 安裝後檢查方法 (Verification)

### 4.1 檢查定時器狀態
確認 `rtc-sync.timer` 已經正確排隊執行：
```bash
systemctl list-timers --all | grep rtc
```

### 4.2 檢查初始化服務
確認開機校時服務已成功執行過：
```bash
systemctl status rtc-init.service
```

### 4.3 查看日誌
檢視最新的同步記錄與偏差分析：
```bash
tail -n 50 /opt/rpi-rtc-manager/logs/rpi-rtc-manager.log
```

---

## 5. 問題排除 (Troubleshooting)

### 5.1 Drift Detected: 17 億秒 (或 0)
*   **可能原因**：DS1302 的 CH (Clock Halt) 位元被觸發，或是電池沒電/接觸不良。
*   **對策**：執行一次 `sudo python3 rtc_sync.py`。程式會自動偵測並重新啟動時鐘。若重啟後依然歸零，請檢查電池電壓。

### 5.2 競爭條件與通訊損壞
*   **現象**：Log 出現 `RTC update verification failed!` 或讀取到垃圾數據。
*   **分析**：可能有多個腳本同時存取 GPIO。
*   **對策**：本專案已加入 `/tmp/rtc_sync.lock` 文件鎖。請確保沒有其他的 `crontab` 任務在存取同一個 GPIO 腳位。

### 5.3 NTP Not Synced
*   **現象**：`rtc_sync.py` 顯示跳過同步。
*   **分析**：RPi 4 目前尚未成功連線至 NTP Server。
*   **對策**：檢查網路連線或 `chronyc tracking` 狀態。這是正常保護機制，防止將錯誤的系統時間寫入 RTC。

---

## 6. 授權與維護
*   **維護者**：mimas9107
*   **授權**：MIT License
