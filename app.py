"""
app.py — Islamic Knowledge Assistant
======================================
Thin orchestration layer. All logic lives in modules.

Architecture:
  app.py          ← Streamlit entry point, orchestration
  config.py       ← All constants and thresholds
  intent.py       ← Language detection, intent routing, query expansion
  retriever.py    ← ChromaDB search, validation, dedup, re-ranking
  chains.py       ← LangChain zero-hallucination prompts per intent
  translator.py   ← Multilingual agent (Arabic/Urdu/Hindi/RomanUrdu)
  memory.py       ← Conversation memory
  database.py     ← DynamoDB persistence
  ui/styles.py    ← All CSS
  ui/components.py← All rendering components
"""

import os
import uuid
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── MODULE IMPORTS ────────────────────────────────────
from config import (
    INTENT_SMALLTALK, INTENT_GENERAL, SYSTEM_ABOUT,
    MIN_SCORE_THRESHOLD
)
from intent    import detect_intent, detect_language, expand_query
from retriever import search, format_context, db_stats
from chains    import build_chains
from translator import translate_to_english, translate_answer
from memory    import ConversationMemory
from database  import get_table, save_chat, load_all_chats, load_chat
from ui.styles import CSS
from ui.components import (
    render_banner, render_welcome, render_messages, render_sidebar
)

# ═══════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Islamic Knowledge Assistant",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  CACHED RESOURCES
# ═══════════════════════════════════════════════════════
@st.cache_resource
def load_chains():
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return None
    return build_chains(key)

@st.cache_resource
def load_dynamo():
    return get_table()

@st.cache_data(ttl=60)
def get_db_stats():
    return db_stats()


# ═══════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "messages":      [],
        "session_id":    str(uuid.uuid4()),
        "session_title": "New Chat",
        "memory":        ConversationMemory(),
        "input_key":     0,     # increment to clear input field
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ═══════════════════════════════════════════════════════
#  LOAD RESOURCES
# ═══════════════════════════════════════════════════════
chains      = load_chains()
dynamo      = load_dynamo()
stats       = get_db_stats()
db_ready    = stats["ready"]
db_count    = stats["total"]
llm_ready   = chains is not None
dynamo_ok   = dynamo is not None


# ═══════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════
with st.sidebar:
    result = render_sidebar(
        session_id    = st.session_state.session_id,
        session_title = st.session_state.session_title,
        all_chats     = load_all_chats(),
        db_ready      = db_ready,
        llm_ready     = llm_ready,
        dynamo_ok     = dynamo_ok,
        db_count      = db_count,
    )

if result == "new_chat":
    st.session_state.messages      = []
    st.session_state.session_id    = str(uuid.uuid4())
    st.session_state.session_title = "New Chat"
    st.session_state.memory        = ConversationMemory()
    st.session_state.input_key    += 1
    st.rerun()
elif isinstance(result, tuple) and result[0] == "load_chat":
    sid = result[1]
    st.session_state.messages      = load_chat(sid)
    st.session_state.session_id    = sid
    st.session_state.session_title = next(
        (c.get('title','Chat') for c in load_all_chats() if c.get('session_id') == sid),
        "Chat"
    )
    st.session_state.input_key += 1
    st.rerun()

# Unpack settings
n_results     = 7
source_filter = "All Sources"
if isinstance(result, tuple) and result[0] == "settings":
    _, n_results, source_filter = result


# ═══════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════
render_banner(
    session_title = st.session_state.session_title,
    db_ready      = db_ready,
    llm_ready     = llm_ready,
    dynamo_ok     = dynamo_ok,
)


# ═══════════════════════════════════════════════════════
#  CHAT DISPLAY
# ═══════════════════════════════════════════════════════
if not st.session_state.messages:
    render_welcome(db_count)
else:
    render_messages(st.session_state.messages)


# ═══════════════════════════════════════════════════════
#  INPUT BAR
# ═══════════════════════════════════════════════════════
st.markdown("---")
col1, col2 = st.columns([6, 1])
with col1:
    query = st.text_input(
        "q",
        placeholder="Ask in Arabic, English, Urdu, Hindi or Roman Urdu...",
        label_visibility="collapsed",
        key=f"q_input_{st.session_state.input_key}",  # key change = blank field
    )
with col2:
    send = st.button("Ask ➤", type="primary", use_container_width=True)

st.markdown(
    '<div style="text-align:center;font-size:11px;color:var(--text3);padding:4px 0 8px">'
    'Sources: Quran · 16+ Hadith Books · Hisnul Muslim · Tafseer Ibn Kathir · '
    'Zero hallucination · All references verified'
    '</div>',
    unsafe_allow_html=True
)


# ═══════════════════════════════════════════════════════
#  QUERY PIPELINE
# ═══════════════════════════════════════════════════════
if send and query.strip():

    # ── Guard: system not ready ───────────────────────
    if not db_ready:
        st.error("⛔ ChromaDB not ready. Run: python3.11 ingest.py")
        st.stop()
    if not llm_ready:
        st.error("⛔ GROQ_API_KEY missing in .env file")
        st.stop()

    now_str = datetime.now().strftime("%I:%M %p")

    # ── Save user message ─────────────────────────────
    st.session_state.messages.append({
        "role": "user", "content": query, "time": now_str
    })
    if st.session_state.session_title == "New Chat":
        st.session_state.session_title = query[:42] + ("..." if len(query) > 42 else "")

    # ── Clear input for next message ──────────────────
    st.session_state.input_key += 1

    with st.spinner("Searching authenticated Islamic sources..."):
        try:
            # STEP 1 — Detect language
            lang = detect_language(query)

            # STEP 2 — Detect intent (on original query)
            intent = detect_intent(query)

            # STEP 3 — Smalltalk / about-system shortcut
            if intent == INTENT_SMALLTALK:
                st.session_state.messages.append({
                    "role":    "assistant",
                    "content": SYSTEM_ABOUT,
                    "intent":  INTENT_SMALLTALK,
                    "sources": [],
                    "time":    datetime.now().strftime("%I:%M %p"),
                    "lang":    "english",
                    "meta":    {},
                })
                save_chat(st.session_state.session_id,
                          st.session_state.session_title,
                          st.session_state.messages)
                st.rerun()

            # STEP 4 — Translate non-English query to English for search
            search_query = translate_to_english(query, lang)

            # STEP 5 — Re-detect intent on English query (may be clearer)
            if lang != "english":
                intent = detect_intent(search_query) or intent

            # STEP 6 — Expand query into variants
            queries = expand_query(search_query, intent, lang)

            # STEP 7 — Retrieve from ChromaDB
            chunks = search(
                queries=queries,
                intent=intent,
                n=n_results,
                source_filter=source_filter
            )

            # STEP 8 — Hard gate: nothing found above threshold
            if not chunks:
                answer = (
                    "**No authenticated Islamic source found** for this query "
                    "in the database.\n\n"
                    "This system only returns verified references. "
                    "Please rephrase your question, try a different filter, "
                    "or consult a qualified Islamic scholar directly."
                )
                sources_data = []
                avg_score    = 0.0
            else:
                # STEP 9 — Format context for LLM
                context = format_context(chunks)

                # STEP 10 — Build conversation history
                history = st.session_state.memory.get_history()

                # STEP 11 — Run intent-specific chain
                chain  = chains.get(intent, chains[INTENT_GENERAL])
                answer = chain.invoke({
                    "context":  context,
                    "question": search_query,   # always English to LLM
                    "history":  history,
                })

                # STEP 12 — Translate answer back to user's language
                if lang != "english":
                    answer = translate_answer(answer, lang)

                # STEP 13 — Update memory
                st.session_state.memory.add(query, answer)

                # Build source card data
                sources_data = [{
                    "source":        c["source"],
                    "hadith_number": c["hadith_number"],
                    "text":          c["text"],
                    "score":         c["score"],
                    "type":          c["type"],
                    "grade":         c.get("grade", ""),
                    "chapter":       c.get("chapter", ""),
                } for c in chunks]

                avg_score = round(
                    sum(c["score"] for c in chunks) / len(chunks), 1
                )

            # STEP 14 — Append bot message
            st.session_state.messages.append({
                "role":    "assistant",
                "content": answer,
                "sources": sources_data,
                "intent":  intent,
                "lang":    lang,
                "time":    datetime.now().strftime("%I:%M %p"),
                "meta": {
                    "n_sources": len(chunks) if chunks else 0,
                    "avg_score": f"{avg_score}%",
                    "n_queries": len(queries),
                },
            })

            # STEP 15 — Persist to DynamoDB
            save_chat(
                st.session_state.session_id,
                st.session_state.session_title,
                st.session_state.messages
            )

        except Exception as e:
            st.session_state.messages.append({
                "role":    "assistant",
                "content": "⚠️ System unable to retrieve authentic Islamic data at the moment. Please try again.",
                "sources": [],
                "intent":  INTENT_GENERAL,
                "time":    datetime.now().strftime("%I:%M %p"),
                "meta":    {},
            })

    st.rerun()
