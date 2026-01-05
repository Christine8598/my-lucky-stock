import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定 (加入狗狗圖案！)
st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6A5ACD;'>讓可愛的狗狗們為妳嗅出股市裡的黃金骨頭！</p>", unsafe_allow_html=True)

# --- 2. 核心診斷功能 ---
def diagnose_stock(sid):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 篩選條件：多頭排列且乖離率在 0~5% 之間
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            return {
                "代碼": sid,
                "判定結果": "🟢 汪！適合買入！",
                "汪汪理由": "趨勢強勁，價格回到安全狗窩區。",
                "現價 (元)": round(c, 1),
                "乖離率": f"{round(bias, 1)}%",
                "跌破這價就跑 (元)": round(ma20 * 0.95, 1) # 加入停損價
            }
    except:
        return None
    return None

# --- 3. 介面呈現 ---

# A. 個股診斷區 (加入狗狗元素)
st.subheader("🦴 個股診斷區：汪！這檔適合撿嗎？")
search_id = st.text_input("請輸入 4 位股票代碼 (例如：3037)", key="search_input")
if search_id:
    res = diagnose_stock(search_id)
    if res:
        st.success(f"🐶 【{search_id}】財運診斷：{res['判定結果']}")
        st.write(f"💬 **汪汪分析：** {res['汪汪理由']}")
        st.write(f"💰 **目前價格：** {res['現價 (元)']} 元")
        st.write(f"⛔️ **保護主人：** 如果跌破 **{res['跌破這價就跑 (元)']} 元**，汪！快跑！")
    else:
        st.error(f"❌ 【{search_id}】汪！這檔現在不適合撿，可能還在挖骨頭中或跑太遠了。")

st.markdown("---")

# B. 全台股強制掃描區 (加入狗狗元素)
st.subheader("🐾 全台股尋寶雷達：汪！快去挖寶！")
st.write("點擊下方按鈕，讓狗狗們幫妳搜尋全台股的黃金骨頭。")

if st.button("🐕‍🦺 啟動全台股汪汪大掃描！"):
    # 1. 抓取清單 (排除金融股)
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        all_df = pd.read_html(url)[0]
        codes = all_df['有價證券代號及名稱'].str.split('　', expand=True)[0].tolist()
        clean_codes = [c for c in codes if len(str(c)) == 4 and not str(c).startswith('28')]
    except Exception as e:
        st.error(f"狗狗們找不到全台股清單，請稍後再試。錯誤：{e}")
        clean_codes = ["2330", "2317", "2454"] # 備援名單
    
    # 2. 顯示進度
    progress_bar = st.progress(0)
    status_text = st.empty()
    found_list = []
    
    total = len(clean_codes)
    for i, code in enumerate(clean_codes):
        percent = (i + 1) / total
        status_text.text(f"🐾 狗狗們正在努力嗅探中：第 {i+1} / {total} 檔 (已找到 {len(found_list)} 根黃金骨頭)")
        progress_bar.progress(percent)
        
        result = diagnose_stock(code)
        if result:
            found_list.append(result)
            
    status_text.success(f"🎉 汪！狗狗們掃描完成！總共檢查了 {total} 檔股票。")
    
    if found_list:
        st.markdown("### 🏆 汪汪精選：今日黃金骨頭名單！")
        df_result = pd.DataFrame(found_list)
        # 讓狗狗們排好隊，把最安全的排在前面
        df_result = df_result.sort_values(by="乖離率", ascending=True).reset_index(drop=True)
        st.table(df_result)
        st.info("💡 **小撇步：** 乖離率越低，表示狗狗們認為價格越接近安全區喔！")
    else:
        st.warning("嗚...今天狗狗們沒有找到符合安全買點的黃金骨頭，建議主人休息一下。")

st.markdown("---")
st.caption("🐶 本系統為 Christine 專屬設計，僅供學習參考。股市有風險，汪汪選股請謹慎！")