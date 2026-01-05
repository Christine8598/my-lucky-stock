import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl

# 環境與時區設定
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# 自定義 CSS 讓進度條更有趣
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #FF69B4;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# --- 1. 庫存管理功能 ---
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}

# --- 2. 核心診斷引擎 ---
def diagnose_stock(sid, cost=0):
    try:
        # 增加逾時設定避免卡住
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        take_profit_price = round(ma20 * 1.1, 1) # 停利點
        stop_loss_price = round(ma20, 1)          # 停損點
        
        status = "🟡 繼續觀察"
        advice = f"建議：{stop_loss_price} 守住續抱"
        
        if c < ma20:
            status = "🚨 汪！建議賣出"
            advice = f"🚨 跌破 {stop_loss_price} 快跑！"
        elif bias > 10:
            status = "🎁 汪！建議停利"
            advice = f"🎁 已過 {take_profit_price} 落袋為安"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            status = "🟢 汪！適合持有"
            advice = "趨勢安全，放心睡覺"
            
        res = {
            "代碼": sid,
            "現價": round(c, 1),
            "判定": status,
            "汪汪指令": advice,
            "停利目標": take_profit_price,
            "停損防線": stop_loss_price,
            "乖離": f"{round(bias, 1)}%"
        }
        
        if cost > 0:
            profit = ((c - cost) / cost) * 100
            res["我的成本"] = cost
            res["損益%"] = f"{round(profit, 2)}%"
            
        return res
    except: return None

# --- 3. 獲取全台股清單 ---
def get_all_stock_list():
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
        clean_list = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return clean_list['code'].tolist()
    except:
        return ["2330", "2317", "2454", "2603", "3037"]

# --- 4. 介面呈現 ---

# 側邊欄：庫存管理
with st.sidebar:
    st.header("🦴 庫存管理登記")
    new_code = st.text_input("輸入代碼", placeholder="例如: 2603")
    new_price = st.number_input("買進價格", value=0.0)
    if st.button("➕ 加入庫存"):
        if new_code and new_price > 0:
            st.session_state.my_stocks[new_code] = new_price
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        del_code = st.selectbox("要丟掉哪根骨頭？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆庫存"):
            del st.session_state.my_stocks[del_code]
            st.rerun()

# A. 我的庫存區
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    my_data = []
    for sid, cost in st.session_state.my_stocks.items():
        res = diagnose_stock(sid, cost)
        if res: my_data.append(res)
    if my_data:
        df_display = pd.DataFrame(my_data)
        st.table(df_display[["代碼", "現價", "我的成本", "損益%", "汪汪指令", "停利目標", "停損防線"]])
else:
    st.info("目前庫存空空，快去左側登記吧！")

st.markdown("---")

# B. 全台股掃描區 (狗狗奔跑進度條)
st.subheader("🐕‍🦺 發現新骨頭 (全台股掃描)")
if st.button("🔥 啟動全台股汪汪大掃描"):
    all_codes = get_all_stock_list()
    total = len(all_codes)
    
    # 創建進度條與文字
    progress_bar = st.progress(0)
    dog_runner = st.empty()
    found_list = []
    
    for i, code in enumerate(all_codes):
        progress = (i + 1) / total
        
        # 狗狗奔跑視覺效果：利用空格讓狗狗移動
        num_spaces = int(progress * 50)
        running_dog = " " * num_spaces + "🐕💨"
        dog_runner.markdown(f"**{running_dog}**")
        
        progress_bar.progress(progress)
        
        res = diagnose_stock(code)
        if res:
            found_list.append(res)
            
    dog_runner.markdown("✨ **🐕 呼...汪！掃描完成！發現好貨了！**")
    
    if found_list:
        st.table(pd.DataFrame(found_list)[["代碼", "現價", "判定", "汪汪指令", "乖離"]])
    else:
        st.warning("今天沒找到好骨頭，休息一下汪！")

st.caption(f"🕒 台灣時間：{now_str} | 汪汪選股所，祝主人發大財！")