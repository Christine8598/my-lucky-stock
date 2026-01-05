import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 0. 基礎設定與環境修復 ---
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# 初始化 Session State
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 1. 核心功能定義 ---

@st.cache_data(ttl=3600)
def get_full_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'big5'
        df_list = pd.read_html(response.text)[0]
        df_list.columns = df_list.iloc[0]
        stocks = df_list.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        clean = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return sorted(list(set(clean['code'].tolist())))
    except:
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382"]

def diagnose_stock(sid, buy_price=0):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="80d")
        if len(df) < 40: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 買賣指令
        sl = round(ma20, 1) # 停損防線
        status, advice = "🟡 繼續觀察", f"守住 {sl} 續抱"
        if c < ma20: status, advice = "🚨 建議賣出", f"跌破 {sl} 快跑！"
        elif bias > 10: status, advice = "🎁 建議停利", f"已過高，入袋為安"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5: status, advice = "🟢 適合持有", "趨勢向上安全"
            
        res = {
            "代碼": sid, 
            "現價": round(c, 1), 
            "判定": status, 
            "指令": advice, 
            "乖離": f"{round(bias, 1)}%"
        }
        
        if buy_price > 0:
            profit_pct = ((c - buy_price) / buy_price) * 100
            res["損益%"] = profit_pct # 存數值方便計算
            res["顯示損益"] = f"{round(profit_pct, 2)}%"
            res["成本"] = buy_price
            
        return res
    except:
        return None

# --- 2. 側邊欄：庫存管理 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    with st.form("add_stock_form", clear_on_submit=True):
        sc_code = st.text_input("股票代碼", placeholder="例如: 3037")
        sc_price = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 加入庫存"):
            if sc_code and sc_price > 0:
                st.session_state.my_stocks[sc_code] = sc_price
                st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        st.subheader("🗑️ 刪除庫存")
        del_target = st.selectbox("要丟掉哪根骨頭？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 確定刪除"):
            del st.session_state.my_stocks[del_target]
            st.rerun()

# --- 3. 主畫面呈現 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 {now_str[:10]} Christine 汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# A. 我的庫存監控 (改用大字體卡片儀表板)
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    stock_items = list(st.session_state.my_stocks.items())
    # 橫向排列卡片
    cols = st.columns(len(stock_items) if len(stock_items) < 5 else 4)
    
    for i, (sid, cost) in enumerate(stock_items):
        res = diagnose_stock(sid, cost)
        if res:
            with cols[i % 4]:
                st.metric(
                    label=f"🐶 {sid}", 
                    value=f"{res['現價']}", 
                    delta=f"{res['顯示損益']} (成本:{cost})",
                    delta_color="normal"
                )
                st.caption(f"📢 {res['指令']}")
else:
    st.info("💡 汪！妳的口袋空空，快在左邊登記妳的骨頭吧！")

st.markdown("---")

# B. 全台股地毯大搜索
st.subheader("🐕‍🦺 發現新骨頭 (1700+ 檔地毯大搜索)")
if st.button("🚀 啟動全台股地毯式大掃描"):
    all_codes = get_full_stock_list()
    total = len(all_codes)
    
    with st.status("🐕 狗狗正在巡邏全台灣，請給牠一點時間...", expanded=True) as status:
        progress_bar = st.progress(0)
        dog_runner = st.empty()
        found = []
        
        for i, code in enumerate(all_codes):
            pct = (i + 1) / total
            num_s = int(pct * 30)
            dog_runner.markdown(f"**{'&nbsp;' * num_s}🐕💨 正在嗅探第 {i+1}/{total} 檔：{code}**")
            progress_bar.progress(pct)
            
            res = diagnose_stock(code)
            if res and res["判定"] == "🟢 適合持有":
                found.append(res)
            if i % 100 == 0: time.sleep(0.01)
                
        st.session_state.scan_results = found
        status.update(label=f"✅ 汪！全台股 {total} 檔巡邏完畢！", state="complete", expanded=False)

# 顯示記憶中的結果
if st.session_state.scan_results:
    st.write(f"### 🏆 狗狗挖到的精華骨頭 (共 {len(st.session_state.scan_results)} 檔)")
    st.table(pd.DataFrame(st.session_state.scan_results)[["代碼", "現價", "指令", "乖離"]])

st.caption(f"🕒 台灣時間：{now_str} | 汪！")