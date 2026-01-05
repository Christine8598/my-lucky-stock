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

# --- 1. 核心功能定義 ---

@st.cache_data(ttl=3600)
def get_all_stock_list():
    """獲取全台股清單並排除金融股"""
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
        # 篩選：4碼數字且非28開頭
        clean = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return clean['code'].tolist()
    except:
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382"]

def diagnose_stock(sid, cost=0):
    """診斷單一股票買賣點"""
    try:
        t = yf.Ticker(f"{sid}.TW")
        df = t.history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        tp = round(ma20 * 1.1, 1) # 停利參考價
        sl = round(ma20, 1)       # 停損參考價 (月線)
        
        status, advice = "🟡 觀望", f"守住 {sl} 續抱"
        if c < ma20:
            status, advice = "🚨 建議賣出", f"🚨 跌破 {sl} 快跑！"
        elif bias > 10:
            status, advice = "🎁 建議停利", f"🎁 已過 {tp} 落袋"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            status, advice = "🟢 適合買入", "趨勢安全"
            
        res = {"代碼": sid, "現價": round(c, 1), "判定": status, "汪汪指令": advice, "停利價": tp, "停損價": sl, "乖離": f"{round(bias, 1)}%"}
        if cost > 0:
            res["成本"] = cost
            res["損益%"] = f"{round(((c - cost) / cost) * 100, 2)}%"
        return res
    except:
        return None

# --- 2. 側邊欄：庫存管理 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    if 'my_stocks' not in st.session_state:
        st.session_state.my_stocks = {}

    with st.form("add_stock", clear_on_submit=True):
        input_code = st.text_input("股票代碼", placeholder="例如: 3037")
        input_price = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 加入庫存"):
            if input_code and input_price > 0:
                st.session_state.my_stocks[input_code] = input_price
                st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        st.subheader("🗑️ 刪除單筆")
        del_target = st.selectbox("要丟掉哪根骨頭？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆"):
            del st.session_state.my_stocks[del_target]
            st.rerun()

# --- 3. 主頁面介面 ---
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# --- A. 庫存監控 (直觀大字版) ---
st.subheader("📋 我的汪汪庫存監控")

if st.session_state.my_stocks:
    # 1. 先用大數字卡片顯示最重要的損益
    stock_items = list(st.session_state.my_stocks.items())
    cols = st.columns(min(len(stock_items), 4)) # 最多一排顯示 4 檔
    
    my_summary_data = []
    
    for i, (sid, cost) in enumerate(stock_items):
        res = diagnose_stock(sid)
        with cols[i % 4]:
            if res:
                # 這裡會顯示像股票 APP 那樣的大字體
                p_str = res["損益%"].replace("%", "")
                p_val = float(p_str)
                st.metric(
                    label=f"🐶 {sid}", 
                    value=f"{res['現價']}", 
                    delta=f"{res['損益%']} (成本:{cost})",
                    delta_color="normal" # 自動根據賺賠變色
                )
                # 顯示最直觀的賣出指令
                st.caption(f"📢 {res['汪汪指令']}")
                
                # 整理進詳細表格 (只保留精華欄位，避免表格太寬)
                my_summary_data.append({
                    "代碼": sid,
                    "現價": res["現價"],
                    "成本": cost,
                    "損益": res["損益%"],
                    "狗狗指令": res["汪汪指令"]
                })

    # 2. 下方提供簡潔的詳細表格
    if my_summary_data:
        with st.expander("看詳細數據清單"):
            st.table(pd.DataFrame(my_summary_data))
else:
    st.info("💡 汪！妳的口袋目前空空。請在左側輸入代碼並點擊『加入庫存』！")

# B. 全台股跑酷掃描
st.subheader("🐕‍🦺 發現新骨頭 (全台股雷達)")
if st.button("🔥 啟動全台股汪汪大掃描"):
    with st.status("🐕 狗狗正在穿鞋子，準備出發...", expanded=True) as status:
        all_codes = get_all_stock_list()
        # 為了穩定，先跑前 200 檔精華股
        scan_pool = all_codes[:200]
        
        progress_bar = st.progress(0)
        dog_runner = st.empty()
        found = []
        
        for i, code in enumerate(scan_pool):
            pct = (i + 1) / len(scan_pool)
            num_s = int(pct * 30)
            dog_runner.markdown(f"**{'&nbsp;' * num_s}🐕💨 正在嗅探 {code}...**")
            progress_bar.progress(pct)
            
            res = diagnose_stock(code)
            if res and res['判定'] == "🟢 適合買入":
                found.append(res)
        
        status.update(label="✅ 汪！掃描完成！", state="complete", expanded=False)

    if found:
        st.write("### 🏆 狗狗挖到的黃金骨頭 (建議買入)")
        st.table(pd.DataFrame(found)[["代碼", "現價", "汪汪指令", "停損價", "乖離"]])
    else:
        st.warning("這區暫時沒好貨，狗狗晚點再去別條街汪！")

st.caption(f"🕒 台灣時間：{now_str} | 汪汪選股所，祝主人發大財！")