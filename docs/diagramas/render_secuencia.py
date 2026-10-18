"""Renderiza el subconjunto de Mermaid usado en docs/diagramas/*.mmd a PNG con matplotlib.
Uso: python docs/diagramas/render_secuencia.py   (no requiere Chrome ni mermaid-cli)."""
import re, textwrap, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def parsear(txt):
    parts, items = {}, []
    for raw in txt.splitlines():
        l = raw.strip()
        if not l or l.startswith("sequenceDiagram") or l == "autonumber":
            continue
        m = re.match(r"(participant|actor)\s+(\w+)\s+as\s+(.+)", l)
        if m:
            parts[m[2]] = (m[3], m[1]); continue
        m = re.match(r"(loop|alt|else|opt)\b\s*(.*)", l)
        if m:
            items.append((m[1], m[2])); continue
        if l == "end":
            items.append(("end", "")); continue
        m = re.match(r"Note over ([\w,]+):\s*(.*)", l)
        if m:
            items.append(("note", m[1].split(","), m[2])); continue
        m = re.match(r"(\w+)(-->>|->>|--x|-x)(\w+):\s*(.*)", l)
        if m:
            items.append(("msg", m[1], m[2], m[3], m[4]))
    return parts, items

def render(ruta):
    parts, items = parsear(Path(ruta).read_text(encoding="utf-8"))
    ids = list(parts); xs = {p: i * 1.75 for i, p in enumerate(ids)}
    n = sum(1 for it in items if it[0] in ("msg", "note", "loop", "alt", "else")) 
    alto = 1.4 + n * 0.33
    fig, ax = plt.subplots(figsize=(1.75 * len(ids) + 0.6, alto))
    ax.set_xlim(-1.0, xs[ids[-1]] + 1.0); ax.set_ylim(-alto + 0.9, 1.0); ax.axis("off")
    y, num, pila = 0.0, 0, []
    for p in ids:
        et, tipo = parts[p]
        txt = "\n".join(textwrap.wrap(et, 17))
        ax.add_patch(Rectangle((xs[p] - 0.82, 0.05), 1.64, 0.7, fc="#FFE4B5" if tipo == "actor" else "#DCE9F7", ec="black", lw=0.8))
        ax.text(xs[p], 0.4, txt, ha="center", va="center", fontsize=7.2, weight="bold")
    y = -0.35
    fin = None; marcos = []
    for it in items:
        k = it[0]
        if k in ("loop", "alt", "opt"):
            y -= 0.12; pila.append([k, it[1], y, len(pila), []]); y -= 0.22
        elif k == "else":
            pila[-1][4].append((y + 0.05, it[1])); y -= 0.22
        elif k == "end":
            f = pila.pop(); marcos.append((f, y + 0.12)); y -= 0.12
        elif k == "note":
            x1, x2 = xs[it[1][0]], xs[it[1][-1]]
            w = max(2.2, abs(x2 - x1) + 1.6)
            ax.add_patch(Rectangle(((x1 + x2) / 2 - w / 2, y - 0.2), w, 0.34, fc="#FFFACD", ec="gray", lw=0.6))
            ax.text((x1 + x2) / 2, y - 0.03, it[2], ha="center", va="center", fontsize=7); y -= 0.33
        elif k == "msg":
            _, a, fl, b, txt = it; num += 1
            x1, x2 = xs[a], xs[b]
            punt = "--" in fl; cruz = "x" in fl
            ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="-|>" if not cruz else "-|>", lw=0.8,
                        linestyle="--" if punt else "-", color="#B22222" if cruz else "black", shrinkA=0, shrinkB=0))
            if cruz: ax.plot([x2], [y], marker="x", color="#B22222", ms=6)
            ax.text((x1 + x2) / 2, y + 0.04, f"{num}. {txt}", ha="center", va="bottom", fontsize=7.4)
            y -= 0.33
    y_fin = y
    for p in ids:
        ax.plot([xs[p], xs[p]], [0.05, y_fin], color="gray", lw=0.6, ls=":", zorder=0)
    for (k, lab, y0, prof, elses), y1 in marcos:
        x0, x1 = xs[ids[0]] - 1.05 + prof * 0.12, xs[ids[-1]] + 1.05 - prof * 0.12
        ax.add_patch(Rectangle((x0, y1), x1 - x0, y0 - y1, fc="none", ec="#444", lw=0.9, zorder=3))
        ax.add_patch(Rectangle((x0, y0 - 0.2), 0.5, 0.2, fc="#EEE", ec="#444", lw=0.9, zorder=3))
        ax.text(x0 + 0.25, y0 - 0.1, k, fontsize=7.4, ha="center", va="center", weight="bold", zorder=4)
        ax.text(x0 + 0.58, y0 - 0.1, f"[{lab}]", fontsize=7, va="center", zorder=4)
        for ye, le in elses:
            ax.plot([x0, x1], [ye, ye], color="#444", ls="--", lw=0.8, zorder=3)
            ax.text(x0 + 0.1, ye - 0.1, f"[{le or 'else'}]", fontsize=7, va="center", zorder=4)
    out = Path(ruta).with_suffix(".png")
    fig.savefig(out, dpi=210, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return out

if __name__ == "__main__":
    d = Path(__file__).parent
    for f in sorted(d.glob("secuencia_*.mmd")):
        print("generado:", render(f))
