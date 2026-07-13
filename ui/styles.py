"""
ui/styles.py — All CSS styles for the Islamic RAG Assistant
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&family=Amiri:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --green:      #22c55e;
    --green-dim:  #16a34a;
    --green-glow: rgba(34,197,94,0.12);
    --surface:    #ffffff;
    --surface2:   #f8fafc;
    --surface3:   #f1f5f9;
    --border:     #e2e8f0;
    --border2:    #cbd5e1;
    --text1:      #0f172a;
    --text2:      #475569;
    --text3:      #94a3b8;
    --blue:       #1d4ed8;
    --gold:       #d97706;
    --gold-dim:   #92400e;
    --gold-glow:  rgba(217,119,6,0.12);
    --shadow:     0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
    --radius:     12px;
    --radius-sm:  8px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--surface2);
    color: var(--text1);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    width: 290px !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
    background: var(--surface) !important;
}
.sb-header {
    padding: 20px 18px 16px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px;
}
.sb-logo {
    width: 44px; height: 44px; border-radius: 12px;
    background: linear-gradient(135deg, var(--green), var(--green-dim));
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 14px var(--green-glow);
    overflow: hidden; flex-shrink: 0;
}
.sb-logo img { width:100%; height:100%; object-fit:cover; border-radius:12px; }
.sb-title { font-size: 14px; font-weight: 600; color: var(--text1); }
.sb-sub   { font-size: 11px; color: var(--text3); margin-top: 2px; }
.sec-label {
    font-size: 10px; font-weight: 700; color: var(--text3);
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 16px 18px 7px;
}

/* ── BUTTONS ── */
.stButton > button {
    background: var(--surface2) !important;
    color: var(--text1) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important; font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 8px 14px !important; width: 100% !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--surface3) !important;
    border-color: var(--border2) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--green), var(--green-dim)) !important;
    color: #fff !important; border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px var(--green-glow) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px var(--green-glow) !important;
}

/* ── CHAT HISTORY ── */
.ch-item {
    padding: 9px 14px; border-radius: 8px; margin: 2px 8px;
    display: flex; align-items: center; gap: 10px;
    border: 1px solid transparent; transition: all 0.12s;
}
.ch-item:hover { background: var(--surface2); border-color: var(--border); }
.ch-item.active { background: var(--green-glow); border-color: rgba(34,197,94,0.25); }
.ch-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--border2); flex-shrink: 0; }
.ch-item.active .ch-dot { background: var(--green); }
.ch-text { font-size: 12px; color: var(--text2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.ch-item.active .ch-text { color: var(--text1); font-weight: 500; }
.ch-date { font-size: 10px; color: var(--text3); flex-shrink: 0; }

/* ── TOP BANNER ── */
.top-banner {
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 14px 28px; display: flex; align-items: center; gap: 14px;
}
.banner-logo {
    width: 42px; height: 42px; border-radius: 11px;
    background: linear-gradient(135deg, var(--green), var(--green-dim));
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 14px var(--green-glow); overflow: hidden; flex-shrink: 0;
}
.banner-logo img { width:100%; height:100%; object-fit:cover; border-radius:11px; }
.banner-title { font-size: 17px; font-weight: 600; color: var(--text1); letter-spacing: -0.3px; }
.banner-sub   { font-size: 12px; color: var(--text3); margin-top: 1px; }
.banner-badges { margin-left: auto; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge {
    display: flex; align-items: center; gap: 5px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 11px;
    font-size: 11px; color: var(--text2); font-weight: 500;
}
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-green { background: var(--green); box-shadow: 0 0 5px var(--green); }
.dot-red   { background: #ef4444; }

/* ── MESSAGES ── */
.msg-wrap { padding: 0 28px 20px; }
.msg-user-row { display: flex; justify-content: flex-end; margin: 20px 0 3px; }
.msg-user-bubble {
    background: linear-gradient(135deg, #1e3a8a, #1d4ed8);
    color: #fff; border-radius: 18px 18px 4px 18px;
    padding: 13px 18px; max-width: 60%;
    font-size: 14px; line-height: 1.65; box-shadow: var(--shadow);
}
.msg-user-time { text-align: right; font-size: 10px; color: var(--text3); margin: 3px 0 10px; }
.msg-bot-row { display: flex; gap: 12px; margin: 20px 0 3px; align-items: flex-start; }
.bot-avatar {
    width: 36px; height: 36px; min-width: 36px; border-radius: 50%;
    background: linear-gradient(135deg, var(--green), var(--green-dim));
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; box-shadow: 0 4px 12px var(--green-glow);
    flex-shrink: 0; overflow: hidden;
}
.bot-avatar img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
.msg-bot-bubble {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px 18px 18px 18px;
    padding: 18px 22px; max-width: 82%;
    font-size: 14px; color: var(--text1); line-height: 1.85;
    box-shadow: var(--shadow);
}
.msg-bot-time { font-size: 10px; color: var(--text3); margin: 3px 0 10px 52px; }

/* ── INTENT BADGE ── */
.intent-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
    padding: 3px 10px; border-radius: 20px; margin-bottom: 12px;
}
.intent-hadith  { background: rgba(234,179,8,0.1);  color: #854d0e; border: 1px solid rgba(234,179,8,0.3); }
.intent-quran   { background: rgba(34,197,94,0.1);  color: #14532d; border: 1px solid rgba(34,197,94,0.3); }
.intent-dua     { background: rgba(168,85,247,0.1); color: #581c87; border: 1px solid rgba(168,85,247,0.3); }
.intent-fiqh    { background: rgba(59,130,246,0.1); color: #1e3a8a; border: 1px solid rgba(59,130,246,0.3); }
.intent-tafseer { background: rgba(217,119,6,0.1);  color: #92400e; border: 1px solid rgba(217,119,6,0.3); }
.intent-general { background: rgba(148,163,184,0.1);color: #334155; border: 1px solid rgba(148,163,184,0.3); }

/* ── ANSWER BODY ── */
.answer-body {
    font-size: 14px; line-height: 1.9; color: var(--text1);
    white-space: pre-wrap; word-break: break-word;
}
.answer-body strong, .answer-body b {
    color: var(--text1); font-weight: 600;
}
.answer-body em { color: var(--text2); }
.arabic-text {
    font-family: 'Amiri', serif;
    font-size: 18px; line-height: 2.2;
    direction: rtl; text-align: right;
    color: var(--text1);
    background: linear-gradient(135deg, rgba(34,197,94,0.04), rgba(22,163,74,0.02));
    border-right: 3px solid var(--green);
    padding: 10px 14px; border-radius: 6px;
    margin: 8px 0;
}
.transliteration {
    font-style: italic; color: var(--text2);
    font-size: 13px; line-height: 1.8;
    background: var(--surface3); border-radius: 6px;
    padding: 8px 12px; margin: 6px 0;
}
.translation-text {
    color: var(--text1); font-size: 14px;
    line-height: 1.8; padding: 4px 0;
}
.ref-line {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    margin-top: 8px; padding-top: 8px;
    border-top: 1px dashed var(--border);
}
.ref-badge {
    font-size: 11px; font-weight: 600; font-family: 'DM Mono', monospace;
    background: var(--surface3); border: 1px solid var(--border);
    border-radius: 4px; padding: 2px 8px; color: var(--text2);
}
.grade-sahih  { background: rgba(34,197,94,0.1); color: #14532d; border-color: rgba(34,197,94,0.3); }
.grade-hasan  { background: rgba(59,130,246,0.1); color: #1e3a8a; border-color: rgba(59,130,246,0.3); }
.grade-daif   { background: rgba(239,68,68,0.1);  color: #991b1b; border-color: rgba(239,68,68,0.3); }
.grade-unknown{ background: var(--surface3); color: var(--text3); }
.not-found-box {
    background: rgba(148,163,184,0.08); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 14px 18px;
    font-size: 13px; color: var(--text2); line-height: 1.7;
}

/* ── SOURCE CARDS ── */
.sources-section { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); }
.sources-title { font-size: 11px; font-weight: 700; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 8px;
}
.src-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 11px 13px;
    transition: border-color 0.15s;
}
.src-card:hover { border-color: var(--green); box-shadow: 0 0 0 3px var(--green-glow); }
.src-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.src-book { font-size: 12px; font-weight: 600; color: var(--green-dim); }
.src-pct {
    font-size: 10px; font-weight: 700;
    background: var(--green-glow); color: var(--green-dim);
    border-radius: 10px; padding: 2px 8px;
}
.src-excerpt {
    font-size: 11px; color: var(--text2); line-height: 1.55; font-style: italic;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.src-tags { display: flex; gap: 5px; margin-top: 7px; flex-wrap: wrap; }
.src-tag {
    font-size: 10px; color: var(--text3); background: var(--surface3);
    border-radius: 3px; padding: 1px 6px; font-family: 'DM Mono', monospace;
}

/* ── ANSWER FOOTER ── */
.ans-footer {
    display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
    margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border);
}
.af-chip { font-size: 10px; color: var(--text3); font-family: 'DM Mono', monospace; }
.lang-indicator {
    font-size: 10px; font-weight: 600;
    background: rgba(59,130,246,0.1); color: #1e3a8a;
    border: 1px solid rgba(59,130,246,0.2); border-radius: 10px;
    padding: 2px 8px;
}

/* ── WELCOME ── */
.welcome {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 62vh; text-align: center; padding: 48px 24px;
}
.welcome-icon {
    width: 80px; height: 80px; border-radius: 22px;
    background: linear-gradient(135deg,rgba(34,197,94,0.1),rgba(22,163,74,0.05));
    border: 1px solid rgba(34,197,94,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 40px; margin-bottom: 22px;
    box-shadow: 0 8px 32px var(--green-glow); overflow: hidden;
}
.welcome-icon img { width:100%; height:100%; object-fit:cover; border-radius:22px; }
.welcome-title { font-size: 26px; font-weight: 700; color: var(--text1); margin-bottom: 10px; }
.welcome-sub { font-size: 15px; color: var(--text2); max-width: 500px; line-height: 1.75; margin-bottom: 28px; }
.welcome-stats { display: flex; gap: 14px; margin-bottom: 32px; flex-wrap: wrap; justify-content: center; }
.stat-box {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 13px 20px;
    text-align: center; box-shadow: var(--shadow);
}
.stat-num { font-size: 20px; font-weight: 700; color: var(--green-dim); }
.stat-lbl { font-size: 10px; color: var(--text3); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.8px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 700px; }
.chip {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 8px 16px;
    font-size: 13px; color: var(--text2); cursor: pointer;
    box-shadow: var(--shadow); transition: all 0.15s;
}
.chip:hover { background: var(--green-glow); border-color: rgba(34,197,94,0.4); color: var(--green-dim); }

/* ── INPUT ── */
.stTextInput > div > div > input {
    background: var(--surface2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; color: var(--text1) !important;
    font-size: 14px !important; padding: 14px 18px !important;
    font-family: 'DM Sans', sans-serif !important; transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--green) !important;
    box-shadow: 0 0 0 3px var(--green-glow) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text3) !important; }

/* ── MISC ── */
.stFileUploader > div { background: var(--surface2) !important; border: 1px dashed var(--border2) !important; border-radius: var(--radius-sm) !important; }
.stSelectbox > div > div { background: var(--surface2) !important; border-color: var(--border) !important; color: var(--text1) !important; font-size: 13px !important; border-radius: var(--radius-sm) !important; }
.stSuccess > div { background: rgba(34,197,94,0.08) !important; border-color: rgba(34,197,94,0.3) !important; color: #166534 !important; border-radius: var(--radius-sm) !important; }
.stError > div { background: rgba(239,68,68,0.08) !important; border-color: rgba(239,68,68,0.3) !important; color: #991b1b !important; border-radius: var(--radius-sm) !important; }
.stSpinner > div { border-top-color: var(--green) !important; }
hr { border-color: var(--border) !important; margin: 4px 0 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }
</style>
"""

# Append translation box styles to CSS variable
_EXTRA = """
.translation-box {
    background: linear-gradient(135deg,rgba(34,197,94,0.05),rgba(22,163,74,0.02));
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: var(--radius-sm);
    padding: 14px 18px; margin-top: 12px;
}
.translation-label {
    font-size: 11px; font-weight: 700; color: var(--green-dim);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px;
}
.translation-content {
    font-size: 14px; line-height: 1.9; color: #f8fafc;
    direction: auto; white-space: pre-wrap;
}
"""
CSS = CSS.replace("</style>", _EXTRA + "</style>")
