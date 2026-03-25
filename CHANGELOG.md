# 更新日誌 (Changelog)

本專案的所有重大更新都將記錄在此檔案中。

## [0.2.0] - 2026-03-25

### 新增
- **網路觸發同步 (Network-Triggered Sync)**：新增了「一連網就同步」的功能，完美解決了設備長時間離線後（例如出差），需要等待數小時才會校正時間的問題。
- **實現機制**: 透過 `NetworkManager Dispatcher` 監聽網路介面狀態。當網路連線 `up` 時，會觸發新的 `rtc-sync-net.service` 立即執行一次時間同步。
- **新增檔案**:
  - `systemd/rtc-sync-net.service`: 專門用於網路觸發的單次服務。
  - `systemd/99-rtc-sync`: 當網路恢復時，負責啟動上述服務的 Dispatcher 腳本。

## [0.1.1] - 2026-03-16

### 新增
- **文件鎖機制 (File Lock)**：在 `rtc_sync.py` 中加入基於 `fcntl` 的文件鎖，防止多個實例同時執行（例如手動觸發與 systemd 定時器衝突）導致的訊號碰撞。
- **寫入驗證 (Write Verification)**：`rtc_sync.py` 現在在寫入 RTC 後會立即讀回時間，確保資料正確寫入硬體。
- **增強除錯日誌**：在 `rtc_sync.py` 中加入詳細的 Unix 時間戳與 RTC 時間對比日誌，方便進行精確的漂移分析。
- **佈署策略優化**：確定標準佈署路徑為 `/opt/rpi-rtc-manager/`，並統一使用 `root:root` 權限管理。

### 修正
- **競爭條件 (Race Condition)**：解決了因重複執行（如同時存在 root 與一般使用者的 crontab）導致 DS1302 通訊混亂及時鐘意外歸零的問題。
- **Systemd 定時優化**：調整了 `rtc-sync.timer` 的啟動間隔，確保在第一次執行同步前，系統網路與時間環境已趨於穩定。

## [0.1.0] - 2026-03-13

### 新增
- **初始版本發佈 (Lite version)**
- **DS1302 驅動程式**：使用 GPIO Bit-banging 實作，支援 BCD 格式轉換，並內建**涓流充電禁用**功能以保護電池。
- **rtc_init**：開機初始化腳本，負責從 RTC 救回系統時鐘，並具備電池失效偵測。
- **rtc_sync**：定期同步腳本，當 NTP 同步成功後自動更新 RTC 時間。
- **配置系統**：透過 `config/rtc.conf` 集中管理 GPIO 腳位與日誌路徑。
- **Systemd 整合**：提供服務與計時器設定檔，實現全自動化運行。
- **測試工具**：提供 `ds1302_test.py` 供硬體通訊驗證使用。
- **日誌系統**：整合日誌紀錄至 `/opt/rpi-rtc-manager/logs/rpi-rtc-manager.log`。
