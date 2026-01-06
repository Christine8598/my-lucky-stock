import sys
# ⭐ 強制相容補丁：讓 Python 3.9 認識新語法
if sys.version_info < (3, 10):
    import typing
    typing.Union = typing.Any 

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# 1. 讀取 Secrets
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(r):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + str(LINE_TOKEN)}
    msg = "🐶 汪汪發現強勢股：" + str(r['代碼']) + "\n📈 評分：" + str(r['得分']) + "\n💰 現價：" + str(r['現價'])
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    print("🐾 正在使用 Python 版本: " + sys.version)
    # 直接用最簡單的測試
    test_list = ["2330", "2317"]
    for sid in test_list:
        try:
            df = yf.Ticker(sid + ".TW").history(period="60d")
            score = 100 if df['Close'].iloc[-1] > df['Close'].mean() else 50
            bark_to_line({"代碼": sid, "得分": score, "現價": round(df['Close'].iloc[-1], 1)})
            print("✅ 測試發送成功: " + sid)
        except Exception as e:
            print("❌ 出錯了: " + str(e))
