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

# ── funding goal ──────────────────────────────────────────────────────────────
FUNDING_GOAL = 760000  # 7.6 lacs

# ── no demo sponsors — show empty if sheet has no confirmed entries ──────────
DEMO = []


def get_sponsors():
    try:
        import urllib.request, csv, io
        SHEET_ID = "1vT0pZZbWovxsUYq9-rHlQgIN7kdG-bh2iXqlmb7AKBE"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form_Responses"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8")
        out = []
        under_review = []
        tech_helpers = []
        reader = csv.reader(io.StringIO(content))
        next(reader)  # skip header row
        for row in reader:
            try:
                name = str(row[1]).strip().strip('"')
                if not name:
                    continue
                status = str(row[10]).strip().strip('"').lower() if len(row) > 10 else ""
                # Column F (index 5) = "How can you help us"
                help_type = str(row[5]).strip().strip('"') if len(row) > 5 else ""
                # Column M (index 12) = specific expertise (shown on hover)
                expertise = str(row[12]).strip().strip('"') if len(row) > 12 else ""

                if "technical" in help_type.lower():
                    # Show name in tech bar, expertise on hover (fallback to help_type if M is empty)
                    hover_text = expertise if expertise else help_type
                    tech_helpers.append({"name": name, "field": hover_text})
                elif status == "done":
                    amount = float(str(row[8]).replace(",", "").replace("₹", "").strip().strip('"'))
                    if amount > 0:
                        out.append({"name": name, "amount": amount})
                else:
                    under_review.append(name)
            except (IndexError, ValueError):
                continue
        # Latest first (reverse order — last row = most recent)
        out.reverse()
        print(f"Loaded {len(out)} sponsors, {len(under_review)} under review, {len(tech_helpers)} tech helpers")
        return out if out else DEMO, under_review, tech_helpers
    except Exception as e:
        print("Sheet error:", e)
        return DEMO, [], []


def inr(n):
    if n >= 100000:
        return f"₹{n/100000:.1f}L"
    elif n >= 1000:
        return f"₹{n/1000:.1f}K"
    return f"₹{n:,.0f}"

def inr_full(n):
    return f"₹{n:,.0f}"


def build_page(sponsors, under_review=[], tech_helpers=[]):
    atv_src  = (f'data:image/png;base64,{_b64_img}'
                if _b64_img else '')
    logo_src = (f'data:image/png;base64,{_b64_logo}'
                if _b64_logo else '')

    total    = sum(s["amount"] for s in sponsors)
    top_name = sponsors[0]["name"].split()[0] if sponsors else "—"

    # funding bar
    pct         = min(total / FUNDING_GOAL * 100, 100)
    pct_display = f"{pct:.1f}"
    remaining   = max(FUNDING_GOAL - total, 0)
    rem_str     = "₹{:,.0f} remaining".format(remaining)

    # Build each sponsor <span> — all same font size (32px)
    spans = []
    for i, s in enumerate(sponsors):
        ratio = (s["amount"] - min(sp["amount"] for sp in sponsors) if sponsors else 0)
        tier  = ("tier-1" if s["amount"] >= 5000 else
                 "tier-2" if s["amount"] >= 2000 else
                 "tier-3" if s["amount"] >= 500  else "tier-4")
        spans.append(
            f'<span class="sponsor-name {tier}" '
            f'style="font-size:32px;animation-delay:{i*0.05:.2f}s" '
            f'data-amount="{inr_full(s["amount"])}">'
            f'{s["name"]}</span>'
        )

    collage = "\n    ".join(spans) if spans else (
        '<p style="color:#c8d8e8;opacity:.3;letter-spacing:.2em;font-size:.85rem">'
        'No confirmed sponsors yet</p>')

    logo_html = ''

    # Build under review section
    if under_review:
        review_items = " ".join(
            f'<span style="background:rgba(255,106,0,.12);border:1px solid rgba(255,106,0,.3);'
            f'color:#ffb347;padding:.3rem .9rem;border-radius:20px;font-size:.82rem;'
            f'letter-spacing:.05em;white-space:nowrap">{n}</span>'
            for n in under_review
        )
        review_html = f'''
  <div style="width:min(980px,96%);margin-top:1.5rem;padding:1.2rem 1.5rem;
              background:rgba(255,106,0,.06);border:1px solid rgba(255,106,0,.2);
              border-radius:16px;backdrop-filter:blur(10px)">
    <div style="font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:.2em;
                color:#ff6a00;margin-bottom:.8rem">⏳ &nbsp;PAYMENT UNDER REVIEW</div>
    <div style="display:flex;flex-wrap:wrap;gap:.5rem">{review_items}</div>
  </div>'''
    else:
        review_html = ''

    # Build tech helpers bar
    if tech_helpers:
        tech_items = " ".join(
            f'<span class="tech-pill" data-field="{h["field"]}">{h["name"]}'
            f'<span class="tech-tooltip">{h["field"]}</span></span>'
            for h in tech_helpers
        )
        tech_html = f'''
  <div style="width:min(980px,96%);margin-top:1.5rem;padding:1.2rem 1.5rem;
              background:rgba(14,94,245,.06);border:1px solid rgba(14,94,245,.25);
              border-radius:16px;backdrop-filter:blur(10px)">
    <div style="font-family:'Bebas Neue',sans-serif;font-size:1rem;letter-spacing:.2em;
                color:var(--blue2);margin-bottom:.8rem">🔧 &nbsp;TECHNICAL SUPPORT TEAM</div>
    <div style="display:flex;flex-wrap:wrap;gap:.5rem">{tech_items}</div>
  </div>'''
    else:
        tech_html = ''

    # Mentor dashboard
    mentors = ["Shishir Raghava", "Jigar Modi", "Raj Choksi", "Param Mehta"]
    mentor_cards = "".join(
        f'<div style="background:rgba(14,94,245,.1);border:1px solid rgba(14,94,245,.3);'
        f'border-radius:12px;padding:.9rem 1.4rem;text-align:center;min-width:140px;flex:1">'
        f'<div style="font-size:2rem;margin-bottom:.4rem">🎓</div>'
        f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.05rem;'
        f'color:#e8e8ff">{m}</div></div>'
        for m in mentors
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<style>html {{ touch-action: pan-y; }}</style>
<title>Team Sovereign — Alumni: The Fuel of Phoenix</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@700&family=Exo+2:wght@400;600;800&family=Cinzel:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{{--blue2:#0e5ef5;--silver:#c8d8e8;--gold:#f0c040;--orange:#ff6a00;--bg:#080e1a}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;background:var(--bg);font-family:'Exo 2',sans-serif;overflow-x:hidden;color:#fff}}

.bg{{position:fixed;inset:0;z-index:0}}
.bg img{{width:100%;height:100%;object-fit:cover;filter:blur(2px) brightness(.32) saturate(1.5);opacity:.6}}
.bg-ov{{position:absolute;inset:0;background:linear-gradient(160deg,rgba(8,14,26,.82) 0%,rgba(14,94,245,.12) 50%,rgba(20,6,2,.88) 100%)}}

.page{{position:relative;z-index:1;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:0 1rem 3rem}}

header{{text-align:center;padding:2.5rem 1rem 1rem;width:100%}}

.sovereign-logo{{
  position:fixed;top:16px;left:20px;width:clamp(100px,14vw,170px);height:auto;z-index:100;
  filter:invert(1) brightness(1.8) drop-shadow(0 0 20px rgba(240,192,64,.9));
  animation:logoGlow 3s ease-in-out infinite alternate;
}}
@keyframes logoGlow{{
  from{{filter:invert(1) brightness(1.5) drop-shadow(0 0 12px rgba(240,192,64,.6));}}
  to  {{filter:invert(1) brightness(2.0) drop-shadow(0 0 36px rgba(240,192,64,1));}}
}}

.team-lbl{{font-family:'Bebas Neue',sans-serif;font-size:clamp(2.8rem,8vw,5.5rem);letter-spacing:.15em;color:var(--gold);margin-bottom:.2rem;font-weight:900}}
.title{{font-family:'Bebas Neue',sans-serif;font-size:clamp(1rem,3vw,1.8rem);letter-spacing:.25em;line-height:1;color:var(--silver);opacity:.75}}
.sub{{font-size:clamp(.75rem,1.4vw,.95rem);color:var(--silver);letter-spacing:.25em;margin-top:.5rem;opacity:.8}}

.phoenix-badge{{
  display:inline-block;margin-top:.7rem;font-family:'Cinzel',serif;
  font-size:clamp(.65rem,1.2vw,.85rem);letter-spacing:.35em;color:var(--orange);
  border:1px solid rgba(255,106,0,.35);padding:.3rem 1.2rem;border-radius:50px;
  background:rgba(255,106,0,.08);backdrop-filter:blur(6px);animation:pulseBadge 2.5s ease-in-out infinite;
}}
@keyframes pulseBadge{{0%,100%{{box-shadow:0 0 8px rgba(255,106,0,.2);}}50%{{box-shadow:0 0 22px rgba(255,106,0,.55);}}}}

.divider{{width:min(520px,80%);height:2px;margin:1.4rem auto;
  background:linear-gradient(90deg,transparent,var(--blue2),var(--gold),var(--orange),var(--blue2),transparent)}}

.stats{{display:flex;gap:2rem;justify-content:center;flex-wrap:wrap;margin-bottom:2.2rem}}
.stat{{text-align:center;background:rgba(14,94,245,.12);border:1px solid rgba(14,94,245,.3);
  border-radius:12px;padding:.75rem 1.6rem;backdrop-filter:blur(8px)}}
.stat-v{{font-family:'Bebas Neue',sans-serif;font-size:2rem;color:var(--gold);line-height:1}}
.stat-l{{font-size:.68rem;letter-spacing:.15em;color:var(--silver);opacity:.75;margin-top:.2rem}}

.collage{{width:min(980px,96%);display:flex;flex-wrap:wrap;justify-content:center;align-items:center;
  gap:.55rem 1.1rem;padding:2rem 1.5rem;background:rgba(8,14,26,.58);
  border:1px solid rgba(14,94,245,.2);border-radius:20px;backdrop-filter:blur(14px);
  box-shadow:0 0 70px rgba(14,94,245,.13),0 0 30px rgba(255,106,0,.06),inset 0 0 40px rgba(0,0,0,.35)}}

.sponsor-name{{font-family:'Rajdhani',sans-serif;font-weight:700;line-height:1.1;cursor:default;
  transition:all .25s ease;text-shadow:0 2px 12px rgba(14,94,245,.5);
  padding:.1em .15em;border-radius:4px;position:relative;animation:fadeUp .5s ease both}}
.sponsor-name:hover{{transform:scale(1.08) translateY(-2px);
  text-shadow:0 4px 24px rgba(240,192,64,.75),0 0 40px rgba(14,94,245,.6);z-index:10}}
.sponsor-name::after{{content:attr(data-amount);position:absolute;bottom:calc(100% + 6px);left:50%;
  transform:translateX(-50%) scale(.85);background:rgba(8,14,26,.95);border:1px solid var(--gold);
  color:var(--gold);font-size:.75rem;letter-spacing:.1em;padding:4px 10px;border-radius:6px;
  white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}}
.sponsor-name:hover::after{{opacity:1;transform:translateX(-50%) scale(1)}}

.tier-1{{color:var(--gold)}}.tier-2{{color:#e8e8ff}}.tier-3{{color:var(--silver)}}.tier-4{{color:#8ab0d0}}

/* ── FUNDING PROGRESS BAR ── */
.funding-wrap{{
  width:min(980px,96%);
  margin-top:1.8rem;
  background:rgba(8,14,26,.65);
  border:1px solid rgba(14,94,245,.22);
  border-radius:18px;
  padding:1.5rem 1.8rem 1.6rem;
  backdrop-filter:blur(14px);
  box-shadow:0 0 40px rgba(14,94,245,.1),inset 0 0 30px rgba(0,0,0,.25);
}}
.funding-header{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:.9rem;flex-wrap:wrap;gap:.4rem}}
.funding-title{{font-family:'Bebas Neue',sans-serif;font-size:clamp(1rem,2.5vw,1.4rem);
  letter-spacing:.25em;color:var(--silver);opacity:.85}}
.funding-pct{{font-family:'Bebas Neue',sans-serif;font-size:clamp(1.8rem,5vw,2.8rem);
  line-height:1;
  background:linear-gradient(90deg,var(--orange),var(--gold));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}

/* outer track */
.bar-track{{
  position:relative;
  width:100%;height:28px;
  background:rgba(255,255,255,.06);
  border-radius:999px;
  border:1px solid rgba(255,255,255,.08);
  overflow:visible;
}}
/* filled portion */
.bar-fill{{
  position:absolute;top:0;left:0;
  height:100%;
  border-radius:999px;
  background:linear-gradient(90deg,#0e5ef5 0%,#7b3fff 40%,#ff6a00 75%,#f0c040 100%);
  box-shadow:0 0 18px rgba(255,106,0,.45),0 0 40px rgba(14,94,245,.3);
  transition:width 1.4s cubic-bezier(.22,1,.36,1);
  min-width:4px;
}}
/* animated shimmer on fill */
.bar-fill::after{{
  content:'';position:absolute;inset:0;border-radius:999px;
  background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.18) 50%,transparent 100%);
  background-size:200% 100%;
  animation:barShimmer 2s linear infinite;
}}
@keyframes barShimmer{{from{{background-position:200% 0}}to{{background-position:-200% 0}}}}

/* flame tip marker */
.bar-tip{{
  position:absolute;top:50%;right:-1px;
  transform:translateY(-50%);
  width:28px;height:28px;
  background:var(--gold);
  border-radius:50%;
  border:2px solid rgba(8,14,26,.8);
  box-shadow:0 0 14px rgba(240,192,64,.8),0 0 28px rgba(255,106,0,.5);
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;
  animation:tipPulse 1.5s ease-in-out infinite;
  z-index:2;
}}
@keyframes tipPulse{{0%,100%{{box-shadow:0 0 14px rgba(240,192,64,.8),0 0 28px rgba(255,106,0,.5);}}
                     50%{{box-shadow:0 0 22px rgba(240,192,64,1),0 0 44px rgba(255,106,0,.8);}}}}

/* milestone marker at 100% */
.bar-goal-marker{{
  position:absolute;top:-8px;right:0;
  height:calc(100% + 16px);
  width:2px;background:rgba(240,192,64,.35);border-radius:2px;
}}

.funding-footer{{display:flex;justify-content:space-between;align-items:center;
  margin-top:.85rem;flex-wrap:wrap;gap:.4rem}}
.funding-raised{{font-family:'Exo 2',sans-serif;font-size:clamp(.8rem,1.8vw,1rem);color:var(--silver)}}
.funding-raised strong{{color:var(--gold);font-weight:800}}
.funding-goal-lbl{{font-family:'Bebas Neue',sans-serif;font-size:clamp(.9rem,2vw,1.15rem);
  letter-spacing:.2em;color:var(--silver);opacity:.6}}
.funding-remaining{{font-family:'Exo 2',sans-serif;font-size:clamp(.7rem,1.4vw,.85rem);
  color:var(--orange);opacity:.8}}

/* ── cta ── */
.cta{{display:inline-block;background:linear-gradient(135deg,var(--blue2),#0a3db0);color:#fff;
  font-family:'Bebas Neue',sans-serif;font-size:1.25rem;letter-spacing:.2em;padding:.72rem 2.4rem;
  border-radius:50px;text-decoration:none;border:1px solid rgba(255,255,255,.2);
  box-shadow:0 4px 24px rgba(14,94,245,.4);transition:transform .2s,box-shadow .2s}}
.cta:hover{{transform:translateY(-2px);box-shadow:0 8px 32px rgba(14,94,245,.65)}}

.revival{{margin-top:2.8rem;text-align:center;font-family:'Cinzel',serif;
  font-size:clamp(.85rem,2.2vw,1.3rem);letter-spacing:.3em;text-transform:uppercase;
  background:linear-gradient(90deg,var(--orange),var(--gold),var(--orange));
  background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;animation:shimmer 3s linear infinite}}
.revival-line{{width:min(320px,70%);height:1px;margin:.6rem auto 0;
  background:linear-gradient(90deg,transparent,var(--orange),transparent);opacity:.5}}
@keyframes shimmer{{to{{background-position:200% center}}}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:translateY(0)}}}}

/* ── TABS ── */
.tab-bar{{display:flex;width:min(980px,96%);border-bottom:2px solid rgba(255,255,255,.08);margin-bottom:1.8rem}}
.tab-btn{{font-family:'Bebas Neue',sans-serif;font-size:1.05rem;letter-spacing:.2em;
  padding:.75rem 2rem;background:none;border:none;color:var(--silver);opacity:.45;
  cursor:pointer;transition:opacity .2s,color .2s;position:relative}}
.tab-btn::after{{content:'';position:absolute;bottom:-2px;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--blue2),var(--gold));border-radius:2px;
  transform:scaleX(0);transition:transform .25s ease}}
.tab-btn.active{{opacity:1;color:#fff}}
.tab-btn.active::after{{transform:scaleX(1)}}
.tab-panel{{display:none;width:100%;flex-direction:column;align-items:center}}
.tab-panel.active{{display:flex}}

/* ── tech pills ── */
.tech-pill{{
  position:relative;
  background:rgba(14,94,245,.15);border:1px solid rgba(14,94,245,.35);
  color:#a8c4ff;padding:.3rem .9rem;border-radius:20px;font-size:.82rem;
  letter-spacing:.05em;white-space:nowrap;cursor:default;
  transition:background .2s;
}}
.tech-pill:hover{{background:rgba(14,94,245,.28)}}
.tech-tooltip{{
  display:none;position:absolute;bottom:calc(100% + 8px);left:50%;
  transform:translateX(-50%);background:rgba(8,14,26,.97);
  border:1px solid var(--blue2);color:#fff;font-size:.72rem;
  padding:5px 12px;border-radius:8px;white-space:nowrap;z-index:20;
  letter-spacing:.05em;
}}
.tech-pill:hover .tech-tooltip{{display:block}}
@media(max-width:480px){{
  .stats{{gap:1rem}}.stat{{padding:.6rem 1rem}}
  .collage{{gap:.4rem .8rem;padding:1.2rem 1rem}}
  .sovereign-logo{{width:80px;top:10px;left:10px}}
  body{{overflow-x:hidden}}.page{{padding:0 .5rem 2rem}}
  .bar-track{{height:20px}}.bar-tip{{width:20px;height:20px;font-size:.65rem}}
  .funding-wrap{{padding:1.1rem 1rem}}
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
    <div class="team-lbl">Alumni: The Fuel of Phoenix</div>
    <div class="sub">PDEU &nbsp;·&nbsp; SAE eBaja India &nbsp;·&nbsp; Phoenix Edition</div>
    <div class="phoenix-badge">🔥 &nbsp;Powering the Revival&nbsp; 🔥</div>
    <div class="divider"></div>
  </header>

  <!-- TAB BAR -->
  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('main',this)">🏎️ &nbsp;Sponsors</button>
    <button class="tab-btn" onclick="switchTab('mentors',this)">🎓 &nbsp;Mentors</button>
  </div>

  <!-- ── SPONSORS TAB ── -->
  <div class="tab-panel active" id="tab-main">
    <div class="stats" style="width:100%;justify-content:center">
      <div class="stat"><div class="stat-v">{len(sponsors)}</div><div class="stat-l">SPONSORS</div></div>
      <div class="stat"><div class="stat-v">{inr(total)}</div><div class="stat-l">TOTAL RAISED</div></div>
      <div class="stat"><div class="stat-v">{top_name}</div><div class="stat-l">TOP SPONSOR</div></div>
    </div>

    <div class="collage" style="margin-top:1.5rem">
      {collage}
    </div>

    {review_html}
    {tech_html}

    <div class="funding-wrap">
      <div class="funding-header">
        <div class="funding-title">🔥 &nbsp;Phoenix Funding Progress</div>
        <div class="funding-pct">{pct_display}%</div>
      </div>
      <div class="bar-track" id="barTrack">
        <div class="bar-fill" id="barFill" style="width:0%">
          <div class="bar-tip">🔥</div>
        </div>
        <div class="bar-goal-marker"></div>
      </div>
      <div class="funding-footer">
        <div class="funding-raised">Raised &nbsp;<strong>{inr_full(total)}</strong>&nbsp;<span style="opacity:.5">of</span></div>
        <div class="funding-goal-lbl">Goal: ₹7,60,000</div>
        <div class="funding-remaining">{"🎯 Goal reached!" if remaining == 0 else rem_str}</div>
      </div>
    </div>

    <div style="margin-top:3rem;text-align:center;width:min(700px,92%)">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:clamp(1.4rem,4vw,2.2rem);
                  letter-spacing:.15em;color:var(--silver);margin-bottom:.6rem">
        WHAT TEAM BAJA GIVES YOU
      </div>
      <div style="font-family:'Cinzel',serif;font-size:clamp(1.1rem,3.5vw,1.8rem);
                  letter-spacing:.1em;background:linear-gradient(90deg,var(--orange),var(--gold),var(--orange));
                  background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;animation:shimmer 3s linear infinite;margin-bottom:1.5rem">
        A Special Place For Your Name On Our Phoenix
      </div>
      <a class="cta"
         href="https://docs.google.com/forms/d/e/1FAIpQLSc1fMKYqQpiBFFi_T4JjJ79QMnrMxwUqFx30XtEVB9u9uR3Hg/viewform"
         target="_blank">➕ &nbsp;BECOME A SPONSOR</a>
      <p style="margin-top:1rem;font-size:.78rem;color:var(--silver);opacity:.55;letter-spacing:.12em">
        Your name appears here after payment is confirmed
      </p>
    </div>
    <div class="revival">The Revival of the Phoenix</div>
    <div class="revival-line"></div>
  </div>

  <!-- ── MENTORS TAB ── -->
  <div class="tab-panel" id="tab-mentors">
    <div style="width:min(980px,96%);margin-top:1rem;padding:2.5rem 2rem;
                background:rgba(8,14,26,.65);border:1px solid rgba(240,192,64,.25);
                border-radius:20px;backdrop-filter:blur(14px)">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:.2em;
                  color:var(--gold);margin-bottom:1rem;text-align:center">
        🏆 &nbsp;OUR MENTORS
      </div>
      <p style="text-align:center;font-size:1.2rem;font-weight:700;color:#fff;opacity:1;
                line-height:1.8;max-width:620px;margin:0 auto 2rem">
        These are our mentors who are supporting us and helping us at every step
        throughout this process in every department.
      </p>
      <div style="display:flex;flex-wrap:wrap;gap:1.2rem;justify-content:center">
        {mentor_cards}
      </div>
    </div>
    <div class="revival" style="margin-top:2rem">The Revival of the Phoenix</div>
    <div class="revival-line"></div>
  </div>

</div>

<script>
  function switchTab(id, btn) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + id).classList.add('active');
    btn.classList.add('active');
    if (id === 'main') {{
      setTimeout(() => {{ document.getElementById('barFill').style.width = '{pct_display}%'; }}, 300);
    }}
  }}
  window.addEventListener('load', () => {{
    setTimeout(() => {{ document.getElementById('barFill').style.width = '{pct_display}%'; }}, 300);
  }});
  setTimeout(() => location.reload(), 5 * 60 * 1000);
</script>
</body>
</html>"""


# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path=""):
    sponsors, under_review, tech_helpers = get_sponsors()
    return Response(build_page(sponsors, under_review, tech_helpers), mimetype="text/html")

# Vercel looks for a variable called `app`
