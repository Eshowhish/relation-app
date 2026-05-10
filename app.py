import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import networkx as nx
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(layout="wide")
st.title("🤝 熟人媒合生態系 - 持久化測試版")

# --- 1. 資料庫連結設定 ---
# 在 Streamlit Cloud 部署時，需在 Secrets 設定中加入 Google Sheets 的 URL
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """從 Google Sheets 讀取資料，若失敗則回傳預設值"""
    try:
        nodes_df = conn.read(worksheet="nodes")
        edges_df = conn.read(worksheet="edges")
        return nodes_df, edges_df
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- 2. 初始化 Session State (將資料存入記憶體以供即時互動) ---
if 'initialized' not in st.session_state:
    nodes_df, edges_df = load_data()
    
    # 如果資料庫有東西，就用資料庫的；否則用預設初始資料
    if not nodes_df.empty:
        st.session_state.nodes = [Node(id=row['id'], label=row['label'], size=20) for _, row in nodes_df.iterrows()]
        st.session_state.edges = [Edge(source=row['source'], target=row['target']) for _, row in edges_df.iterrows()]
        st.session_state.raw_edges = [(row['source'], row['target']) for _, row in edges_df.iterrows()]
    else:
        # 預設初始資料 (第一次執行時使用)
        st.session_state.nodes = [
            Node(id="Denny", label="Denny (我)", size=25, color="#FF4B4B"),
            Node(id="爸爸", label="爸爸", size=20),
            Node(id="同事Nick", label="同事 Nick", size=20),
        ]
        st.session_state.edges = [Edge(source="Denny", target="爸爸"), Edge(source="Denny", target="同事Nick")]
        st.session_state.raw_edges = [("Denny", "爸爸"), ("Denny", "同事Nick")]
    
    st.session_state.initialized = True

def save_to_sheets():
    """將目前的狀態寫回 Google Sheets"""
    # 轉換 nodes
    n_data = [{"id": n.id, "label": n.label} for n in st.session_state.nodes]
    # 轉換 edges
    e_data = [{"source": e[0], "target": e[1]} for e in st.session_state.raw_edges]
    
    conn.update(worksheet="nodes", data=pd.DataFrame(n_data))
    conn.update(worksheet="edges", data=pd.DataFrame(e_data))
    st.toast("✅ 資料已同步至 Google Sheets")

# --- 3. 側邊欄：管理功能 ---
with st.sidebar:
    st.header("➕ 擴展人脈網")
    new_person = st.text_input("人名")
    knows_who = st.selectbox("認識誰？", [n.id for n in st.session_state.nodes])
    skill = st.text_input("專業技能 (選填)")
    
    if st.button("加入生態系並儲存"):
        if new_person and new_person not in [n.id for n in st.session_state.nodes]:
            label = f"{new_person}\n({skill})" if skill else new_person
            st.session_state.nodes.append(Node(id=new_person, label=label, size=20))
            st.session_state.edges.append(Edge(source=knows_who, target=new_person))
            st.session_state.raw_edges.append((knows_who, new_person))
            save_to_sheets() # 寫回資料庫
            st.rerun()

    st.markdown("---")
    st.header("🗑️ 管理人脈網")
    delete_person = st.selectbox("選擇要刪除的人", [n.id for n in st.session_state.nodes if n.id != "Denny"])
    if st.button("刪除此人"):
        st.session_state.nodes = [n for n in st.session_state.nodes if n.id != delete_person]
        st.session_state.raw_edges = [re for re in st.session_state.raw_edges if re[0] != delete_person and re[1] != delete_person]
        st.session_state.edges = [Edge(source=re[0], target=re[1]) for re in st.session_state.raw_edges]
        save_to_sheets() # 寫回資料庫
        st.rerun()

# --- 4. 主畫面：搜尋與圖形 ---
st.subheader("🔍 尋找可信賴的專家")
col1, col2 = st.columns([1, 3])

with col1:
    search_target = st.text_input("輸入你想找的人名", "爸爸")
    if st.button("計算信任路徑"):
        temp_nx = nx.Graph()
        temp_nx.add_edges_from(st.session_state.raw_edges)
        try:
            path = nx.shortest_path(temp_nx, source="Denny", target=search_target)
            st.success("✅ 找到安全路徑！")
            st.info(" ➡️ ".join(path))
        except:
            st.error("❌ 目前人脈網尚未連結。")

with col2:
    config = Config(width=800, height=600, directed=False, physics=True, hierarchical=False)
    agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)