import matplotlib.pyplot as plt
import networkx as nx

def draw_topology(graph, title, pos=None):
    plt.figure(figsize=(8, 6))
    nx.draw_networkx(graph, pos=pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=12, font_weight='bold', edge_color='gray')
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.show()

# 1. Bus Topology
bus = nx.Graph()
bus.add_nodes_from(["Bus1", "Bus2", "Bus3", "Bus4", "Bus5", "NodeA", "NodeB", "NodeC"])
bus.add_edges_from([("Bus1", "Bus2"), ("Bus2", "Bus3"), ("Bus3", "Bus4"), ("Bus4", "Bus5")])
bus.add_edges_from([("NodeA", "Bus2"), ("NodeB", "Bus3"), ("NodeC", "Bus4")])
draw_topology(bus, "Bus Topology")

# 2. Star Topology
star = nx.Graph()
nodes = ["Center", "A", "B", "C", "D"]
star.add_nodes_from(nodes)
star.add_edges_from([("Center", n) for n in nodes if n != "Center"])
draw_topology(star, "Star Topology")

# 3. Ring Topology
ring = nx.Graph()
ring_nodes = ["A", "B", "C", "D", "E"]
ring.add_nodes_from(ring_nodes)
ring.add_edges_from([(ring_nodes[i], ring_nodes[(i+1) % len(ring_nodes)]) for i in range(len(ring_nodes))])
draw_topology(ring, "Ring Topology")

# 4. Mesh Topology
mesh = nx.Graph()
mesh_nodes = ["A", "B", "C", "D"]
mesh.add_nodes_from(mesh_nodes)
mesh.add_edges_from([(a, b) for idx, a in enumerate(mesh_nodes) for b in mesh_nodes[idx+1:]])
draw_topology(mesh, "Mesh Topology")

# 5. Tree Topology
tree = nx.Graph()
tree.add_edges_from([
    ("Root", "A"), ("Root", "B"),
    ("A", "A1"), ("A", "A2"),
    ("B", "B1"), ("B", "B2")
])
draw_topology(tree, "Tree Topology")

# 6. Hybrid Topology (Star + Ring)
hybrid = nx.Graph()
hybrid.add_edges_from([
    ("Center", "A"), ("Center", "B"), ("Center", "C"),
    ("C", "D"), ("D", "E"), ("E", "C")  # Ring on one branch
])
draw_topology(hybrid, "Hybrid Topology")

# 7. Point-to-Point
p2p = nx.Graph()
p2p.add_edge("Device1", "Device2")
draw_topology(p2p, "Point-to-Point Topology")
