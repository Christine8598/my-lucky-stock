import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time
import numpy as np

# --- 0. 基礎設定 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 1. 核心診斷邏輯 (加入理由分析與風險評分) ---
def diagnose_with_risk(sid, buy_p=0):
    try:
        # 抓取稍長一段時間來計算波動率
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if df.empty or len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # --- 計算風險分數 (基於 20 日波動率) ---
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100 # 年化波動率百分比
        
        if volatility < 15: score = 1
        elif volatility < 25: score = 2
        elif volatility < 35: score = 3
        elif volatility < 45: score = 4
        else: score = 5
        risk_bones = "🦴" * score
        
        # --- 理由分析邏輯 ---
        reasons = []
        if c > ma20: reasons.append("股價站在月線之上")
        if ma20 > ma60: reasons.append("多頭排列(月線>季線)")
        if 0 < bias <= 5: reasons.append("距離支撐點近(未追高)")
        reason_text = " + ".join(reasons) if reasons else "趨勢不明朗"
        
        # 判定
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            status = "🟢 適合買進"
            analysis = f"狗狗發現這檔骨頭剛起跑！理由：{reason_text}"
        elif c > ma20 and ma20 > ma60:
            status = "🔵 適合持有"
            analysis = f"這根骨頭很穩，繼續抱著。理由：{reason_text}"
        elif c < ma20:
            status = "🚨 警戒區"
            analysis = "已跌破月線支撐，目前風險較高"
        else:
            status = "🟡 盤整中"
            analysis = "目前還在咬骨頭，沒有方向性"

        res = {
            "代碼": sid, "現價": round(c, 1), "判定": status, 
            "深度分析": analysis, "風險等級": risk_bones, 
            "防守價": round(ma20, 1), "乖離": f"{round(bias, 1)}%"
        }
        
        if buy_p > 0:
            p_pct = ((c - buy_p) / buy_p) * 100
            res["損益%"] = p_pct
            res["成本"] = buy_p
        return res
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
        return [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
    except:
        return ["2330", "2317", "2454", "2603", "3037"]

# --- 2. 側邊欄 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    with st.form("add_form", clear_on_submit=True):
        sc = st.text_input("股票代碼")
        sp = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 確定加入庫存"):
            if sc and sp > 0:
                st.session_state.my_stocks[sc] = sp
                st.rerun()
    
    if st.session_state.my_stocks:
        st.write("---")
        del_t = st.selectbox("移除庫存：", list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除"):
            del st.session_state.my_stocks[del_t]
            st.rerun()

# --- 3. 主畫面 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# 【上層：庫存卡片】
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    items = list(st.session_state.my_stocks.items())
    cols = st.columns(4)
    for i, (sid, cost) in enumerate(items):
        res = diagnose_with_risk(sid, cost)
        if res:
            with cols[i % 4]:
                color = "inverse" if res["損益%"] > 0 else "normal"
                st.metric(label=f"🐶 {sid}", value=f"{res['現價']}", delta=f"{round(res['損益%'],2)}%", delta_color=color)
                st.write(f"風險評分: {res['風險等級']}")
                with st.expander("🔍 深度分析"):
                    st.write(res["深度分析"])
                    st.caption(f"防守門檻：{res['防守價']}")
else:
    st.info("💡 汪！妳的口袋空空，請在左側登記骨頭！")

st.markdown("---")

# 【下層：掃描雷達】
st.subheader("🐕‍🦺 全台股地毯雷達")
if st.button("🚀 啟動 1700+ 檔大掃描"):
    codes = get_stock_list()
    with st.status("🐕 狗狗正在穿上護目鏡，掃描風險中...", expanded=True) as status:
        p_bar = st.progress(0)
        found = []
        for i, c in enumerate(codes):
            pct = (i + 1) / len(codes)
            p_bar.progress(pct)
            r = diagnose_with_risk(c)
            if r and "🟢" in r["判定"]: found.append(r)
            if i % 100 == 0: time.sleep(0.01)
        st.session_state.scan_results = found
        status.update(label="✅ 風險評估完成！", state="complete")

if st.session_state.scan_results:
    st.write(f"### 🏆 推薦買進名單 (共 {len(st.session_state.scan_results)} 檔)")
    df_res = pd.DataFrame(st.session_state.scan_results)
    # 把表格欄位整理得更漂亮
    st.table(df_res[["代碼", "現價", "風險等級", "深度分析", "防守價"]])

st.caption(f"🕒 更新時間：{now_str} | 汪！")
