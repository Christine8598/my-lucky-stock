import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import time
import requests
import ssl
import datetime

# --- 0. 基礎設定與 SSL 修復 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# --- 1. 永久記憶功能：檔案存取 ---
DB_FILE = "my_stock_memory.json"

def load_memory():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_memory(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def bark_to_line(token, user_id, r):
    """讓機器人汪一聲！"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    msg = (f"🌟【手動掃描回報】🌟\n\n"
           f"🐶 標的：{r['代碼']}\n"
           f"📈 得分：{r['得分']}\n"
           f"💰 現價：{r['現價']}\n"
           f"🐾 汪！這根骨頭看起來很不錯！")
    payload = {"to": user_id, "messages": [{"type": "text", "text": msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=5)
    except:
        pass
        
# 初始化 Session State
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = load_memory()
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 2. 核心診斷邏輯 (修正版) ---
# 必須先定義這個函數
def get_market_sentiment():
    try:
        twii = yf.Ticker("^TWII")
        df = twii.history(period="60d")
        df['MA20'] = df['Close'].rolling(20).mean()
        last_close = df['Close'].iloc[-1]
        last_ma20 = df['MA20'].iloc[-1]
        if last_close > last_ma20:
            return "🟢 多頭 (大盤在月線上，適合進攻)", True
        else:
            return "🔴 空頭 (大盤在月線下，建議保守)", False
    except:
        return "⚪ 無法取得大盤資訊", True
        
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

# --- 3. 側邊欄：庫存登記 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    sc = st.text_input("股票代碼")
    sp = st.number_input("買進成本", min_value=0.0, step=0.1)
    if st.button("➕ 寫入記憶存檔"):
        if sc and sp > 0:
            st.session_state.my_stocks[sc] = sp
            save_memory(st.session_state.my_stocks)
            st.success(f"汪！{sc} 已存入永久記憶！")
            time.sleep(1)
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        del_t = st.selectbox("移除：", list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除並更新檔案"):
            del st.session_state.my_stocks[del_t]
            save_memory(st.session_state.my_stocks)
            st.rerun()

# --- 4. 主畫面 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# 【上層：永久庫存卡片】
st.subheader("📋 我的「骨」倉")
if st.session_state.my_stocks:
    cols = st.columns(4)
    for i, (sid, cost) in enumerate(st.session_state.my_stocks.items()):
        res = diagnose_with_soul(sid, cost)
        if res:
            with cols[i % 4]:
                # 修正：根據 "警報" 欄位判斷顏色
                d_color = "inverse" if res['警報'] != "" else "normal"
                st.metric(label=f"🐶 {sid}", value=f"{res['現價']}", delta=f"{res['損益%']}%", delta_color=d_color)
                
                with st.expander("🔍 深度分析"):
                    # 修正：顯示 "警報" 內容
                    if res['警報']:
                        if "🆘" in res['警報'] or "⚠️" in res['警報']:
                            st.error(res['警報'])
                        else:
                            st.success(res['警報'])
                    st.write(f"得分: {res['得分']} | 風險: {res['風險']}")
                    st.write(f"判定: {res['買點']}")
else: st.info("💡 目前沒有存檔的骨頭汪。")

st.markdown("---")
market_status, is_bull = get_market_sentiment()
st.info(f"📊 **目前大盤環境：{market_status}**")

if not is_bull:
    st.warning("⚠️ 警語：目前大盤走勢疲軟，選股雷達發現的標的請務必謹慎小量參與。")
# 【下層：不中斷掃描雷達 - 優化版】
st.subheader("🐕‍🦺 汪星人台股尋寶雷達")

# 用一個 container 來統一管理顯示區域
scan_container = st.container()

if st.button("🚀 啟動全台尋寶"):
    codes = get_stock_list()
    status_area = st.empty()
    progress_bar = st.progress(0)
    found = []
    
    # 建立一個佔位空間，專門用來放表格
    table_placeholder = st.empty()
    
    for i, c in enumerate(codes):
        progress = (i + 1) / len(codes)
        progress_bar.progress(progress)
        if i % 10 == 0:
            status_area.markdown(f"🐕 狗狗巡邏中... 當前進度: **{int(progress*100)}%** ({c})")
        
        r = diagnose_with_soul(c)
        # 篩選：強勢且得分 >= 75
        if r and "🟢" in r["判定"] and r["得分"] >= 75:
            found.append(r)
            st.session_state.scan_results = found 
            # 即時在佔位空間更新表格內容
            with table_placeholder.container():
                st.write(f"### 🏆 已發現 {len(found)} 檔高品質骨頭")
                df_temp = pd.DataFrame(found)[["代碼", "現價", "得分", "風險", "買點", "乖離"]]
                st.table(df_temp.tail(15)) # 掃描時顯示最新發現的 15 筆，避免頁面拉太長
            
    status_area.success(f"✅ 全台尋寶完畢！共計發現 {len(found)} 檔。")
    # 掃描結束後，把佔位空間換成完整的總表
    with table_placeholder.container():
        st.write(f"### 🏁 全台尋寶總表 (共 {len(found)} 檔)")
        st.dataframe(pd.DataFrame(found)[["代碼", "現價", "得分", "風險", "買點", "乖離"]])

# 如果頁面重新整理，但之前已經有掃描結果，就顯示出來
elif st.session_state.scan_results:
    st.write(f"### 🏁 上次巡邏結果 (共 {len(st.session_state.scan_results)} 檔)")
    st.dataframe(pd.DataFrame(st.session_state.scan_results)[["代碼", "現價", "得分", "風險", "買點", "乖離"]])

st.caption(f"🕒 更新時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 汪！")












