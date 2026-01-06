import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import sys

# 1. 讀取 Secrets
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(r):
    if not LINE_TOKEN or not USER_ID:
        print("⚠️ 找不到 LINE_TOKEN 或 USER_ID")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + LINE_TOKEN}
    
    msg = "⏰【汪汪巡邏】\n\n發現標的：" + str(r['代碼']) + "\n得分：" + str(r['得分']) + "\n現價：" + str(r['現價']) + "\n🐾 汪！"
    
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    res = requests.post(url, headers=headers, json=payload)
    print("📡 LINE 狀態:", res.status_code)

def diagnose_logic(sid, df):
    try:
        if df.empty or len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last = df.iloc[-1]
        
        score = 0
        if last['MA20'] > last['MA60']: score += 50
        
        return {"代碼": sid, "現價": round(last['Close'], 1), "得分": score}
    except: return None

if __name__ == "__main__":
    print("🐾 正在測試版本: " + sys.version)
    # 這裡放幾支權值股測試，確保一定會跑出結果
    test_list = ["2330", "2317", "2454"]
    for sid in test_list:
        ticker = yf.Ticker(sid + ".TW")
        df = ticker.history(period="100d")
        res = diagnose_logic(sid, df)
        if res:
            bark_to_line(res)
