"""Hình 3.1 — Kiến trúc hệ thống EpiWeather.
Palette: draw.io default (blue #dae8fc/#6c8ebf, yellow #fff2cc/#d6b656, white #ffffff/#999999).
Chạy: python hinh_3_1_arch.py  ->  hinh_3_1_arch.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

plt.rcParams["font.family"] = "DejaVu Sans"

# ── kích thước ────────────────────────────────────────────────────────────────
FW, FH = 34, 17
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis("off")
fig.patch.set_facecolor("#ffffff")

# ── palette draw.io ───────────────────────────────────────────────────────────
BLUE_F  = "#dae8fc"; BLUE_S  = "#6c8ebf"   # blue boxes
YEL_F   = "#fff2cc"; YEL_S   = "#d6b656"   # yellow boxes
WHT_F   = "#ffffff"; WHT_S   = "#999999"    # white boxes
GRAY_F  = "#f5f5f5"; GRAY_S  = "#cccccc"   # light gray
TEXT    = "#111111"
ARROW   = "#555555"

# ── helpers ───────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc, ec, lw=1.3, z=3):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z)
    ax.add_patch(p)

def section(x, y, w, h, fc, ec, num, title, tfs=10):
    """Khối section: viền + dải header màu đậm hơn."""
    box(x, y, w, h, fc, ec, lw=1.8, z=3)
    # header strip — dùng màu stroke làm nền header
    box(x, y+h-0.58, w, 0.58, ec, ec, lw=0, z=4)
    ax.text(x+w/2, y+h-0.29, title,
            ha="center", va="center", fontsize=tfs,
            color="white", fontweight="bold", zorder=5)
    # số tròn
    circ = plt.Circle((x+0.3, y+h-0.29), 0.22, color="white", zorder=6)
    ax.add_patch(circ)
    ax.text(x+0.3, y+h-0.29, str(num),
            ha="center", va="center", fontsize=8, color=ec, fontweight="bold", zorder=7)

def item(x, y, w, h, fc, ec, title, body="", tfs=9, bfs=8):
    """Sub-box nhỏ bên trong section."""
    box(x, y, w, h, fc, ec, lw=1.0, z=5)
    if body:
        ax.text(x+w/2, y+h*0.65, title,
                ha="center", va="center", fontsize=tfs, color=TEXT,
                fontweight="bold", zorder=6, multialignment="center")
        ax.text(x+w/2, y+h*0.28, body,
                ha="center", va="center", fontsize=bfs, color="#444444",
                zorder=6, multialignment="center")
    else:
        ax.text(x+w/2, y+h/2, title,
                ha="center", va="center", fontsize=tfs, color=TEXT,
                fontweight="bold", zorder=6, multialignment="center")

def sub_section(x, y, w, h, fc, ec, title, tfs=8.5, body="", bfs=8):
    """Sub-box với strip header mỏng."""
    box(x, y, w, h, fc, ec, lw=1.2, z=5)
    box(x, y+h-0.42, w, 0.42, ec, ec, lw=0, z=6)
    ax.text(x+w/2, y+h-0.21, title,
            ha="center", va="center", fontsize=tfs,
            color="white", fontweight="bold", zorder=7)
    if body:
        # căn theo chiều cao thực, không dùng tỷ lệ
        body_y = y + (h - 0.42) / 2
        ax.text(x+w/2, body_y, body,
                ha="center", va="center", fontsize=bfs, color=TEXT,
                zorder=7, multialignment="center")

def badge(x, y, w, h, fc, ec, label, lfs=7.5):
    box(x, y, w, h, fc, ec, lw=0, z=8)
    ax.text(x+w/2, y+h/2, label,
            ha="center", va="center", fontsize=lfs,
            color="white", fontweight="bold", zorder=9)

def t(x, y, s, fs=9, c=TEXT, bold=False, ha="center", va="center", z=6, it=False):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=c,
            fontweight="bold" if bold else "normal",
            fontstyle="italic" if it else "normal", zorder=z,
            multialignment=ha)

def arr(x1, y1, x2, y2, c=ARROW, lw=1.3, ls="-", rad=0, hw=0.18, hl=0.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle=f"->, head_width={hw}, head_length={hl}",
                    color=c, lw=lw, linestyle=ls,
                    connectionstyle=f"arc3,rad={rad}"))

def albl(x, y, s, fs=7.5):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color=ARROW,
            style="italic",
            bbox=dict(fc="white", ec="none", pad=0.5), zorder=9)

# ── layout ────────────────────────────────────────────────────────────────────
GAP  = 0.32
X0   = 0.4
W    = [3.9, 4.1, 4.1, 4.1, 4.8, 3.8]
xs   = []
cur  = X0
for w in W:
    xs.append(cur); cur += w + GAP

YB  = 2.0        # boxes bottom
YT  = 15.4       # boxes top
YH  = YT - YB
IY  = 0.22       # infra bar
IH  = 1.6

# ══════════════════════════════════════════════════════════════════════════════
# TIÊU ĐỀ
# ══════════════════════════════════════════════════════════════════════════════
t(FW/2, 16.55, "EpiWeather System Architecture", fs=20, bold=True, c=TEXT)
t(FW/2, 16.05,
  "End-to-end disease forecasting and risk-alert pipeline  ·  Kiến trúc ba tầng",
  fs=10.5, c="#555555", it=True)

# ══════════════════════════════════════════════════════════════════════════════
# NỀN TẦNG XỬ LÝ (cột 2-4 + viền nhẹ)
# ══════════════════════════════════════════════════════════════════════════════
tx_x = xs[1] - 0.12
tx_w = xs[3] + W[3] - xs[1] + 0.24
box(tx_x, YB-0.12, tx_w, YH+0.24, "#f0f8ff", BLUE_S, lw=1.8, z=1)
# nhãn tầng xử lý — đặt ở góc trên trái của dải nền
ax.text(tx_x+0.15, YT+0.55, "▶  TẦNG XỬ LÝ  (ETL · Feature Engineering · ML Training · FastAPI)",
        ha="left", va="center", fontsize=9, color=BLUE_S,
        fontweight="bold", zorder=3)

# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA SOURCES
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[0], W[0]
section(bx, YB, bw, YH, BLUE_F, BLUE_S, 1, "1. Data Sources")

srcs = [
    ("WHO FluNet",        "CSV · weekly · cúm toàn cầu"),
    ("OpenDengue v1.3",   "sốt xuất huyết\nnhiều quốc gia"),
    ("ERA5 / Copernicus", "17 biến khí hậu lịch sử\n2010–2019 · 1°×1° grid"),
    ("Open-Meteo",        "Archive API · ERA5-based\nscheduled sync"),
]
ys1 = [YB+YH-1.55, YB+YH-3.95, YB+YH-6.55, YB+YH-9.15]
for (name, desc), y in zip(srcs, ys1):
    item(bx+0.2, y-0.75, bw-0.4, 1.3, WHT_F, WHT_S,
         name, desc, tfs=9, bfs=8)

# ══════════════════════════════════════════════════════════════════════════════
# 2. DATA VALIDATION + ETL
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[1], W[1]
section(bx, YB, bw, YH, BLUE_F, BLUE_S, 2, "2. Data Validation + ETL")

etls = [
    ("Quality Checks",    "completeness · ranges\noutliers · duplicates"),
    ("Flu / Dengue ETL",  "clean · merge · deduplicate\nISO week alignment"),
    ("ERA5 ETL",          "download · process\nmaster CSV"),
    ("KD-tree mapping",   "721×1440 → ISO3\ncentroid nearest-neighbor"),
    ("Aggregate weekly",  "1 hàng / quốc gia / tuần"),
]
ys2 = [YB+YH-1.55, YB+YH-3.7, YB+YH-5.9, YB+YH-8.1, YB+YH-10.1]
for (name, desc), y in zip(etls, ys2):
    item(bx+0.2, y-0.65, bw-0.4, 1.2, WHT_F, WHT_S, name, desc, tfs=9, bfs=8)

# ══════════════════════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[2], W[2]
section(bx, YB, bw, YH, YEL_F, YEL_S, 3, "3. Feature Engineering")

feats = [
    ("AR lags",
     "flu: 1–3w · dengue: 6–14w\n+ log1p transform\n+ autoregressive lags"),
    ("Weather lags",
     "flu: temp2m / rhum2m / sol2m\ndengue: temp1m / dewpoint2m\n        / precip6w"),
    ("Endemic channel\nlabeling",
     "Bortman 1999 · WHO EWARS\nbaseline = mean(5y) ± 2σ\nLow / Medium / High"),
]
ys3 = [YB+YH-1.85, YB+YH-5.3, YB+YH-9.0]
for (name, desc), y in zip(feats, ys3):
    item(bx+0.2, y-1.35, bw-0.4, 1.95, WHT_F, WHT_S, name, desc, tfs=9, bfs=8)

t(bx+bw/2, YB+0.55,
  "ML-ready: 10–18 vars / disease", fs=8, c="#666", it=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. ML TRAINING
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[3], W[3]
section(bx, YB, bw, YH, YEL_F, YEL_S, 4, "4. ML Training")

# Regression sub-block
sub_section(bx+0.2, YB+YH-6.18, bw-0.4, 5.6, BLUE_F, BLUE_S,
            "Regression",
            body=("LightGBM  ✓  (cúm)\n"
                  "Random Forest  ✓  (dengue)\n"
                  "XGBoost · Prophet\n\n"
                  "Metrics: RMSE / MAE / R²\n"
                  "walk-forward CV · 6 folds"),
            bfs=8.2)

# Classification sub-block
sub_section(bx+0.2, YB+0.12, bw-0.4, 5.35, YEL_F, YEL_S,
            "Classification",
            body=("XGBClassifier\n"
                  "multi:softprob · 3 lớp\n\n"
                  "Low / Medium / High\n"
                  "(endemic channel label)\n\n"
                  "macro-F1 · AUC OvR\n"
                  "Precision-Recall per class"),
            bfs=8.2)

# ══════════════════════════════════════════════════════════════════════════════
# 5. SERVING & APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[4], W[4]
section(bx, YB, bw, YH, WHT_F, WHT_S, 5, "5. Serving & Application")

# PostgreSQL — Tầng dữ liệu
pg_t = YB+YH-0.65; pg_h = 3.6
sub_section(bx+0.22, pg_t-pg_h, bw-0.44, pg_h, BLUE_F, BLUE_S,
            "PostgreSQL",
            body=("ca bệnh · khí hậu · đặc trưng\n"
                  "dự báo · ngưỡng nguy cơ\n"
                  "metadata · log pipeline\n"
                  "partitioned × ISO3×8\n"
                  "materialized view < 50 ms"),
            bfs=8.2)
badge(bx+0.22, pg_t-pg_h, 2.1, 0.38, BLUE_S, BLUE_S, "Tầng dữ liệu", lfs=7.5)

# FastAPI — Tầng xử lý
fa_t = pg_t-pg_h-0.2; fa_h = 3.7
sub_section(bx+0.22, fa_t-fa_h, bw-0.44, fa_h, BLUE_F, BLUE_S,
            "FastAPI REST API",
            body=("GET /risk-map\n"
                  "POST /predict\n"
                  "GET /history · GET /analytics\n\n"
                  "SQL + materialized view\n"
                  "online p95 < 300 ms\n"
                  "JSON: risk_level · predicted_cases\n"
                  "      calibrated prob_high"),
            bfs=8.0)

# React Frontend — Tầng giao diện
re_t = fa_t-fa_h-0.2; re_h = 2.6
sub_section(bx+0.22, re_t-re_h, bw-0.44, re_h, YEL_F, YEL_S,
            "React Frontend",
            body=("Leaflet choropleth · bản đồ nguy cơ\n"
                  "Recharts trend charts · alert feed\n"
                  "realtime update (flu)"),
            bfs=8.2)
badge(bx+0.22, re_t-re_h, 2.2, 0.38, YEL_S, YEL_S, "Tầng giao diện", lfs=7.5)

# ══════════════════════════════════════════════════════════════════════════════
# 6. MLOps MONITOR
# ══════════════════════════════════════════════════════════════════════════════
bx, bw = xs[5], W[5]
section(bx, YB, bw, YH, YEL_F, YEL_S, 6, "6. MLOps Monitor")

mlops = [
    ("Drift Detection",
     "feature + prediction drift\nalerts & metrics"),
    ("Retraining Trigger",
     "evaluate → approve → retrain\n(planned · scheduled)"),
    ("Prediction Logs",
     "mọi request /predict\nlưu vào PostgreSQL"),
]
ys6 = [YB+YH-1.85, YB+YH-5.3, YB+YH-8.8]
for (name, desc), y in zip(mlops, ys6):
    item(bx+0.2, y-1.35, bw-0.4, 1.95, WHT_F, WHT_S, name, desc, tfs=9, bfs=8)

t(bx+bw/2, YB+0.55,
  "data → feature + prediction\ndrift alerts & metrics",
  fs=8, c="#666", it=True)

# ══════════════════════════════════════════════════════════════════════════════
# 7. DEPLOYMENT — thanh đáy
# ══════════════════════════════════════════════════════════════════════════════
ALL_W = xs[5]+W[5] - xs[0]
box(xs[0], IY, ALL_W, IH, GRAY_F, GRAY_S, lw=1.5, z=2)
t(xs[0]+ALL_W/2, IY+IH-0.28,
  "7. Deployment & CI/CD — Infrastructure Layer  (all services run on this layer)",
  fs=9.5, bold=True, c="#424242")

infra = [
    (xs[0], W[0],            "Docker Compose",          "backend + frontend\n+ postgres"),
    (xs[1], W[1],            "GitHub Actions",           "CI test · DB seed\nweekly sync"),
    (xs[2], W[2]+GAP+W[3],   "Google Colab (training)",  "huấn luyện offline\n2010–2019"),
    (xs[4], W[4],            "APScheduler",              "batch jobs\ncập nhật định kỳ"),
    (xs[5], W[5],            "Monitoring Stack",         "logs · drift alerts\n(planned)"),
]
for ix, iw, name, desc in infra:
    ih2 = IH - 0.42
    box(ix+0.12, IY+0.1, iw-0.24, ih2, WHT_F, WHT_S, lw=0.9, z=4)
    t(ix+iw/2, IY+0.1+ih2*0.64, name, fs=8.5, bold=True, c=TEXT, z=5)
    t(ix+iw/2, IY+0.1+ih2*0.25, desc, fs=7.8, c="#555",  z=5)

# đường nối infra
for i in range(6):
    cx = xs[i]+W[i]/2
    ax.plot([cx, cx], [IY+IH, YB], color=GRAY_S, lw=0.8, ls="--", zorder=1)

# ══════════════════════════════════════════════════════════════════════════════
# MŨI TÊN LUỒNG CHÍNH
# ══════════════════════════════════════════════════════════════════════════════
MY = YB + YH * 0.52

# 1→2  2→3  3→4  4→5
pairs = [(0,1,BLUE_S,"raw weekly"), (1,2,BLUE_S,"master CSV"),
         (2,3,YEL_S,"features"),   (3,4,WHT_S,"model .pkl")]
for i, j, c, lbl in pairs:
    arr(xs[i]+W[i], MY, xs[j]-0.04, MY, c)
    albl((xs[i]+W[i]+xs[j])/2, MY+0.4, lbl)

# ETL → PostgreSQL (store)
pg_cx = xs[4]+0.22+(W[4]-0.44)/2
pg_my = pg_t - pg_h/2
ax.annotate("",
            xy=(pg_cx-0.3, pg_my),
            xytext=(xs[1]+W[1]*0.55, YB+0.7),
            arrowprops=dict(arrowstyle="->, head_width=0.15, head_length=0.18",
                            color=BLUE_S, lw=1.2,
                            connectionstyle="arc3,rad=-0.18"))
albl((xs[1]+W[1]*0.55+pg_cx-0.3)/2, YB+0.28, "store → PostgreSQL")

# FastAPI ↔ PG
ax.annotate("",
            xy=(xs[4]+W[4]-0.4, pg_t-pg_h+0.25),
            xytext=(xs[4]+W[4]-0.4, fa_t-0.2),
            arrowprops=dict(arrowstyle="<->, head_width=0.13, head_length=0.14",
                            color=BLUE_S, lw=1.1))
albl(xs[4]+W[4]-0.05, (pg_t-pg_h+fa_t)/2, "query", fs=7.5)

# FastAPI → React
arr(xs[4]+W[4]-0.4, fa_t-fa_h-0.02,
    xs[4]+W[4]-0.4, re_t-0.02, WHT_S)
albl(xs[4]+W[4]+0.1, (fa_t-fa_h+re_t)/2, "JSON", fs=7.5)

# API → MLOps
fa_mid = fa_t - fa_h/2
arr(xs[4]+W[4], fa_mid, xs[5]-0.04, fa_mid, YEL_S, ls="--")
albl((xs[4]+W[4]+xs[5])/2, fa_mid+0.35, "prediction logs")

# MLOps → Training  retraining trigger
arr(xs[5]+W[5]/2, YT-0.35, xs[3]+W[3]/2, YT-0.35, YEL_S, ls="--")
albl((xs[3]+W[3]/2+xs[5]+W[5]/2)/2, YT+0.05,
     "retraining trigger (drift detected)")

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════
legend_h = [
    mpatches.Patch(fc=BLUE_F, ec=BLUE_S, label="Data / Tầng dữ liệu"),
    mpatches.Patch(fc=YEL_F,  ec=YEL_S,  label="ML / MLOps / Tầng giao diện"),
    mpatches.Patch(fc=WHT_F,  ec=WHT_S,  label="Serving (FastAPI)"),
    mpatches.Patch(fc=GRAY_F, ec=GRAY_S, label="Tầng triển khai & CI/CD"),
    Line2D([0],[0], color=ARROW, lw=1.3, label="Luồng dữ liệu"),
    Line2D([0],[0], color=YEL_S, lw=1.2, ls="--", label="Trigger / Log"),
]
ax.legend(handles=legend_h, loc="lower right",
          bbox_to_anchor=(1.0, 0.0), fontsize=8.5, framealpha=0.95,
          ncol=3, handlelength=1.6, handleheight=1.0, borderpad=0.7)

# ══════════════════════════════════════════════════════════════════════════════
out = r"f:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN\docs\figures\hinh_3_1_arch.png"
plt.tight_layout(pad=0)
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
plt.close()
print("OK ->", out)
