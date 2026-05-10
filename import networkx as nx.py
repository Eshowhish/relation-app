import networkx as nx

# 建立圖形
G = nx.Graph()

# 模擬你的初期資料獲取：家人、同事、朋友
# 關係路徑：(起點, 終點, 權重/親疏距離)
G.add_edge("Denny", "爸爸", weight=1)
G.add_edge("Denny", "同事Nick", weight=1)
G.add_edge("爸爸", "水電王師傅", weight=1)
G.add_edge("同事Nick", "鋼琴老師", weight=1)
G.add_edge("鋼琴老師", "室內設計師", weight=1)

# 搜尋目標
target = "室內設計師"

try:
    # 尋找最短信任路徑
    path = nx.shortest_path(G, source="Denny", target=target)
    print(f"✅ 找到目標！從你到【{target}】的信任鏈為：")
    print(f" 👉 {' -> '.join(path)}")
except nx.NetworkXNoPath:
    print("❌ 抱歉，目前的人脈網還沒連到這位專家。")