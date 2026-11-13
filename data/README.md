# 十翼數據文件

## 文件說明

- **文件名稱**：`shi_yi_data.json`
- **數據來源**：杜澤遜主編《周易注疏匯校》（中華書局）
- **數據版本**：1.0.0
- **文件大小**：約 42 KB

## 數據結構

```json
{
  "version": "1.0.0",          // 數據版本號
  "source": "...",             // 數據來源說明
  "exported_at": "2026-10-27", // 導出日期
  "da_xiang": {               // 大象傳（64 卦）
    "乾为天": "天行健，君子以自強不息。",
    ...
  },
  "tuan_zhuan": {             // 彖傳（64 卦）
    "乾为天": {
      "彖曰": "...",
      "釋義": "..."
    },
    ...
  },
  "xiao_xiang": {             // 小象傳（64 卦 × 6 爻 = 384 條）
    "乾为天": [
      "潛龍勿用，陽在下也。",
      ...
    ],
    ...
  },
  "wen_yan": {                // 文言傳（乾、坤兩卦）
    "乾": {
      "原文": "...",
      "釋義": "...",
      ...
    },
    "坤": { ... }
  },
  "za_gua": {                 // 雜卦傳（32 對）
    "乾健也，坤順也": {
      "乾": "剛健不息，創造萬物。",
      "坤": "柔順承天，容載萬物。"
    },
    ...
  }
}
```

## 如何更新數據

### 方法一：直接編輯 JSON（推薦）

1. 用文本編輯器（如 VS Code、Notepad++）打開 `shi_yi_data.json`
2. 找到對應的卦名和數據類型
3. 修改內容後保存
4. 下次啟動程序即可生效（無需重新打包 exe）

### 方法二：用 Python 腳本更新

```python
import json

# 讀取現有數據
with open('data/shi_yi_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修改數據（例如修改乾為天的大象傳）
data['da_xiang']['乾为天'] = "天行健，君子以自強不息。"

# 保存
with open('data/shi_yi_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 數據文件位置

| 環境 | 路徑 |
|------|------|
| 開發環境 | `yijing-demo/data/shi_yi_data.json` |
| 打包環境 | `yijing_gui/_internal/data/shi_yi_data.json` |

> **注意**：打包後的數據文件在 `_internal/data/` 目錄下，由程序自動定位，無需手動複製。

## 回退機制

如果 JSON 文件不存在或解析失敗，程序會自動回退到 Python 模塊（`da_xiang.py`、`tuan_zhuan.py` 等）作為備份數據源。

## 版本記錄

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0.0 | 2026-10-27 | 初始版本，基於《周易注疏匯校》 |
