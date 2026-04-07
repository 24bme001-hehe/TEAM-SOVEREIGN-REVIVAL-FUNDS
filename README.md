# 🏎️ Team Sovereign — eBaja Sponsor Collage (Vercel)

## Why this works on Vercel
- **No `templates/` folder** — HTML is generated directly inside Python (no Jinja2 file loading)
- **No static file serving** — ATV image is base64-embedded into the HTML
- **Single serverless function** at `api/index.py`

## File Structure
```
ebaja-vercel/
├── api/
│   └── index.py        ← Only Python file Vercel needs
├── static/
│   └── images/
│       └── atv.png     ← Embedded as base64 at startup
├── vercel.json         ← Routes everything to api/index.py
├── requirements.txt
└── .gitignore
```

## Deploy Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "eBaja sponsors collage"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ebaja-sponsors.git
git push -u origin main
```

### 2. Connect to Vercel
1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import your GitHub repo
3. Framework Preset: **Other** (don't change anything else)
4. Click **Environment Variables** → add:

| Variable | Value |
|---|---|
| `SHEET_ID` | Your Google Sheet ID |
| `GOOGLE_CREDENTIALS` | Full contents of your service account JSON key |
| `NAME_COL` | e.g. `1` (B=1, C=2, D=3…) |
| `AMOUNT_COL` | e.g. `2` |

5. Click **Deploy** ✅

### 3. Google Sheet Setup
- Google Form → Responses tab → Sheets icon → Create spreadsheet  
- Copy Sheet ID from URL: `spreadsheets/d/`**`SHEET_ID`**`/edit`
- Share sheet with your service account email as **Viewer**

---
Without `SHEET_ID` set, the site shows demo names so you can verify deployment works first.
