"""
회로도 및 블록 다이어그램 자동 생성 서비스
"""
import os
import uuid
import json
import matplotlib
matplotlib.use('Agg')  # GUI 없이 실행
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

OUTPUT_DIR = "/data/generated/diagrams"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Node-RED 블록 다이어그램 생성 ─────────────────────────

def generate_nodered_diagram(nodes: list, connections: list, title: str = "Node-RED Flow") -> str:
    """
    nodes: [{"id":"1","name":"Inject","type":"inject","x":0,"y":0}, ...]
    connections: [{"from":"1","to":"2"}, ...]
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_xlim(-0.5, 10)
    ax.set_ylim(-0.5, len(nodes) * 1.5 + 0.5)
    ax.axis('off')

    # 노드 타입별 색상
    NODE_COLORS = {
        "inject":    {"bg": "#8B4513", "border": "#A0522D", "text": "white"},
        "function":  {"bg": "#DAA520", "border": "#FFD700", "text": "black"},
        "switch":    {"bg": "#DAA520", "border": "#FFD700", "text": "black"},
        "change":    {"bg": "#DAA520", "border": "#FFD700", "text": "black"},
        "debug":     {"bg": "#2E8B57", "border": "#3CB371", "text": "white"},
        "http in":   {"bg": "#4169E1", "border": "#6495ED", "text": "white"},
        "http out":  {"bg": "#4169E1", "border": "#6495ED", "text": "white"},
        "mqtt in":   {"bg": "#9370DB", "border": "#BA55D3", "text": "white"},
        "mqtt out":  {"bg": "#9370DB", "border": "#BA55D3", "text": "white"},
        "output":    {"bg": "#2E8B57", "border": "#3CB371", "text": "white"},
        "default":   {"bg": "#4682B4", "border": "#5F9EA0", "text": "white"},
    }

    node_positions = {}

    # 노드 자동 배치 (x, y 없으면 자동)
    for i, node in enumerate(nodes):
        x = node.get("x", i % 4 * 2.5)
        y = node.get("y", (i // 4) * 1.5)
        node_positions[node["id"]] = (x, y)

        ntype = node.get("type", "default").lower()
        colors = NODE_COLORS.get(ntype, NODE_COLORS["default"])

        # 노드 박스
        box = FancyBboxPatch(
            (x - 0.9, y - 0.3), 1.8, 0.6,
            boxstyle="round,pad=0.05",
            facecolor=colors["bg"],
            edgecolor=colors["border"],
            linewidth=2,
            zorder=3
        )
        ax.add_patch(box)

        # 연결 포인트 (왼쪽)
        ax.plot(x - 0.9, y, 'o', color='#cccccc', markersize=5, zorder=4)
        # 연결 포인트 (오른쪽)
        ax.plot(x + 0.9, y, 'o', color='#cccccc', markersize=5, zorder=4)

        # 노드 이름
        ax.text(x, y, node["name"],
                ha='center', va='center',
                fontsize=8, fontweight='bold',
                color=colors["text"], zorder=5)

        # 타입 라벨 (작게)
        ax.text(x, y - 0.22, f'[{ntype}]',
                ha='center', va='center',
                fontsize=6, color='#aaaaaa', zorder=5)

    # 연결선 그리기
    for conn in connections:
        if conn["from"] in node_positions and conn["to"] in node_positions:
            x1, y1 = node_positions[conn["from"]]
            x2, y2 = node_positions[conn["to"]]

            # 베지어 곡선으로 연결
            ax.annotate("",
                xy=(x2 - 0.9, y2),
                xytext=(x1 + 0.9, y1),
                arrowprops=dict(
                    arrowstyle="->",
                    color="#aaaaaa",
                    lw=1.5,
                    connectionstyle="arc3,rad=0.1"
                ),
                zorder=2
            )

            # 연결 라벨
            if "label" in conn:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                ax.text(mx, my + 0.1, conn["label"],
                        ha='center', fontsize=6,
                        color='#888888', zorder=5)

    # 제목
    ax.text(5, len(nodes) * 1.5 + 0.2, title,
            ha='center', va='center',
            fontsize=14, fontweight='bold',
            color='white')

    # 저장
    filename = f"nodered_{uuid.uuid4()}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor='#1a1a2e', edgecolor='none')
    plt.close()

    return f"/generated/diagrams/{filename}"


# ── 회로도 생성 ───────────────────────────────────────────

def generate_circuit_diagram(components: list, connections: list, title: str = "회로도") -> str:
    """
    components: [{"id":"R1","type":"resistor","value":"10kΩ","x":1,"y":2}, ...]
    connections: [{"from":"R1","to":"C1"}, ...]
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_facecolor('#0a0a0a')
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_xlim(-1, 10)
    ax.set_ylim(-1, 8)
    ax.axis('off')

    COMP_COLORS = {
        "resistor":   "#FF6B6B",
        "capacitor":  "#4ECDC4",
        "led":        "#FFE66D",
        "transistor": "#A8E6CF",
        "ic":         "#88D8B0",
        "power":      "#FF8B94",
        "ground":     "#B0B0B0",
        "default":    "#778CA3",
    }

    COMP_SYMBOLS = {
        "resistor":   "▭",
        "capacitor":  "⊣⊢",
        "led":        "▷|",
        "transistor": "⊿",
        "ic":         "▬",
        "power":      "⊕",
        "ground":     "⏚",
        "default":    "○",
    }

    comp_positions = {}

    for comp in components:
        x = comp.get("x", 0)
        y = comp.get("y", 0)
        comp_positions[comp["id"]] = (x, y)

        ctype = comp.get("type", "default").lower()
        color = COMP_COLORS.get(ctype, COMP_COLORS["default"])
        symbol = COMP_SYMBOLS.get(ctype, COMP_SYMBOLS["default"])

        # 부품 박스
        if ctype == "ic":
            box = FancyBboxPatch(
                (x - 0.6, y - 0.4), 1.2, 0.8,
                boxstyle="round,pad=0.05",
                facecolor='#1a1a2e',
                edgecolor=color,
                linewidth=2, zorder=3
            )
        else:
            box = FancyBboxPatch(
                (x - 0.4, y - 0.25), 0.8, 0.5,
                boxstyle="round,pad=0.05",
                facecolor='#1a1a2e',
                edgecolor=color,
                linewidth=2, zorder=3
            )
        ax.add_patch(box)

        # 부품 ID
        ax.text(x, y + 0.1, comp["id"],
                ha='center', va='center',
                fontsize=9, fontweight='bold',
                color=color, zorder=5)

        # 부품 값
        if "value" in comp:
            ax.text(x, y - 0.12, comp["value"],
                    ha='center', va='center',
                    fontsize=7, color='#888888', zorder=5)

        # 연결 포트
        ax.plot(x - 0.4, y, 'o', color=color, markersize=4, zorder=4)
        ax.plot(x + 0.4, y, 'o', color=color, markersize=4, zorder=4)

    # 연결선
    for conn in connections:
        if conn["from"] in comp_positions and conn["to"] in comp_positions:
            x1, y1 = comp_positions[conn["from"]]
            x2, y2 = comp_positions[conn["to"]]

            # L자형 배선
            mid_x = (x1 + x2) / 2
            ax.plot([x1 + 0.4, mid_x, mid_x, x2 - 0.4],
                    [y1, y1, y2, y2],
                    color='#00FF00', linewidth=1.5,
                    solid_capstyle='round', zorder=2)

    # 제목
    ax.text(4.5, 7.5, title,
            ha='center', va='center',
            fontsize=14, fontweight='bold', color='white')

    # 범례
    legend_items = []
    for ctype, color in COMP_COLORS.items():
        if ctype != "default":
            patch = mpatches.Patch(color=color, label=ctype)
            legend_items.append(patch)

    ax.legend(handles=legend_items[:6],
              loc='lower right',
              facecolor='#1a1a2e',
              edgecolor='#444444',
              labelcolor='white',
              fontsize=7)

    filename = f"circuit_{uuid.uuid4()}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor='#0a0a0a', edgecolor='none')
    plt.close()

    return f"/generated/diagrams/{filename}"


# ── AI가 텍스트에서 자동으로 다이어그램 파싱 ───────────────

async def auto_generate_from_response(ai_response: str, diagram_type: str = "auto") -> str | None:
    """AI 응답에서 다이어그램 데이터 추출 후 자동 생성"""
    import re

    # JSON 블록 추출
    json_match = re.search(r'```(?:json|diagram)\s*(.*?)\s*```', ai_response, re.DOTALL)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group(1))

        if diagram_type == "nodered" or data.get("type") == "nodered":
            return generate_nodered_diagram(
                data.get("nodes", []),
                data.get("connections", []),
                data.get("title", "Node-RED Flow")
            )
        elif diagram_type == "circuit" or data.get("type") == "circuit":
            return generate_circuit_diagram(
                data.get("components", []),
                data.get("connections", []),
                data.get("title", "회로도")
            )
    except Exception as e:
        print(f"다이어그램 생성 오류: {e}")
        return None