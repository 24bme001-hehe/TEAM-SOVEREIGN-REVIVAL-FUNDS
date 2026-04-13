"""
api/index.py — Team Sovereign eBaja Sponsor Collage
Vercel serverless entry point. NO templates folder needed.
All HTML is generated as a string directly in Python.
"""

from flask import Flask, Response
import os, json, base64, pathlib

# ── optional Google Sheets integration ────────────────────────────────────────
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

app = Flask(__name__)

# ── config via env vars ───────────────────────────────────────────────────────
SHEET_ID   = os.environ.get("SHEET_ID",   "")
NAME_COL   = int(os.environ.get("NAME_COL",   "1"))
AMOUNT_COL = int(os.environ.get("AMOUNT_COL", "2"))
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ── embed images as base64 (no static-file server needed on Vercel) ───────────
_base = pathlib.Path(__file__).parent.parent / "static" / "images"

_b64_img = ""
_img_path = _base / "atv.png"
if _img_path.exists():
    _b64_img = base64.b64encode(_img_path.read_bytes()).decode()

_b64_logo = ""
_logo_path = _base / "logo.png"
if _logo_path.exists():
    _b64_logo = base64.b64encode(_logo_path.read_bytes()).decode()

# ── demo sponsors shown when sheet isn't configured ──────────────────────────
DEMO = [
    {"name": "Jigar Modi",  "amount": 2500},
    {"name": "Raj Choksi",   "amount": 2500},
    {"name": "Jinay Panchal",   "amount": 2500},
    {"name": "Param Mehta",   "amount": 2500},
    {"name": "Shishir Raghva",   "amount": 2500},
    
   
]


def get_sponsors():
    try:
        import urllib.request, csv, io
        SHEET_ID = "1vT0pZZbWovxsUYq9-rHlQgIN7kdG-bh2iXqlmb7AKBE"
        # Try gviz JSON endpoint - more reliable than CSV export
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form_Responses"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8")
        out = []
        reader = csv.reader(io.StringIO(content))
        next(reader)  # skip header row
        for row in reader:
            try:
                # Only show if column D (index 3) says "done" (case insensitive)
                status = str(row[3]).strip().strip('"').lower() if len(row) > 3 else ""
                if status != "done":
                    continue
                name   = str(row[1]).strip().strip('"')
                amount = float(str(row[2]).replace(",", "").replace("₹", "").strip().strip('"'))
                if name and amount > 0:
                    out.append({"name": name, "amount": amount})
            except (IndexError, ValueError):
                continue
        out.sort(key=lambda x: x["amount"], reverse=True)
        print(f"Loaded {len(out)} sponsors from sheet")
        return out if out else DEMO
    except Exception as e:
        print("Sheet error:", e)
        return DEMO


def inr(n):
    return f"₹{n:,.0f}"


def build_page(sponsors):
    atv_src  = (f'data:image/png;base64,{_b64_img}'
                if _b64_img else '')
    logo_src = (f'data:image/png;base64,{_b64_logo}'
                if _b64_logo else '')

    total    = sum(s["amount"] for s in sponsors)
    top_name = sponsors[0]["name"].split()[0] if sponsors else "—"
    max_a    = sponsors[0]["amount"]  if sponsors else 1
    min_a    = sponsors[-1]["amount"] if sponsors else 0
    rng      = max(max_a - min_a, 1)

    # Build each sponsor <span>
    spans = []
    for i, s in enumerate(sponsors):
        ratio = (s["amount"] - min_a) / rng
        fs    = round(ratio * 72 + 17)
        tier  = ("tier-1" if ratio >= 0.75 else
                 "tier-2" if ratio >= 0.45 else
                 "tier-3" if ratio >= 0.2  else "tier-4")
        spans.append(
            f'<span class="sponsor-name {tier}" '
            f'style="font-size:{fs}px;animation-delay:{i*0.05:.2f}s" '
            f'data-amount="{inr(s["amount"])}">'
            f'{s["name"]}</span>'
        )

    collage = "\n    ".join(spans) if spans else (
        '<p style="color:#c8d8e8;opacity:.6;letter-spacing:.2em">'
        'No sponsors yet — be the first!</p>')

    logo_html = ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<meta name="screen-orientation" content="portrait"/>
<style>
  html {{ touch-action: pan-y; }}
</style>
<title>Alumni: The Fuel of Phoenix — Team Sovereign</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@700&family=Exo+2:wght@400;600;800&family=Cinzel:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{{--blue2:#0e5ef5;--silver:#c8d8e8;--gold:#f0c040;--orange:#ff6a00;--bg:#080e1a}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;background:var(--bg);font-family:'Exo 2',sans-serif;
      overflow-x:hidden;color:#fff}}

/* ── background ── */
.bg{{position:fixed;inset:0;z-index:0}}
.bg img{{width:100%;height:100%;object-fit:cover;
         filter:blur(2px) brightness(.32) saturate(1.5);opacity:.6}}
.bg-ov{{position:absolute;inset:0;
        background:linear-gradient(160deg,rgba(8,14,26,.82) 0%,
        rgba(14,94,245,.12) 50%,rgba(20,6,2,.88) 100%)}}

/* ── layout ── */
.page{{position:relative;z-index:1;min-height:100vh;display:flex;
       flex-direction:column;align-items:center;padding:0 1rem 2rem}}

/* ── header ── */
header{{text-align:center;padding:2.5rem 1rem 1rem;width:100%}}

/* Logo */
.sovereign-logo{{
  position:fixed;
  top:16px;
  left:20px;
  width:clamp(100px,14vw,170px);
  height:auto;
  z-index:100;
  filter:invert(1) brightness(1.8) drop-shadow(0 0 20px rgba(240,192,64,.9));
  animation:logoGlow 3s ease-in-out infinite alternate;
}}
@keyframes logoGlow{{
  from{{filter:invert(1) brightness(1.5) drop-shadow(0 0 12px rgba(240,192,64,.6));}}
  to  {{filter:invert(1) brightness(2.0) drop-shadow(0 0 36px rgba(240,192,64,1));}}
}}

.team-lbl{{font-family:'Bebas Neue',sans-serif;font-size:clamp(1.6rem,4vw,2.8rem);
           letter-spacing:.55em;color:var(--blue2);margin-bottom:.2rem}}
.title{{font-family:'Bebas Neue',sans-serif;font-size:clamp(2.4rem,8vw,5.5rem);
        letter-spacing:.06em;line-height:1;
        background:linear-gradient(90deg,var(--silver) 20%,#fff 50%,var(--blue2) 80%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.sub{{font-size:clamp(.75rem,1.4vw,.95rem);color:var(--silver);letter-spacing:.25em;
      margin-top:.5rem;opacity:.8}}

/* Phoenix badge */
.phoenix-badge{{
  display:inline-block;
  margin-top:.7rem;
  font-family:'Cinzel',serif;
  font-size:clamp(.65rem,1.2vw,.85rem);
  letter-spacing:.35em;
  color:var(--orange);
  text-transform:uppercase;
  border:1px solid rgba(255,106,0,.35);
  padding:.3rem 1.2rem;
  border-radius:50px;
  background:rgba(255,106,0,.08);
  backdrop-filter:blur(6px);
  animation:pulseBadge 2.5s ease-in-out infinite;
}}
@keyframes pulseBadge{{
  0%,100%{{box-shadow:0 0 8px rgba(255,106,0,.2);}}
  50%{{box-shadow:0 0 22px rgba(255,106,0,.55);}}
}}

.divider{{width:min(520px,80%);height:2px;margin:1.4rem auto;
          background:linear-gradient(90deg,transparent,var(--blue2),var(--gold),
          var(--orange),var(--blue2),transparent)}}

/* ── stats ── */
.stats{{display:flex;gap:2rem;justify-content:center;flex-wrap:wrap;margin-bottom:2.2rem}}
.stat{{text-align:center;background:rgba(14,94,245,.12);
       border:1px solid rgba(14,94,245,.3);border-radius:12px;
       padding:.75rem 1.6rem;backdrop-filter:blur(8px)}}
.stat-v{{font-family:'Bebas Neue',sans-serif;font-size:2rem;color:var(--gold);line-height:1}}
.stat-l{{font-size:.68rem;letter-spacing:.15em;color:var(--silver);opacity:.75;margin-top:.2rem}}

/* ── collage ── */
.collage{{width:min(980px,96%);display:flex;flex-wrap:wrap;
          justify-content:center;align-items:center;
          gap:.55rem 1.1rem;padding:2rem 1.5rem;
          background:rgba(8,14,26,.58);border:1px solid rgba(14,94,245,.2);
          border-radius:20px;backdrop-filter:blur(14px);
          box-shadow:0 0 70px rgba(14,94,245,.13),
                     0 0 30px rgba(255,106,0,.06),
                     inset 0 0 40px rgba(0,0,0,.35)}}

.sponsor-name{{font-family:'Rajdhani',sans-serif;font-weight:700;line-height:1.1;
               cursor:default;transition:all .25s ease;
               text-shadow:0 2px 12px rgba(14,94,245,.5);
               padding:.1em .15em;border-radius:4px;position:relative;
               animation:fadeUp .5s ease both}}
.sponsor-name:hover{{transform:scale(1.08) translateY(-2px);
                     text-shadow:0 4px 24px rgba(240,192,64,.75),
                                 0 0 40px rgba(14,94,245,.6);z-index:10}}
.sponsor-name::after{{content:attr(data-amount);position:absolute;
                      bottom:calc(100% + 6px);left:50%;
                      transform:translateX(-50%) scale(.85);
                      background:rgba(8,14,26,.95);border:1px solid var(--gold);
                      color:var(--gold);font-size:.75rem;letter-spacing:.1em;
                      padding:4px 10px;border-radius:6px;white-space:nowrap;
                      opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}}
.sponsor-name:hover::after{{opacity:1;transform:translateX(-50%) scale(1)}}

.tier-1{{color:var(--gold)}}
.tier-2{{color:#e8e8ff}}
.tier-3{{color:var(--silver)}}
.tier-4{{color:#8ab0d0}}

/* ── cta ── */
.cta{{display:inline-block;
      background:linear-gradient(135deg,var(--blue2),#0a3db0);
      color:#fff;font-family:'Bebas Neue',sans-serif;font-size:1.25rem;
      letter-spacing:.2em;padding:.72rem 2.4rem;border-radius:50px;
      text-decoration:none;border:1px solid rgba(255,255,255,.2);
      box-shadow:0 4px 24px rgba(14,94,245,.4);
      transition:transform .2s,box-shadow .2s}}
.cta:hover{{transform:translateY(-2px);box-shadow:0 8px 32px rgba(14,94,245,.65)}}

/* ── revival footer line ── */
.revival{{
  margin-top:2.5rem;
  text-align:center;
  font-family:'Cinzel',serif;
  font-size:clamp(.85rem,2.2vw,1.3rem);
  letter-spacing:.3em;
  text-transform:uppercase;
  background:linear-gradient(90deg,var(--orange),var(--gold),var(--orange));
  background-size:200% auto;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  animation:shimmer 3s linear infinite;
}}
.revival-line{{
  width:min(320px,70%);height:1px;margin:.6rem auto 0;
  background:linear-gradient(90deg,transparent,var(--orange),transparent);
  opacity:.5;
}}
@keyframes shimmer{{to{{background-position:200% center}}}}

footer{{margin-top:1.8rem;text-align:center;font-size:.7rem;
        color:var(--silver);opacity:.4;letter-spacing:.15em}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:translateY(0)}}}}
@media(max-width:480px){{
  .stats{{gap:1rem}}
  .stat{{padding:.6rem 1rem}}
  .collage{{gap:.4rem .8rem;padding:1.2rem 1rem}}
  .sovereign-logo{{width:80px;top:10px;left:10px}}
  .title{{font-size:2rem}}
  body{{overflow-x:hidden}}
  .page{{padding:0 .5rem 2rem}}
}}
</style>
</head>
<body>

<div class="bg">
  <img src="{atv_src}" alt="Team Sovereign Phoenix eBaja"/>
  <div class="bg-ov"></div>
</div>

{logo_html}

<div class="page">
  <header>
    <div class="team-lbl">Alumni</div>
    <div class="title">The Fuel of Phoenix</div>
    <div class="sub">SAE eBaja India &nbsp;·&nbsp; Team Sovereign</div>
    <div class="phoenix-badge">🔥 &nbsp;Powering the Revival&nbsp; 🔥</div>
    <div class="divider"></div>
  </header>

  <div class="stats">
    <div class="stat">
      <div class="stat-v">{len(sponsors)}</div>
      <div class="stat-l">SPONSORS</div>
    </div>
    <div class="stat">
      <div class="stat-v">{inr(total)}</div>
      <div class="stat-l">TOTAL RAISED</div>
    </div>
    <div class="stat">
      <div class="stat-v">{top_name}</div>
      <div class="stat-l">TOP SPONSOR</div>
    </div>
  </div>

  <div class="collage">
    {collage}
  </div>

  <div style="margin-top:2rem;text-align:center">
    <a class="cta"
       href="https://docs.google.com/forms/d/e/1FAIpQLSc1fMKYqQpiBFFi_T4JjJ79QMnrMxwUqFx30XtEVB9u9uR3Hg/viewform"
       target="_blank">➕ &nbsp;BECOME A SPONSOR</a>
    <p style="margin-top:1rem;font-size:.78rem;color:var(--silver);opacity:.55;letter-spacing:.12em">
      Your name appears here after payment is confirmed
    </p>
    <p style="margin-top:.6rem;font-size:.78rem;color:var(--gold);opacity:.75;letter-spacing:.1em">
      🏎️ &nbsp;Your name will be displayed on our Phoenix eBaja vehicle at the SAE competition
    </p>
  </div>

  <!-- Revival tagline -->
  <div class="revival">The Revival of the Phoenix</div>
  <div class="revival-line"></div>

  <footer>Auto-refreshes every 5 min &nbsp;·&nbsp; Team Sovereign &nbsp;·&nbsp; Phoenix</footer>
</div>

<script>setTimeout(()=>location.reload(),5*60*1000)</script>
</body>
</html>"""


# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path=""):
    sponsors = get_sponsors()
    return Response(build_page(sponsors), mimetype="text/html")


# Vercel looks for a variable called `app`
