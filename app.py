import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import networkx as nx

st.set_page_config(layout="wide")
st.title("🤝 熟人媒合生態系 - MVP 原型")

# 1. 初始化資料 (增加一個 raw_edges 來存儲單純的字串對)
if 'nodes' not in st.session_state:
    st.session_state.nodes = [
        Node(id="Denny", label="Denny (我)", size=25, color="#FF4B4B"),
        Node(id="爸爸", label="爸爸", size=20),
        Node(id="同事Nick", label="同事 Nick", size=20),
        Node(id="水電王師傅", label="水電王師傅", size=20, color="#1E90FF"),
        Node(id="鋼琴老師", label="鋼琴老師", size=20, color="#1E90FF"),
    ]
    # 用來畫圖的 Edge 物件
    st.session_state.edges = [
        Edge(source="Denny", target="爸爸"),
        Edge(source="Denny", target="同事Nick"),
        Edge(source="爸爸", target="水電王師傅"),
        Edge(source="同事Nick", target="鋼琴老師"),
    ]
    # 用來算演算法的純資料
    st.session_state.raw_edges = [
        ("Denny", "爸爸"), ("Denny", "同事Nick"),
        ("爸爸", "水電王師傅"), ("同事Nick", "鋼琴老師")
    ]

# 2. 側邊欄：新增人脈
with st.sidebar:
    st.header("➕ 擴展人脈網")
    new_person = st.text_input("人名")
    knows_who = st.selectbox("認識誰？", [n.id for n in st.session_state.nodes])
    skill = st.text_input("專業技能 (選填)")
    
    if st.button("加入生態系"):
        if new_person and new_person not in [n.id for n in st.session_state.nodes]:
            label = f"{new_person}\n({skill})" if skill else new_person
            st.session_state.nodes.append(Node(id=new_person, label=label, size=20))
            # 同時更新畫圖用的 Edge 和 算邏輯用的 raw_edges
            st.session_state.edges.append(Edge(source=knows_who, target=new_person))
            st.session_state.raw_edges.append((knows_who, new_person))
            st.rerun()

# 3. 主畫面：搜尋信任路徑
st.subheader("🔍 尋找可信賴的專家")
col1, col2 = st.columns([1, 3])

with col1:
    search_target = st.text_input("輸入你想找的人名", "水電王師傅")
    if st.button("計算信任路徑"):
        # 使用我們儲存的 raw_edges 來建立 NetworkX 圖形
        temp_nx = nx.Graph()
        temp_nx.add_edges_from(st.session_state.raw_edges)
        
        try:
            path = nx.shortest_path(temp_nx, source="Denny", target=search_target)
            st.success("✅ 找到安全路徑！")
            # 用漂亮的方式顯示路徑
            path_str = " ➡️ ".join(path)
            st.info(path_str)
        except Exception as e:
            st.error(f"❌ 目前人脈網尚未連結。")

with col2:
    config = Config(width=800, height=600, directed=False, physics=True, hierarchical=False)
    agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)