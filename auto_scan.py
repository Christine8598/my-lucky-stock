import sys

# ⭐ 核心補丁：讓舊版 Python 3.9 認識新版語法，解決 TypeError
if sys.version_info < (3, 10):
    import typing
    if not hasattr(typing, 'TypeAlias'):
        typing.TypeAlias = typing.Any
    # 針對 yfinance 報錯的類型宣告做特殊處理
    import types
    if not hasattr(types, 'GenericAlias'):
        class MockAlias:
            def __or__(self, other): return typing.Any
        types.GenericAlias = MockAlias()

import yfinance as yf
import pandas as pd
import requests
import os

# 1. 讀取 Secrets
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(msg):
    if not LINE_TOKEN or not USER_ID:
        print("⚠️ 找不到 LINE_TOKEN 或 USER_ID")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + str(LINE_TOKEN)}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    res = requests.post(url, headers=headers, json=payload)
    print("📡 LINE 發送狀態:", res.status_code)

if __name__ == "__main__":
    print("🐾 汪汪測試啟動，當前 Python 版本:", sys.version)
    
    # 測試抓取兩支標的
    test_list = ["2330", "2317"]
    result_msg = "🐶【汪汪巡邏連線測試】\n"
    
    for sid in test_list:
        try:
            # 使用最保險的抓取方式
            data = yf.download(sid + ".TW", period="5d", progress=False)
            if not data.empty:
                price = round(float(data['Close'].iloc[-1]), 1)
                result_msg += f"\n📍 {sid} 現價: {price}"
        except Exception as e:
            print(f"❌ {sid} 抓取失敗: {e}")
            
    result_msg += "\n\n🐾 汪！看到這條訊息代表連線成功了！"
    bark_to_line(result_msg)
