import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# 從 GitHub Secrets 讀取你的私密資訊
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(r):
    if not LINE_TOKEN or not USER_ID:
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    msg = (f"⏰【每日 09:00 定時尋寶】\n\n"
           f"🐶 發現強勢股：{r['代碼']}\n"
           f"📈 綜合評分：{r['得分']}\n"
           f"💰 當前現價：{r['現價']}\n"
           f"📊 乖離率：{r['乖離']}\n"
           f"🐾 汪！開盤前請留意這根骨頭！")
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

# 這裡放入你原本的診斷邏輯 (簡化版)
def diagnose(sid):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last = df.iloc[-1]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        score = 0
        if last['MA20'] > last['MA60']: score += 50
        if 0 < bias <= 5: score += 50
        
        if score >= 90:
            return {"代碼": sid, "現價": round(last['Close'], 1), "得分": score, "乖離": f"{round(bias,1)}%"}
    except: return None
    return None

if __name__ == "__main__":
    # 你可以自訂掃描清單，或用原本的 get_stock_list 邏輯
    test_list = ["2330", "2317", "2454", "2603", "3037", "1513", "2382", "2308"]
    for sid in test_list:
        result = diagnose(sid)
        if result:
            bark_to_line(result)
