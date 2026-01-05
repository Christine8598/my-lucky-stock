import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# 0. 環境設定與時區
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

# 1. 網頁基本配置
st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# --- 2. 側邊欄：庫存登記處 (核心功能) ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    st.write("在這裡輸入妳買入的骨頭資訊：")
    
    # 初始化庫存資料 (如果還沒有的話)
    if 'my_stocks' not in st.session_state:
        st.session_state.my_stocks = {}

    with st.form("add_stock_form", clear_on_submit=True):
        input_code = st.text_input("股票代碼", placeholder="例如: 3037")
        input_price = st.number_input("買進成本", min_value=0.0, step=0.1)
        submit_button = st.form_submit_button("➕ 加入庫存")
        
        if submit_button and input_code and input_price > 0:
            st.session_state.my_stocks[input_code] = input_price
            st.success(f"汪！已加入 {input_code}")
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        st.subheader("🗑️ 管理庫存")
        del_target = st.selectbox("選擇要刪除的股票", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆庫存"):
            del st.session_state.my_stocks[del_target]
            st.rerun()
        
        if st.button("🧨 全部清空"):
            st.session_state.my_stocks = {}
            st.rerun()

# --- 3. 核心判定引擎 ---
def diagnose_stock(sid, cost=0):
    try:
        t = yf.Ticker(f"{sid}.TW")
        df = t.history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        tp = round(ma20 * 1.1, 1) # 停利參考
        sl = round(ma20, 1)       # 停損參考 (月線)
        
        status, advice = "🟡 觀望", f"守住 {sl} 續抱"
        if c < ma20: status, advice = "🚨 建議賣出", f"🚨 跌破 {sl} 快跑！"
        elif bias > 10: status, advice = "🎁 建議停利", f"🎁 已過 {tp} 落袋"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5: status, advice = "🟢 適合買入", "趨勢安全"
            
        res = {"代碼": sid, "現價": round(c, 1), "判定": status, "汪汪指令": advice, "停利價": tp, "停損價": sl}
        if cost > 0:
            res["成本"] = cost
            res["損益%"] = f"{round(((c - cost) / cost) * 100, 2)}%"
        return res
    except: return None

# --- 4. 主畫面呈現 ---
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# A. 我的庫存區
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    my_results = []
    for sid, cost in st.session_state.my_stocks.items():
        res = diagnose_stock(sid, cost)
        if res: my_results.append(res)
    if my_results:
        st.table(pd.DataFrame(my_results)[["代碼", "現價", "成本", "損益%", "汪汪指令", "停利價", "停損價"]])
else:
    st.info("💡 汪！請看左側側邊欄，登記妳買入的股票喔！ (若沒看到側邊欄，請點左上角 '>' )")

st.markdown("---")

# B. 全台股掃描區 (狗狗奔跑特效)
st.subheader("🐕‍🦺 發現新骨頭 (全台股雷達)")
if st.button("🔥 啟動全台股汪汪大掃描"):
    # 獲取清單
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    response = requests.get(url, verify=False)
    response.encoding = 'big5'
    df_list = pd.read_html(response.text)[0]
    df_list.columns = df_list.iloc[0]
    codes = df_list['有價證券代號及名稱'].str.split('　', expand=True)[0].tolist()
    clean_codes = [c for c in codes if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')][:300]
    
    progress_bar = st.progress(0)
    dog_status = st.empty()
    found = []
    
    for i, code in enumerate(clean_codes):
        progress = (i + 1) / len(clean_codes)
        num_spaces = int(progress * 35)
        dog_status.markdown(f"**{'&nbsp;' * num_spaces}🐕💨 正在嗅探 {code}...**")
        progress_bar.progress(progress)
        
        item = diagnose_stock(code)
        if item and item['判定'] == "🟢 適合買入":
            found.append(item)
    
    dog_status.success("✨ 汪！前 300 檔活躍股掃描完成！")
    if found:
        st.table(pd.DataFrame(found)[["代碼", "現價", "汪汪指令", "停損價"]])
    else:
        st.warning("這區沒找到適合買入的骨頭汪！")

st.caption(f"🕒 台灣時間：{now_str} | 汪汪選股所，祝主人發大財！")