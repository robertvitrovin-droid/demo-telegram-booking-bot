"""Render demo/transcript.json into Telegram-style mock chat PNGs (screenshots/). Needs google-chrome."""
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
CSS = """body{margin:0;background:#0e1621;font-family:Inter,'Noto Color Emoji',sans-serif;color:#fff}
.top{background:#17212b;padding:14px 18px;display:flex;gap:12px;align-items:center;border-bottom:1px solid #0b1118}
.av{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#5eb5f7,#2b7de0);display:flex;align-items:center;justify-content:center;font-weight:700}
.nm{font-weight:600}.st{font-size:13px;color:#6c7883}.demo{margin-left:auto;background:#e8a33d;color:#111;font-weight:800;font-size:12px;padding:4px 9px;border-radius:6px;letter-spacing:1px}
.chat{padding:16px 14px 22px;display:flex;flex-direction:column;gap:8px}
.b{max-width:78%;padding:9px 13px;border-radius:14px;font-size:15px;line-height:1.38;white-space:pre-wrap}
.bot{background:#182533;align-self:flex-start;border-bottom-left-radius:4px}
.me{background:#2b5278;align-self:flex-end;border-bottom-right-radius:4px}
.tap{align-self:flex-end;font-size:12px;color:#8fb3d6;font-style:italic}
.kb{display:flex;flex-direction:column;gap:4px;margin-top:4px;align-self:flex-start;max-width:78%;min-width:52%}
.row{display:flex;gap:4px}.k{flex:1;background:#2b3a4a;border-radius:8px;padding:8px 6px;text-align:center;font-size:13.5px;color:#e6eef6}
.sys{align-self:center;background:#1e2c3a;color:#9fb0c0;font-size:12.5px;padding:5px 12px;border-radius:12px}
.toast{align-self:center;background:#fff;color:#111;padding:9px 16px;border-radius:10px;font-size:14px;box-shadow:0 4px 14px #0008}
.file{display:flex;gap:10px;align-items:center}.ic{width:40px;height:40px;border-radius:50%;background:#4ea4f6;display:flex;align-items:center;justify-content:center}
"""


def page(title, sub, items):
    out = []
    for e in items:
        if e.get("who") == "user":
            out.append(f'<div class="b me">{html.escape(e["text"])}</div>')
        elif e.get("who") == "tap":
            out.append(f'<div class="tap">натиснуто: {html.escape(e["text"])}</div>')
        elif e.get("who") == "toast":
            out.append(f'<div class="toast">{html.escape(e["text"])}</div>')
        elif e.get("who") == "sys":
            out.append(f'<div class="sys">{html.escape(e["text"])}</div>')
        elif e.get("file"):
            out.append(f'<div class="b bot file"><div class="ic">📄</div><div>{e["file"]}<br><span class="st">CSV · експорт записів</span></div></div>')
        else:
            out.append(f'<div class="b bot">{html.escape(e["text"])}</div>')
            if e.get("kb"):
                out.append('<div class="kb">' + "".join(
                    '<div class="row">' + "".join(f'<div class="k">{html.escape(t)}</div>' for t in r) + "</div>"
                    for r in e["kb"]) + "</div>")
    return (f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="top">'
            f'<div class="av">B</div><div><div class="nm">{title}</div><div class="st">{sub}</div></div>'
            f'<div class="demo">DEMO</div></div><div class="chat">{"".join(out)}</div></body></html>')


def shoot(html_str, png, width=600, height=1400):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={width},{height}", "--force-device-scale-factor=2",
                    f"--screenshot={png}", f.name], check=True, capture_output=True)


def main():
    log = json.loads((ROOT / "demo/transcript.json").read_text(encoding="utf-8"))
    scenes, cur = {}, None
    for e in log:
        if "scene" in e:
            cur = e["scene"]; scenes[cur] = []
        else:
            scenes[cur].append(e)
    client = scenes["client"]
    client_a, client_b = client[:6], client[6:]
    rem = [e for e in scenes["reminder"] if e.get("chat") == 1001]
    client_b += [{"who": "sys", "text": "12.10, 10:05 — фонове нагадування"}] + rem
    admin = scenes["admin"]
    out = ROOT / "screenshots"; out.mkdir(exist_ok=True)
    jobs = [("01-client-choose-slot.png", "Клієнт: вибір послуги, дати й часу", client_a, 1080),
            ("02-client-confirm-reminder.png", "Клієнт: підтвердження і нагадування", client_b, 640),
            ("03-admin-panel.png", "Адмін: доступ, список, скасування, експорт", admin, 720)]
    for name, sub, items, h in jobs:
        shoot(page("Demo Booking Bot", sub, items), str(out / name), height=h)
        print(out / name)


if __name__ == "__main__":
    sys.exit(main())
