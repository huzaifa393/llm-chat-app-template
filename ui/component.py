"""
ui/components.py — All Streamlit UI rendering components.
Renders clean HTML — never exposes raw div code to the user.
"""
import base64
import os
import streamlit as st
from config import INTENT_META, INTENT_GENERAL


def get_logo_b64() -> str | None:
    for name in ["rag.png", "logo.png"]:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def logo_html(size: int = 38, circle: bool = False) -> str:
    b64 = get_logo_b64()
    rad = "50%" if circle else "10px"
    if b64:
        return f'<img src="data:image/png;base64,{b64}" style="width:{size}px;height:{size}px;object-fit:cover;border-radius:{rad};">'
    return "🕌"


def render_banner(session_title: str, db_ready: bool, llm_ready: bool, dynamo_ok: bool):
    av = logo_html(42)
    st.markdown(f"""
    <div class="top-banner">
        <div class="banner-logo">{av}</div>
        <div>
            <div class="banner-title">Islamic Knowledge Assistant</div>
            <div class="banner-sub">{session_title}</div>
        </div>
        <div class="banner-badges">
            <div class="badge"><div class="dot {'dot-green' if db_ready  else 'dot-red'}"></div> ChromaDB</div>
            <div class="badge"><div class="dot {'dot-green' if llm_ready else 'dot-red'}"></div> Groq LLM</div>
            <div class="badge"><div class="dot {'dot-green' if dynamo_ok else 'dot-red'}"></div> DynamoDB</div>
            <div class="badge"><div class="dot dot-green"></div> LangChain RAG</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_welcome(db_count: int):
    av = logo_html(60)
    st.markdown(f"""
    <div class="welcome">
        <div class="welcome-icon">{av}</div>
        <div class="welcome-title">Islamic Knowledge Assistant</div>
        <div class="welcome-sub">
            A scholarly RAG system for authentic Islamic research.<br>
            Every answer is sourced from authenticated texts — Quran, Hadith, Tafseer, Dua, and Fiqh.<br>
            Zero hallucination. Full references. Arabic & English.
        </div>
        <div class="welcome-stats">
            <div class="stat-box"><div class="stat-num">{db_count:,}</div><div class="stat-lbl">Text Chunks</div></div>
            <div class="stat-box"><div class="stat-num">16+</div><div class="stat-lbl">Hadith Books</div></div>
            <div class="stat-box"><div class="stat-num">6,236</div><div class="stat-lbl">Quran Verses</div></div>
            <div class="stat-box"><div class="stat-num">5</div><div class="stat-lbl">Languages</div></div>
        </div>
        <div class="chips">
            <div class="chip">📜 Hadith on patience in hardship</div>
            <div class="chip">📖 Tafseer of Ayatul Kursi</div>
            <div class="chip">🤲 Dua before sleeping (Hisnul Muslim)</div>
            <div class="chip">⚖️ Is music halal or haram?</div>
            <div class="chip">📜 40 Hadith Qudsi on Allah's mercy</div>
            <div class="chip">🤲 Morning and evening Adhkar</div>
            <div class="chip">📖 Quran verses about gratitude</div>
            <div class="chip">📜 Hadith about seeking knowledge</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _grade_class(grade: str) -> str:
    g = grade.lower()
    if "sahih" in g:    return "grade-sahih"
    if "hasan" in g:    return "grade-hasan"
    if "da'if" in g or "daif" in g or "weak" in g: return "grade-daif"
    return "grade-unknown"


def _build_source_cards(sources: list) -> str:
    if not sources:
        return ""
    cards = ""
    for s in sources:
        if not isinstance(s, dict):
            continue
        book    = s.get("source", "Unknown")
        ref     = s.get("hadith_number", "?")
        score   = s.get("score", "?")
        stype   = s.get("type", "")
        grade   = s.get("grade", "")
        chapter = s.get("chapter", "")
        text    = s.get("text", "")

        # Clean excerpt — strip [Arabic] blocks from preview
        import re
        excerpt = re.sub(r'\[Arabic\]\n.*?(?=\[English\]|\Z)', '', text, flags=re.DOTALL)
        excerpt = re.sub(r'\[English\]\n', '', excerpt)
        excerpt = excerpt.strip()[:180]

        grade_tag   = f"<span class='src-tag {_grade_class(grade)}'>{grade}</span>" if grade and grade not in ("None","") else ""
        chapter_tag = f"<span class='src-tag'>{chapter[:25]}</span>" if chapter and chapter not in ("None","") else ""

        cards += f"""
        <div class="src-card">
            <div class="src-top">
                <div class="src-book">📖 {book}</div>
                <div class="src-pct">{score}%</div>
            </div>
            <div class="src-excerpt">"{excerpt}{'...' if len(text) > 180 else ''}"</div>
            <div class="src-tags">
                <span class="src-tag">#{ref}</span>
                <span class="src-tag">{stype}</span>
                {grade_tag}{chapter_tag}
            </div>
        </div>"""
    return f'<div class="sources-section"><div class="sources-title">📚 Retrieved Sources</div><div class="sources-grid">{cards}</div></div>'


def render_messages(messages: list):
    av = logo_html(36, circle=True)
    st.markdown('<div class="msg-wrap">', unsafe_allow_html=True)

    for msg in messages:
        ts = msg.get("time", "")

        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user-row">
                <div class="msg-user-bubble">{msg['content']}</div>
            </div>
            <div class="msg-user-time">{ts}</div>
            """, unsafe_allow_html=True)

        else:
            intent = msg.get("intent", INTENT_GENERAL)
            # Guard: intent may be a list in old saved messages
            if isinstance(intent, list):
                intent = intent[0] if intent else INTENT_GENERAL
            if not isinstance(intent, str):
                intent = INTENT_GENERAL
            icon, label, css = INTENT_META.get(intent, ("💬", "General", "intent-general"))
            sources  = msg.get("sources", [])
            meta     = msg.get("meta", {})
            lang     = msg.get("lang", "english")
            content  = msg.get("content", "")

            src_html  = _build_source_cards(sources)
            lang_html = ""
            if lang != "english":
                lang_names = {"arabic":"🌐 Arabic","urdu":"🌐 Urdu",
                              "hindi":"🌐 Hindi","roman_urdu":"🌐 Roman Urdu"}
                lang_html = f'<span class="lang-indicator">{lang_names.get(lang, lang)}</span>'

            footer = ""
            if meta:
                footer = f"""
                <div class="ans-footer">
                    {lang_html}
                    <span class="af-chip">📚 {meta.get('n_sources','?')} sources</span>
                    <span class="af-chip">📈 {meta.get('avg_score','?')}% avg match</span>
                    <span class="af-chip">🔍 {meta.get('n_queries','?')} queries</span>
                    <span class="af-chip">🤖 Llama 3.3 70B · T=0.0</span>
                </div>"""

            st.markdown(f"""
            <div class="msg-bot-row">
                <div class="bot-avatar">{av}</div>
                <div class="msg-bot-bubble">
                    <div class="intent-badge {css}">{icon}&nbsp;{label}</div>
                    <div class="answer-body">{content}</div>
                    {src_html}
                    {footer}
                </div>
            </div>
            <div class="msg-bot-time">{ts}</div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar(session_id: str, session_title: str,
                   all_chats: list, db_ready: bool,
                   llm_ready: bool, dynamo_ok: bool, db_count: int):
    av = logo_html(44)
    st.markdown(f"""
    <div class="sb-header">
        <div class="sb-logo">{av}</div>
        <div>
            <div class="sb-title">Islamic Assistant</div>
            <div class="sb-sub">LangChain · Groq · ChromaDB</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("＋  New Conversation", use_container_width=True):
        return "new_chat"

    st.markdown('<div class="sec-label">Recent Chats</div>', unsafe_allow_html=True)
    if not all_chats:
        st.markdown('<div style="font-size:12px;color:var(--text3);padding:8px 18px">No saved chats yet</div>', unsafe_allow_html=True)
    else:
        rendered = set()
        for i, chat in enumerate(all_chats[:15]):
            sid    = chat.get('session_id', '')
            title  = chat.get('title', 'Untitled')[:30]
            date   = chat.get('date_label', '')
            active = (sid == session_id)
            key    = f"load_{sid}_{i}"
            if key in rendered: continue
            rendered.add(key)
            st.markdown(f"""
            <div class="ch-item {'active' if active else ''}">
                <div class="ch-dot"></div>
                <div class="ch-text">{title}</div>
                <div class="ch-date">{date}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open", key=key, help=title):
                return ("load_chat", sid)

    st.markdown('<div class="sec-label">Search Settings</div>', unsafe_allow_html=True)
    n_results = st.slider("Sources to retrieve", 3, 12, 7)
    source_filter = st.selectbox(
        "Filter by type",
        ["All Sources","Hadith Only","Quran Only","Dua Only",
         "Hadith Qudsi Only","Tafseer Only"]
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:11px;color:var(--text3);padding:4px 8px;line-height:2.2">
        {'✅' if db_ready  else '❌'} ChromaDB — {db_count:,} docs<br>
        {'✅' if llm_ready else '❌'} Groq LLM (Llama 3.3 70B · T=0.0)<br>
        {'✅' if dynamo_ok else '⚠️'} DynamoDB<br>
        ✅ Zero-Hallucination RAG · 6-intent routing
    </div>
    """, unsafe_allow_html=True)

    return ("settings", n_results, source_filter)
