"""
ui/components.py — All Streamlit UI rendering components.
Clean HTML output — never exposes raw div code to user.
"""
import re
import base64
import os
import streamlit as st
from config import INTENT_META, INTENT_GENERAL


def get_logo_b64() -> str | None:
    for name in ["rag.png", "logo.png"]:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name
        )
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def logo_html(size: int = 38, circle: bool = False) -> str:
    b64 = get_logo_b64()
    rad = "50%" if circle else "10px"
    if b64:
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:{size}px;height:{size}px;object-fit:cover;border-radius:{rad};">'
        )
    return "🕌"


def _safe_intent(intent) -> str:
    if isinstance(intent, list):
        intent = intent[0] if intent else INTENT_GENERAL
    if not isinstance(intent, str) or not intent:
        return INTENT_GENERAL
    return intent


def render_banner(session_title: str, db_ready: bool,
                  llm_ready: bool, dynamo_ok: bool):
    av = logo_html(42)
    st.markdown(f"""
    <div class="top-banner">
        <div class="banner-logo">{av}</div>
        <div>
            <div class="banner-title">Islamic Knowledge Assistant</div>
            <div class="banner-sub">{session_title}</div>
        </div>
        <div class="banner-badges">
            <div class="badge">
                <div class="dot {'dot-green' if db_ready  else 'dot-red'}"></div> ChromaDB
            </div>
            <div class="badge">
                <div class="dot {'dot-green' if llm_ready else 'dot-red'}"></div> Groq LLM
            </div>
            <div class="badge">
                <div class="dot {'dot-green' if dynamo_ok else 'dot-red'}"></div> DynamoDB
            </div>
            <div class="badge">
                <div class="dot dot-green"></div> LangChain RAG
            </div>
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
            A production-grade RAG system for authentic Islamic scholarship.<br>
            Every answer comes from verified sources — Quran, Hadith, Tafseer, Dua, Fiqh.<br>
            Zero hallucination &bull; Full citations &bull; Arabic &amp; English &bull; 5 Languages
        </div>
        <div class="welcome-stats">
            <div class="stat-box">
                <div class="stat-num">{db_count:,}</div>
                <div class="stat-lbl">Total Chunks</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">44,915</div>
                <div class="stat-lbl">Hadiths</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">6,236</div>
                <div class="stat-lbl">Quran Verses</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">6,900</div>
                <div class="stat-lbl">Fiqh Entries</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">268</div>
                <div class="stat-lbl">Duas</div>
            </div>
        </div>
        <div class="chips">
            <div class="chip">📜 Hadith on patience in hardship</div>
            <div class="chip">📖 Tafseer of Ayatul Kursi</div>
            <div class="chip">🤲 Dua before sleeping (Hisnul Muslim)</div>
            <div class="chip">⚖️ Is music halal or haram?</div>
            <div class="chip">📜 40 Hadith Qudsi on Allah&apos;s mercy</div>
            <div class="chip">🤲 Morning and evening Adhkar</div>
            <div class="chip">📖 Quran verses about gratitude</div>
            <div class="chip">⚖️ What breaks wudu?</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _grade_class(grade: str) -> str:
    g = str(grade).lower()
    if "sahih" in g:
        return "grade-sahih"
    if "hasan" in g:
        return "grade-hasan"
    if "da'if" in g or "daif" in g or "weak" in g:
        return "grade-daif"
    return "grade-unknown"


def _build_source_cards(sources) -> str:
    if not sources or not isinstance(sources, list):
        return ""
    cards = ""
    for s in sources:
        if not isinstance(s, dict):
            continue
        book    = str(s.get("source", "Unknown"))
        ref     = str(s.get("hadith_number", "?"))
        score   = s.get("score", "?")
        stype   = str(s.get("type", ""))
        grade   = str(s.get("grade", ""))
        chapter = str(s.get("chapter", ""))
        text    = str(s.get("text", ""))

        # Clean excerpt — remove [Arabic], [English], [Translation] tags
        excerpt = re.sub(r'\[Arabic\]\n.*?(?=\[|\Z)', '', text, flags=re.DOTALL)
        excerpt = re.sub(r'\[(English|Translation|Transliteration|Reference|Hisnul Muslim[^\]]*)\]\n', '', excerpt)
        excerpt = re.sub(r'\[Source \d+\].*?\n', '', excerpt)
        excerpt = re.sub(r'(Book|Ref|Grade|Type|Match|Chapter|Surah|Verse)\s*:.*?\n', '', excerpt)
        excerpt = excerpt.strip()[:200]

        grade_tag = (
            f"<span class='src-tag {_grade_class(grade)}'>{grade}</span>"
            if grade and grade not in ("None", "", "Not specified")
            else ""
        )
        chapter_tag = (
            f"<span class='src-tag'>{chapter[:25]}</span>"
            if chapter and chapter not in ("None", "")
            else ""
        )

        type_icon = {
            "hadith": "📜", "hadith_qudsi": "✨", "quran": "📖",
            "tafseer": "🔍", "dua": "🤲", "fiqh": "⚖️",
        }.get(stype, "📄")

        cards += f"""
        <div class="src-card">
            <div class="src-top">
                <div class="src-book">{type_icon} {book}</div>
                <div class="src-pct">{score}%</div>
            </div>
            <div class="src-excerpt">"{excerpt}{'...' if len(text) > 200 else ''}"</div>
            <div class="src-tags">
                <span class="src-tag">#{ref}</span>
                <span class="src-tag">{stype}</span>
                {grade_tag}{chapter_tag}
            </div>
        </div>"""

    if not cards:
        return ""
    return (
        '<div class="sources-section">'
        '<div class="sources-title">📚 Retrieved Sources</div>'
        f'<div class="sources-grid">{cards}</div>'
        '</div>'
    )


def render_translate_button(msg_index: int, content: str):
    """Render a translate button for each bot message."""
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("🌐 Translate", key=f"translate_{msg_index}",
                     help="Translate this answer"):
            st.session_state[f"translate_target_{msg_index}"] = True
    with col2:
        if st.session_state.get(f"translate_target_{msg_index}"):
            lang = st.selectbox(
                "To",
                ["Urdu", "Arabic", "Hindi", "Roman Urdu"],
                key=f"lang_select_{msg_index}",
                label_visibility="collapsed"
            )
            if st.button("Go", key=f"do_translate_{msg_index}"):
                st.session_state[f"translate_result_{msg_index}"] = {
                    "lang": lang,
                    "text": content
                }


def render_messages(messages: list):
    av = logo_html(36, circle=True)
    st.markdown('<div class="msg-wrap">', unsafe_allow_html=True)

    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue

        ts   = str(msg.get("time", ""))
        role = str(msg.get("role", ""))

        if role == "user":
            content = str(msg.get("content", ""))
            st.markdown(f"""
            <div class="msg-user-row">
                <div class="msg-user-bubble">{content}</div>
            </div>
            <div class="msg-user-time">{ts}</div>
            """, unsafe_allow_html=True)

        else:
            intent  = _safe_intent(msg.get("intent", INTENT_GENERAL))
            sources = msg.get("sources", [])
            meta    = msg.get("meta", {})
            lang    = str(msg.get("lang", "english"))
            content = str(msg.get("content", ""))

            if not isinstance(sources, list):
                sources = []
            if not isinstance(meta, dict):
                meta = {}

            icon, label, css = INTENT_META.get(
                intent, ("💬", "General", "intent-general")
            )

            src_html  = _build_source_cards(sources)

            lang_html = ""
            if lang and lang != "english":
                lang_names = {
                    "arabic":     "🌐 Arabic",
                    "urdu":       "🌐 Urdu",
                    "hindi":      "🌐 Hindi",
                    "roman_urdu": "🌐 Roman Urdu",
                }
                lang_html = (
                    f'<span class="lang-indicator">'
                    f'{lang_names.get(lang, lang)}</span>'
                )

            footer = ""
            if meta:
                n_src  = meta.get("n_sources", "?")
                avg_sc = meta.get("avg_score", "?")
                n_q    = meta.get("n_queries", "?")
                footer = f"""
                <div class="ans-footer">
                    {lang_html}
                    <span class="af-chip">📚 {n_src} sources</span>
                    <span class="af-chip">📈 {avg_sc} avg match</span>
                    <span class="af-chip">🔍 {n_q} queries</span>
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

            # Translate button (only for bot messages with content)
            if content and "Not found" not in content[:50]:
                render_translate_button(idx, content)

            # Show translation result if triggered
            tr = st.session_state.get(f"translate_result_{idx}")
            if tr:
                with st.spinner(f"Translating to {tr['lang']}..."):
                    try:
                        from translator import translate_answer
                        lang_map = {
                            "Urdu": "urdu", "Arabic": "arabic",
                            "Hindi": "hindi", "Roman Urdu": "roman_urdu"
                        }
                        translated = translate_answer(
                            tr["text"], lang_map.get(tr["lang"], "urdu")
                        )
                        st.markdown(f"""
                        <div class="translation-box">
                            <div class="translation-label">🌐 {tr['lang']} Translation</div>
                            <div class="translation-content">{translated}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Translation failed: {e}")

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
        st.markdown(
            '<div style="font-size:12px;color:var(--text3);padding:8px 18px">'
            'No saved chats yet</div>',
            unsafe_allow_html=True
        )
    else:
        rendered = set()
        for i, chat in enumerate(all_chats[:15]):
            if not isinstance(chat, dict):
                continue
            sid    = str(chat.get("session_id", ""))
            title  = str(chat.get("title", "Untitled"))[:30]
            date   = str(chat.get("date_label", ""))
            active = (sid == session_id)
            key    = f"load_{sid}_{i}"
            if key in rendered:
                continue
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
        ["All Sources", "Hadith Only", "Quran Only", "Dua Only",
         "Hadith Qudsi Only", "Tafseer Only", "Fiqh Only"]
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:11px;color:var(--text3);padding:4px 8px;line-height:2.2">
        {'✅' if db_ready  else '❌'} ChromaDB — {db_count:,} docs<br>
        {'✅' if llm_ready else '❌'} Groq LLM (Llama 3.3 70B · T=0.0)<br>
        {'✅' if dynamo_ok else '⚠️'} DynamoDB<br>
        ✅ 2-Stage Hybrid Retrieval<br>
        ✅ Zero-Hallucination · 7-intent routing
    </div>
    """, unsafe_allow_html=True)

    return ("settings", n_results, source_filter)
