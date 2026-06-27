"""
Tái tạo sơ đồ luồng xử lý request (Hình 3.9) — hinh_3_9_request_flow.svg + .png
Chạy lại script này bất cứ khi nào cần cập nhật nội dung node.
"""
import os
import graphviz
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "docs" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Đường dẫn graphviz trên Windows
GRAPHVIZ_BIN = r"C:\Program Files\Graphviz\bin"
os.environ["PATH"] = GRAPHVIZ_BIN + os.pathsep + os.environ.get("PATH", "")

g = graphviz.Digraph(
    "request_flow",
    graph_attr={
        "rankdir": "TB",
        "splines": "polyline",
        "nodesep": "0.5",
        "ranksep": "0.55",
        "bgcolor": "white",
        "fontname": "Arial",
    },
    node_attr={"fontname": "Arial", "fontsize": "11"},
    edge_attr={"fontname": "Arial", "fontsize": "9"},
)

# ── Start / End ──────────────────────────────────────────────
g.node(
    "start",
    label="Client gửi request\nGET /forecast/{disease}/{iso3}",
    shape="rectangle",
    style="filled",
    fillcolor="#4a7db5",
    fontcolor="white",
    color="none",
)
g.node(
    "end_node",
    label="Client nhận response",
    shape="rectangle",
    style="filled",
    fillcolor="#4a7db5",
    fontcolor="white",
    color="none",
)

# ── Process nodes ─────────────────────────────────────────────
PROC_ATTRS = dict(
    shape="rectangle",
    style="filled,rounded",
    fillcolor="#eaf1fb",
    color="#4a7db5",
    penwidth="1.2",
)

g.node("check_cache",        label="Tìm kết quả trong\nbảng predictions",                  **PROC_ATTRS)
g.node("return_precomputed", label="Đọc từ bảng predictions\n(một câu SELECT)",             **PROC_ATTRS)
g.node("read_snapshot",      label="Đọc vector đặc trưng\ntừ feature_snapshots",            **PROC_ATTRS)
g.node("call_model",         label="Gọi model.predict()\ncho h = 1, 2, 3, 4",               **PROC_ATTRS)
g.node("apply_threshold",    label="Phân loại mức nguy cơ\nqua XGBClassifier (predict_proba)", **PROC_ATTRS)
g.node("add_coverage",       label="Gắn trường data_coverage\n(cảnh báo nếu ngoại suy ngoài 2010–2019)", **PROC_ATTRS)
g.node("return_json",        label="Trả về JSON response\n(horizon, week, cases, risk, r2_cv)", **PROC_ATTRS)

# ── Decision diamond ──────────────────────────────────────────
g.node(
    "decision",
    label="Đã có\ntrong cache?",
    shape="diamond",
    style="filled",
    fillcolor="#f5f0e8",
    color="#b8860b",
    penwidth="1.4",
)

# ── Edges ─────────────────────────────────────────────────────
g.edge("start",             "check_cache")
g.edge("check_cache",       "decision")
g.edge("decision",          "return_precomputed", label=" Có  ", color="#2e7d32", fontcolor="#2e7d32")
g.edge("decision",          "read_snapshot",      label=" Chưa có  ", color="#c62828", fontcolor="#c62828")
g.edge("read_snapshot",     "call_model")
g.edge("call_model",        "apply_threshold")
g.edge("apply_threshold",   "add_coverage")
g.edge("add_coverage",      "return_json")
g.edge("return_json",       "end_node")
g.edge("return_precomputed","end_node")

# ── Render ────────────────────────────────────────────────────
out_base = str(OUT_DIR / "hinh_3_9_request_flow")
g.render(filename=out_base, format="png", cleanup=True)
g.render(filename=out_base, format="svg", cleanup=True)
print(f"OK — {out_base}.png + .svg")
