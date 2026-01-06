import yfinance as yf
import pandas as pd
import requests
import os

# 1. 讀取 Secrets
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(msg):
    if not LINE_TOKEN or not USER_ID:
        print("⚠️ 缺少 Secrets 設定")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + LINE_TOKEN}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    res = requests.post(url, headers=headers, json=payload)
    print("📡 LINE 狀態碼:", res.status_code)

if __name__ == "__main__":
    print("🐾 汪汪救援隊啟動！")
    
    # 測試兩支最穩的股票
    stocks = ["2330", "2317"]
    report = "🐶【汪汪巡邏回報】\n"
    
    for sid in stocks:
        try:
            # 使用舊版套件的標準抓取方式
            df = yf.download(sid + ".TW", period="1mo", progress=False)
            if not df.empty:
                price = round(float(df['Close'].iloc[-1]), 1)
                report += "\n📍 " + sid + " 現價: " + str(price)
        except Exception as e:
            print("❌ 抓取 " + sid + " 出錯: " + str(e))
    
    report += "\n\n🐾 汪！連線測試成功！"
    bark_to_line(report)
