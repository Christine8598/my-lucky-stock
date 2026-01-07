import requests
import os
import json
import time

# 1. 取得 LINE 設定 (由 GitHub Secrets 提供)
LINE_TOKEN = os.environ.get('LINE_TOKEN')
USER_ID = os.environ.get('USER_ID')

def bark_to_line(msg):
    if not LINE_TOKEN or not USER_ID:
        print("⚠️ 缺少 Secret 設定，無法發送 LINE")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload, timeout=10)

def get_price_and_analysis(sid):
    """直接從證交所抓取資料，最穩定不報錯"""
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{sid}.tw|otc_{sid}.tw"
        res = requests.get(url, timeout=10)
        info = res.json()['msgArray'][0]
        # z: 現價, n: 名稱, y: 昨收
        price = float(info['z']) if info['z'] != '-' else float(info['y'])
        return info['n'], price
    except:
        return None, None

if __name__ == "__main__":
    print("🐾 早上 9 點汪汪巡邏開始...")
    
    # 這裡放你想監控的清單，或是從你的記憶檔讀取
    # 範例：監控你 App 裡的庫存
    monitor_list = ["2330", "2317", "2454"] 
    
    report = "⏰【早上 9 點開盤巡邏】\n"
    
    for sid in monitor_list:
        name, price = get_price_and_analysis(sid)
        if name:
            # 這裡可以加入簡單邏輯，例如：
            report += f"\n📍 {name}({sid})\n現價：{price}\n"
            # 你可以在這裡加入「大於某價格就通知買進」的判斷
            
    report += "\n🐾 汪！祝今日財運亨通！"
    bark_to_line(report)
    print("✅ 報告已送出")
