import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import datetime

# 從 GitHub Secrets 讀取金鑰
LINE_TOKEN = os.environ.get("LINE_TOKEN")
USER_ID = os.environ.get("USER_ID")

def get_stock_list():
    """獲取全台股清單 (避開金融股與權證)"""
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, timeout=10)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        codes = df.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)[0]
        # 篩選 4 位數代碼，避開 28 開頭的金融股
        return [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
    except Exception as e:
        print(f"獲取清單失敗: {e}")
        return ["2330", "2317", "2454", "2603", "3037"] # 備援清單

def diagnose_logic(sid, df):
    """你的核心診斷邏輯"""
    try:
        if df.empty or len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last = df.iloc[-1]
        prev = df.iloc[-2]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        # 得分計算
        score = 0
        if last['MA20'] > last['MA60']: score += 25
        if last['MA60'] > df['MA60'].iloc[-5]: score += 25
        if last['Volume']/1000 > 1000: score += 20
        if 0 < bias <= 3.5: score += 30 # 絕佳買點加分
        elif bias < 10: score += 10
        if last['Volume'] < prev['Volume']: score -= 10
        
        score = max(0, min(100, score))
        
        # 只回傳強勢股 (在月線上且得分高)
        if last['Close'] > last['MA20'] and score >= 85:
            return {
                "代碼": sid,
                "現價": round(last['Close'], 1),
                "得分": score,
                "乖離": f"{round(bias, 1)}%"
            }
    except:
        return None

def send_line(message):
    if not LINE_TOKEN or not USER_ID:
        print("缺少 LINE 設定")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

def main():
    print("🐾 汪！開始全台股掃描任務...")
    codes = get_stock_list()
    found_stocks = []
    
    for c in codes:
        try:
            ticker = yf.Ticker(f"{c}.TW")
            df = ticker.history(period="100d", auto_adjust=False)
            res = diagnose_logic(c, df)
            if res:
                found_stocks.append(res)
        except:
            continue
            
    # 整理訊息內容
    if found_stocks:
        # 按得分排序
        found_stocks = sorted(found_stocks, key=lambda x: x['得分'], reverse=True)[:10]
        msg = f"⏰【每日尋寶報報】\n掃描時間：{datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        for s in found_stocks:
            msg += f"🐶 {s['代碼']} | 分數：{s['得分']}\n💰 價格：{s['現價']} (乖離：{s['乖離']})\n---\n"
        msg += "🐾 汪！這些骨頭看起來最香！"
    else:
        msg = "🐶 報告！今天大盤冷清清，沒發現香噴噴的骨頭。"
        
    send_line(msg)
    print("✅ 任務完成，訊息已送出！")

if __name__ == "__main__":
    main()
