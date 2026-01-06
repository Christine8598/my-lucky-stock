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
def diagnose_logic(sid, df, buy_p=0):
    try:
        if df.empty or len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last, prev = df.iloc[-1], df.iloc[-2]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        # --- 1. 計算得分與風險 (必須先定義 score 和 volatility) ---
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        bones = "🦴" * min(5, max(1, int(volatility / 10)))
        
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

        # --- 2. [自動切換] 停損停利邏輯 ---
        stop_signal = ""
        if buy_p > 0:
            profit_loss_ratio = (last['Close'] - buy_p) / buy_p
            
            # A. 基礎防線：停損
            if profit_loss_ratio <= -0.07:
                stop_signal = "🆘 汪！跌幅超標！(停損 -7%)"
            elif last['Close'] < last['MA20']:
                stop_signal = "⚠️ 汪！破月線了！(趨勢轉弱)"
            
            # B. 判斷模式：00開頭、權值股、或高分穩健股皆視為「長線模式」
            else:
                is_long_term = (sid.startswith("00")) or \
                               (sid in ["2330", "2317", "2454"]) or \
                               (score >= 80 and volatility < 35)

                if is_long_term:
                    # 長線不輕易停利
                    if profit_loss_ratio >= 1.0:
                        stop_signal = "👑 傳奇汪：達成翻倍成就！跟著國運一起飛"
                    elif profit_loss_ratio >= 0.20:
                        if bias > 15:
                            stop_signal = "💎 成長汪：獲利達標但乖離稍大，建議減碼非全賣"
                        else:
                            stop_signal = "🚀 成長汪：強勢波段中，沒破月線請抱緊！"
                else:
                    # 短線股 20% 提醒
                    if profit_loss_ratio >= 0.20:
                        stop_signal = "💰 短線汪：獲利 +20% 達標，汪汪入袋為安！"

        return {
            "代碼": sid, "現價": round(last['Close'], 1), "得分": score,
            "風險": bones, "乖離": f"{round(bias, 1)}%", "買點": buy_note,
            "判定": "🟢 強勢" if last['Close'] > last['MA20'] else "🔴 轉弱",
            "損益%": round(((last['Close'] - buy_p) / buy_p) * 100, 2) if buy_p > 0 else 0,
            "警報": stop_signal
        }
    except Exception as e:
        print(f"診斷出錯: {e}")
        return None

# 這個函數負責「抓資料」
def diagnose_with_soul(sid, buy_p=0):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="100d", auto_adjust=False)
        return diagnose_logic(sid, df, buy_p)
    except: return None
        
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, verify=False, timeout=10)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        codes = df.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)[0]
        # 過濾四位數代碼，避開金融股(28開頭)
        return [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
    except: return ["2330", "2317", "2454", "2603", "3037"]

    for sid in test_list:
        result = diagnose(sid)
        if result:
            bark_to_line(result)
