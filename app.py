import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import networkx as nx
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(layout="wide")
st.title("🤝 熟人媒合生態系 - 生態觀測站")

# --- 1. 資料庫連結設定 (僅讀取模式) ---
# Secrets 中只需 spreadsheet 網址即可，不需複雜金鑰
conn = st.connection("gsheets", type=GSheetsConnection)

def load_form_data():
    """從 Google 表單連結的試算表讀取資料"""
    try:
        # ttl=60 代表每 60 秒緩存失效，會去抓一次新資料
        df = conn.read(ttl=60) 
        return df
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return pd.DataFrame()

# --- 2. 建立人脈圖譜邏輯 ---
df = load_form_data()

# 初始化節點與連結
nodes = [Node(id="Denny", label="Denny (我)", size=25, color="#FF4B4B")]
edges = []
raw_edges = []

# 建立基礎關係 (你可以根據需求手動預設幾個人)
base_people = ["爸爸", "同事Nick"]
for person in base_people:
    nodes.append(Node(id=person, label=person, size=20))
    edges.append(Edge(source="Denny", target=person))
    raw_edges.append(("Denny", person))

# --- 3. 自動處理表單傳入的新人脈 ---
# 假設你的 Google 表單欄位名稱分別為: "姓名", "推薦人", "專長"
if not df.empty:
    for _, row in df.iterrows():
        # 確保資料是字串且處理空值
        name = str(row.get('你的名字', '')).strip()
        referrer = str(row.get('你認識的人', '')).strip()
        skill = str(row.get('你的專長', ''))

        if name and name != 'nan':
            # 如果這個人還沒在節點裡，就加入他
            if name not in [n.id for n in nodes]:
                display_label = f"{name}\n({skill})" if skill != 'nan' and skill else name
                nodes.append(Node(id=name, label=display_label, size=20))
            
            # 如果推薦人存在，建立與推薦人的連結
            if referrer and referrer != 'nan':
                # 防止重複建立連結
                if (referrer, name) not in raw_edges and (name, referrer) not in raw_edges:
                    raw_edges.append((referrer, name))
                    edges.append(Edge(source=referrer, target=name))

# --- 4. 側邊欄：引導與管理 ---
with st.sidebar:
    st.header("📢 擴展生態系")
    st.write("目前改用 Google 表單收集資料，確保資料永不遺失！")
    
    # 這裡貼上你的 Google 表單網址
    st.link_button("👉 填寫人脈問卷", "https://docs.google.com/forms/d/e/1FAIpQLSc8RqsHcLMk5q2KPux5yfAfs4Ls2IdYwxzDSmVuHx9QNw4iZA/viewform?usp=publish-editor")
    
    st.divider()
    st.info("💡 提示：在表單提交後，約一分鐘後重新整理網頁即可看到新節點。")

# --- 5. 主畫面：搜尋功能 ---
st.subheader("🔍 尋找可信賴的專家")
col1, col2 = st.columns([1, 3])

with col1:
    search_target = st.text_input("輸入你想找的人名", "爸爸")
    if st.button("計算信任路徑"):
        # 建立 NetworkX 演算法模型
        temp_nx = nx.Graph()
        temp_nx.add_edges_from(raw_edges)
        
        try:
            path = nx.shortest_path(temp_nx, source="Denny", target=search_target)
            st.success("✅ 找到安全路徑！")
            st.info(" ➡️ ".join(path))
        except:
            st.error("❌ 目前人脈網尚未與此人建立連結。")

with col2:
    # 繪製圖形
    config = Config(width=800, height=600, directed=False, physics=True, hierarchical=False)
    agraph(nodes=nodes, edges=edges, config=config)