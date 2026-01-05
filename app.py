import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 0. 基礎設定 ---
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# 初始化記憶體 (Session State)
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None  # 用來記住掃描結果

# --- 1. 核心功能定義 ---

@st.cache_data(ttl=3600)
def get_full_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        stocks = df['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        clean = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return sorted(list(set(clean['code'].tolist())))
    except:
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382"]

def diagnose_stock(sid):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="80d")
        if len(df) < 40: return None
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            return {"代碼": sid, "現價": round(c, 1), "判定": "🟢 適合買入", "汪汪指令": f"防守價: {round(ma20, 1)}", "乖離": f"{round(bias, 1)}%"}
    except: return None
    return None

# --- 2. 側邊欄：庫存管理 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    with st.form("add_stock", clear_on_submit=True):
        input_code = st.text_input("股票代碼")
        input_price = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 加入庫存"):
            if input_code and input_price > 0:
                st.session_state.my_stocks[input_code] = input_price
                st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        del_target = st.selectbox("要刪除哪筆？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆"):
            del st.session_state.my_stocks[del_target]
            st.rerun()

# --- 3. 主畫面呈現 ---
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# A. 庫存監控
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    my_data = []
    for sid, cost in st.session_state.my_stocks.items():
        res = diagnose_stock(sid)
        if res:
            res["成本"] = cost
            res["損益%"] = f"{round(((res['現價'] - cost) / cost) * 100, 2)}%"
            my_data.append(res)
    if my_data:
        st.table(pd.DataFrame(my_data)[["代碼", "現價", "成本", "損益%", "汪汪指令", "乖離"]])
else:
    st.info("💡 汪！請在側邊欄登記庫存喔！")

st.markdown("---")

# B. 全台股地毯掃描
st.subheader("🐕‍🦺 發現新骨頭 (全台股地毯式搜索)")

if st.button("🚀 啟動 1700+ 檔地毯式大掃描"):
    all_codes = get_full_stock_list()
    total = len(all_codes)
    
    with st.status("🐕 狗狗正在巡邏全台灣，請給牠一點時間...", expanded=True) as status:
        progress_bar = st.progress(0)
        dog_runner = st.empty()
        found = []
        
        for i, code in enumerate(all_codes):
            pct = (i + 1) / total
            num_s = int(pct * 30)
            dog_runner.markdown(f"**{'&nbsp;' * num_s}🐕💨 嗅探中 {i+1}/{total} : {code}**")
            progress_bar.progress(pct)
            
            res = diagnose_stock(code)
            if res: found.append(res)
            if i % 100 == 0: time.sleep(0.01)
                
        # 關鍵：掃描完後存入「大腦」
        st.session_state.scan_results = found
        status.update(label=f"✅ 汪！全台股 {total} 檔巡邏完畢！", state="complete", expanded=False)

# 顯示「記憶中」的掃描結果
if st.session_state.scan_results is not None:
    if st.session_state.scan_results:
        st.write(f"### 🏆 狗狗在全台灣挖到的精華骨頭 (共 {len(st.session_state.scan_results)} 檔)")
        st.table(pd.DataFrame(st.session_state.scan_results)[["代碼", "現價", "汪汪指令", "乖離"]])
    else:
        st.warning("嗚...狗狗跑遍全台都沒找到適合的骨頭。")

st.caption(f"🕒 台灣時間：{now_str} | 汪！")