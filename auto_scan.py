import sys

# ⭐【核心修復】這段補丁會騙過 yfinance，解決 Python 3.9 的語法報錯問題
if sys.version_info < (3, 10):
    import typing
    # 建立一個假的 Union 類型來應付新版語法
    if not hasattr(typing, 'TypeAlias'):
        typing.TypeAlias = typing.Any
    # 解決截圖中報錯的 "|" 符號衝突
    class GenericAliasPatch:
        def __or__(self, other): return typing.Any
    sys.modules['types'].GenericAlias = GenericAliasPatch()

# --- 現在開始原本的程式碼 ---
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# 從 Secrets 拿鑰匙
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(sid, score, price):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    msg = f"🐶 汪汪巡邏報：\n\n發現標的：{sid}\n評分：{score}\n現價：{price}\n🐾 汪！"
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    print(f"🐾 正在使用 Python {sys.version} 執行...")
    # 我們先用兩支最強的標的來測試通訊
    test_list = ["2330", "2317"] 
    
    for sid in test_list:
        try:
            ticker = yf.Ticker(f"{sid}.TW")
            df = ticker.history(period="60d")
            if not df.empty:
                last_price = round(df['Close'].iloc[-1], 1)
                # 測試邏輯：只要有收盤價就發送
                bark_to_line(sid, "測試中", last_price)
                print(f"✅ {sid} 掃描成功並嘗試發送")
        except Exception as e:
            print(f"❌ {sid} 發生錯誤: {str(e)}")
