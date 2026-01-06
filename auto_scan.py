import sys

# 解決 yfinance 在舊版 Python 的語法衝突
if sys.version_info < (3, 10):
    import typing
    if not hasattr(typing, 'TypeAlias'):
        typing.TypeAlias = typing.Any
        
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# --- 1. 從 GitHub Secrets 讀取你的私密資訊 ---
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(r):
    if not LINE_TOKEN or not USER_ID:
        print("⚠️ 找不到 LINE_TOKEN 或 USER_ID")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    
    # 建立訊息內容
    msg = (f"⏰【汪汪定時巡邏回報】\n\n"
           f"🐶 發現強勢股：{r['代碼']}\n"
           f"📈 綜合評分：{r['得分']}\n"
           f"💰 當前現價：{r['現價']}\n"
           f"📊 乖離率：{r['乖離']}\n"
           f"🎯 買點建議：{r['買點']}\n\n"
           f"🐾 汪！這根骨頭看起來很不錯喔！")
    
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    res = requests.post(url, headers=headers, json=payload)
    print(f"📡 LINE 發送狀態: {res.status_code}")

# --- 2. 核心診斷邏輯 ---
def diagnose_logic(sid, df, buy_p=0):
    try:
        if df.empty or len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last, prev = df.iloc[-1], df.iloc[-2]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        
        score = 0
        if last['MA20'] > last['MA60']: score += 25
        if last['MA60'] > df['MA60'].iloc[-5]: score += 25
        if last['Volume']/1000 > 1000: score += 20
        if bias < 10: score += 10
        
        buy_note = "🐾建議稍等回檔"
        if 0 < bias <= 3.5:
            score += 20
            buy_note = "🎯 絕佳買點"
        elif bias > 10: buy_note = "🚨 乖離過大"
        
        if last['Volume'] < prev['Volume']: score -= 10
        score = max(0, min(100, score))

        return {
            "代碼": sid, "現價": round(last['Close'], 1), "得分": score,
            "乖離": f"{round(bias, 1)}%", "買點": buy_note
        }
    except Exception as e:
        print(f"診斷 {sid} 出錯: {e}")
        return None

def diagnose_with_soul(sid):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="100d", auto_adjust=False)
        return diagnose_logic(sid, df)
    except: return None

def get_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        # 注意：GitHub 環境需要加 headers 模擬瀏覽器
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, verify=False, timeout=10)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        codes = df.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)[0]
        return [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
    except Exception as e:
        print(f"抓取清單失敗: {e}")
        return ["2330", "2317", "2454", "2603", "3037", "2382", "3231", "1513"]

# --- 3. 執行區 ---
if __name__ == "__main__":
    print("🐾 汪汪巡邏開始...")
    codes = get_stock_list()
    found_count = 0
    
    for sid in codes:
        result = diagnose_with_soul(sid)
        # 設定發送門檻：得分 >= 90 分才發 LINE 通知
        if result and result['得分'] >= 90:
            print(f"🎯 發現好骨頭！{sid} 得分：{result['得分']}")
            bark_to_line(result)
            found_count += 1
            
    print(f"🏁 巡邏結束，共發現 {found_count} 檔高品質骨頭。")
