# 串串串

燕雲機器人。有人用指定 emoji 對訊息按反應時，在同一頻道用那個人的暱稱和頭像重發一次。

## 功能

- 預設觸發 emoji 是 ➕，每個伺服器可用 `/setmimicemoji` 修改
- 監聽機器人看得到的文字頻道與討論串
- 狀態固定為「正在抽八音」

## 指令

| 指令 | 說明 | 權限 |
|------|------|------|
| `/setmimicemoji` | 設定觸發重發的 emoji | 管理員 |

## 設定

1. 安裝依賴：`pip install -r requirements.txt`
2. 在 `config.env` 寫入 `DISCORD_BOT_TOKEN`
3. 執行 `python run.py`

邀請時需要 **Manage Webhooks**、Read Message History、View Channels、Use Slash Commands。

## 專案結構

```
dc2/
├── bot.py
├── run.py
├── utils.py
├── data_manager.py
├── cogs/
│   ├── mimic.py
│   └── tasks.py
└── data/
    └── mimic_emojis.json
```
