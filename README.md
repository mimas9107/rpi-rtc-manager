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
    ├── rtc-sync.timer
    ├── rtc-sync-net.service  # (新增) 網路觸發專用服務
    └── 99-rtc-sync           # (新增) NetworkManager 觸發腳本
```

---

## 2. 模組功能說明 (Modules)

### 2.1 ds1302.py (Core Driver)
*   **功能**：提供與 DS1302 晶片的底層通訊。
*   **特性**：
    *   **UTC 基準**：RTC 內部僅儲存 UTC 時間，徹底避免時區造成的 8 小時時差 (Timezone Offset Bug)。
    *   **Burst Mode**：採用連讀/連寫模式，確保時間資料的原子性。
    *   **WP/CH 管理**：自動處理寫入保護與時鐘停止位元。
    *   **涓流充電保護**：自動關閉內部充電功能。

### 2.2 rtc_init.py (Boot Init)
*   **執行時機**：開機早期 (Network 啟動前)。
*   **功能**：將系統時鐘設定為 RTC 提供的絕對時間戳 (@timestamp)，避免時區解析衝突。

### 2.3 rtc_sync.py (Runtime Sync)
*   **執行時機**：由 `systemd timer` 定期觸發，或由網路事件觸發。
*   **功能**：
    *   **互斥鎖保護**：內建 `/tmp/rtc_sync.lock`，防止重複執行導致訊號干擾。
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
編輯 `/opt/rpi-rtc-manager/config/rtc.conf` 確保與物理接線一致。

### 3.3 註冊系統服務
```bash
# 複製服務檔與計時器檔
sudo cp /opt/rpi-rtc-manager/systemd/*.service /etc/systemd/system/
sudo cp /opt/rpi-rtc-manager/systemd/*.timer /etc/systemd/system/

# 重新載入並啟用
sudo systemctl daemon-reload
sudo systemctl enable rtc-init.service
sudo systemctl enable rtc-sync.timer
sudo systemctl start rtc-sync.timer
```

### 3.4 (新增) 註冊網路觸發同步
此功能讓 RPi 在連上網路時立即同步 RTC，解決長時間離線後的延遲校正問題。
```bash
# 複製 NetworkManager 觸發腳本
sudo cp /opt/rpi-rtc-manager/systemd/99-rtc-sync /etc/NetworkManager/dispatcher.d/
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-rtc-sync
```

### 3.5 系統時區與 RTC 設定 (重要)
為確保 Linux 系統正確解讀 RTC 內部的 UTC 時間，**務必執行以下指令**將系統配置為「RTC 使用 UTC 模式」：
```bash
# 修正系統配置，避免時區偏移 (+8h Bug)
sudo timedatectl set-local-rtc 0

# 檢查設定狀況 (RTC in local TZ 應顯示為 no)
timedatectl
```

---

## 4. 安裝後檢查方法 (Verification)

### 4.1 檢查定時器狀態
確認 `rtc-sync.timer` 已經正確排隊執行：
```bash
systemctl list-timers --all | grep rtc
```

### 4.2 查看日誌
檢視最新的同步記錄與偏差分析：
```bash
tail -n 50 /opt/rpi-rtc-manager/logs/rpi-rtc-manager.log
```

---

## 5. 問題排除 (Troubleshooting)

### 5.1 時間出現 8 小時時差 (+8h Bug)
*   **現象**：開機後時間比正確時間快或慢了 8 小時。
*   **對策**：
    1. 執行 `sudo timedatectl set-local-rtc 0`。
    2. 執行 `sudo python3 /opt/rpi-rtc-manager/rtc_sync.py` 重新校正 RTC 為 UTC 基準。

### 5.2 Drift Detected: 17 億秒 (或 0)
*   **可能原因**：DS1302 電池電力耗盡或 CH 位元被觸發。
*   **對策**：執行一次 `sudo python3 rtc_sync.py` 重新啟動時鐘。

### 5.3 競爭條件與通訊損壞
*   **現象**：Log 出現 `RTC update verification failed!`。
*   **對策**：本專案已加入文件鎖保護。請檢查是否同時存在其他的排程 (Crontab) 正在讀寫 GPIO。

---

## 6. 授權與維護
*   **維護者**：mimas9107
*   **授權**：MIT License
