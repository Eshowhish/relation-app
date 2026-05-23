import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import networkx as nx
import pandas as pd
import json
import urllib.request

st.set_page_config(layout="wide")
st.title("🤝 熟人媒合生態系 - AI 智能擴展版")

# --- 1. AI 文字解析核心邏輯 (使用免費的 Gemini API) ---
def analyze_text_with_ai(user_text, api_key):
    """將使用者的隨性描述，透過 AI 轉化為標準的 Node 與 Edge JSON 格式"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 建立嚴格的 Prompt，強迫 AI 只能回傳標準 JSON
    prompt = f"""
    你是一個專門分析人關係與專長的 AI。請分析以下這段文字，並萃取取出裡面提到的人名（Nodes）以及人與人之間的認識關係（Edges）。
    
    【文字內容】: "{user_text}"
    
    【輸出規範】:
    請「嚴格」只回傳一個 JSON 物件，不要包含任何 markdown 語法（例如 ```json 標籤），格式如下：
    {{
        "nodes": [
            {{"id": "人名", "skill": "他的專業技能，若文字沒提到則留空字串""}}
        ],
        "edges": [
            {{"source": "認識的人A", "target": "認識的人B"}}
        ]
    }}
    
    注意：
    1. edges 的 source 和 target 必須出現在 nodes 的 id 中，或是原本系統已存在的名字。
    2. 關係是雙向的，一對關係只需要建立一筆 edge 即可。
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text_response)
    except Exception as e:
        st.error(f"AI 解析失敗，請檢查 API Key 或網路連線: {e}")
        return None

# --- 2. 初始化 Session State ---
# 為了能即時看到 AI 加進來的圓點，我們使用 Session State 來維持狀態
if 'nodes_dict' not in st.session_state:
    # 預設基礎人脈資料庫
    st.session_state.nodes_dict = {
        "Denny": "Denny (我)",
        "爸爸": "爸爸",
        "同事Nick": "同事 Nick",
        "水電王師傅": "水電王師傅",
        "鋼琴老師": "鋼琴老師",
        "室內設計師": "室內設計師"
    }
    st.session_state.raw_edges = [
        ("Denny", "爸爸"), 
        ("Denny", "同事Nick"),
        ("爸爸", "水電王師傅"),
        ("同事Nick", "鋼琴老師"),
        ("鋼琴老師", "室內設計師")
    ]

# --- 3. 側邊欄：AI 智能輸入區 ---
with st.sidebar:
    st.header("🤖 AI 語意匯入人脈")
    st.write("不需填問卷！直接貼上對話紀錄或隨性打一段話：")
    
    # 讓使用者在網頁上填入自己的 Gemini API 金鑰
    gemini_key = st.text_input("輸入您的 Gemini API Key", type="password", help="請至 Google AI Studio 免費申請")
    
    user_input = st.text_area(
        "輸入人脈描述：", 
        placeholder="例如：我爸是水電王師傅。上次 Nick 介紹的鋼琴老師很有 Patience，對了，鋼琴老師還認識一位室內設計師！",
        height=150
    )
    
    if st.button("讓 AI 解析並加入網圖"):
        if not gemini_key:
            st.error("🔑 請先輸入 Gemini API Key 才能使用 AI 解析功能！")
        elif user_input:
            with st.spinner("AI 正在解析人脈網絡..."):
                ai_result = analyze_text_with_ai(user_input, gemini_key)
                
                if ai_result:
                    # 處理 AI 解析出的節點
                    for n in ai_result.get("nodes", []):
                        n_id = n["id"].strip()
                        n_skill = n.get("skill", "").strip()
                        if n_id and n_id not in st.session_state.nodes_dict:
                            st.session_state.nodes_dict[n_id] = f"{n_id}\n({n_skill})" if n_skill else n_id
                    
                    # 處理 AI 解析出的關係
                    for e in ai_result.get("edges", []):
                        src = e["source"].strip()
                        tgt = e["target"].strip()
                        if src Opp tgt: # 避免自連
                            # 確保雙向關係不重複加入
                            if (src, tgt) not in st.session_state.raw_edges and (tgt, src) not in st.session_state.raw_edges:
                                st.session_state.raw_edges.append((src, tgt))
                    
                    st.success("🎉 AI 成功解析！已動態動態更新圖譜。")
                    st.rerun()

# --- 4. 轉換為 agraph 所需的視覺化物件 ---
nodes = []
for n_id, n_label in st.session_state.nodes_dict.items():
    if n_id == "Denny":
        nodes.append(Node(id=n_id, label=n_label, size=25, color="#FF4B4B"))
    elif "師" in n_id or "老師" in n_id: # 簡單高亮專家節點
        nodes.append(Node(id=n_id, label=n_label, size=20, color="#1E90FF"))
    else:
        nodes.append(Node(id=n_id, label=n_label, size=20))

edges = [Edge(source=src, target=tgt) for src, tgt in st.session_state.raw_edges]

# --- 5. 主畫面：搜尋功能 ---
st.subheader("🔍 尋找可信賴的專家")
col1, col2 = st.columns([1, 3])

with col1:
    search_target = st.text_input("輸入你想找的人名或關鍵字", "室內設計師")
    if st.button("計算信任路徑"):
        # 建立 NetworkX 演算法模型
        temp_nx = nx.Graph()
        temp_nx.add_edges_from(st.session_state.raw_edges)
        
        try:
            path = nx.shortest_path(temp_nx, source="Denny", target=search_target)
            st.balloons()
            st.success("✅ 找到安全路徑！")
            st.info(" ➡️ ".join(path))
        except:
            st.error("❌ 目前人脈網尚未與此人建立連結。")

with col2:
    # 繪製圖形
    config = Config(width=800, height=600, directed=False, physics=True, hierarchical=False)
    agraph(nodes=nodes, edges=edges, config=config)