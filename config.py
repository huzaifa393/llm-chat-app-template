"""
config.py — Central configuration for Islamic RAG Assistant
"""
import os

CHROMA_PATH      = "./chroma_db"
COLLECTION_NAME  = "islamic_texts"
LLM_MODEL        = "llama-3.3-70b-versatile"
LLM_TEMPERATURE  = 0.0
LLM_MAX_TOKENS   = 2000
DEFAULT_N_RESULTS   = 7
MIN_SCORE_THRESHOLD = 40.0
MIN_CHUNK_LENGTH    = 80
MAX_CONTEXT_CHARS   = 12000
MEMORY_TURNS        = 4
AWS_REGION   = os.getenv("AWS_REGION", "eu-north-1")
DYNAMO_TABLE = "islamic_rag_chats"

# Intent types
INTENT_HADITH    = "hadith"
INTENT_QURAN     = "quran"
INTENT_DUA       = "dua"
INTENT_FIQH      = "fiqh"
INTENT_TAFSEER   = "tafseer"
INTENT_MIXED     = "mixed"
INTENT_GENERAL   = "general"
INTENT_SMALLTALK = "smalltalk"

INTENT_META = {
    INTENT_HADITH:    ("📜", "Hadith",        "intent-hadith"),
    INTENT_QURAN:     ("📖", "Quran",          "intent-quran"),
    INTENT_DUA:       ("🤲", "Dua / Dhikr",   "intent-dua"),
    INTENT_FIQH:      ("⚖️",  "Fiqh / Ruling", "intent-fiqh"),
    INTENT_TAFSEER:   ("🔍", "Tafseer",        "intent-tafseer"),
    INTENT_MIXED:     ("📚", "Mixed Sources",  "intent-general"),
    INTENT_GENERAL:   ("💬", "General",        "intent-general"),
    INTENT_SMALLTALK: ("🕌", "About System",  "intent-general"),
}

# Strict type filters per intent — NO global retrieval
INTENT_TYPE_FILTER = {
    INTENT_HADITH:   ["hadith", "hadith_qudsi"],
    INTENT_QURAN:    ["quran"],
    INTENT_DUA:      ["dua"],                        # ONLY dua — never hadith for dua queries
    INTENT_FIQH:     ["fiqh", "hadith"],
    INTENT_TAFSEER:  ["tafseer", "quran"],
    INTENT_MIXED:    [],                             # all sources
    INTENT_GENERAL:  [],
}

# Source quality priority for ranking (lower = higher priority)
SOURCE_PRIORITY = {
    "quran":        1,
    "tafseer":      2,
    "hadith_qudsi": 3,
    "hadith":       4,
    "fiqh":         5,
    "dua":          6,
}

# Grade quality scores
GRADE_SCORES = {
    "sahih":        10,
    "sahih isnaad": 9,
    "hasan sahih":  8,
    "hasan":        7,
    "daif":         -5,
    "weak":         -5,
    "mawdu":        -10,
}

NOISE_PATTERNS = [
    "a hadith like this has been narrated",
    "this hadith has been narrated",
    "a similar hadith was narrated",
    "transmitted on the authority of",
    "like this has been transmitted",
    "(as above hadith)",
    "see previous hadith",
    "narrated it from the messenger of allah",
    "same hadith has been",
    "hadith has been transmitted on the authority",
]

SYSTEM_ABOUT = """
I am the **Islamic Knowledge Assistant** — a production-grade RAG system for Islamic scholarship and research.

**Knowledge Base:**
- 📜 **44,915 Hadith** — Bukhari, Muslim, Abu Dawud, Tirmidhi, Ibn Majah, Nasai, Ahmad, Malik, Darimi, Riyad as-Salihin, Bulugh al-Maram, Mishkat, Al-Adab Al-Mufrad, Shamail, Nawawi 40, 40 Hadith Qudsi
- 📖 **Quran** — English + Urdu + Muhammad Asad translation (6,236 verses)
- 🔍 **Tafseer** — Tafseer Ibn Kathir (6,236 entries)
- 🤲 **Dua & Dhikr** — Hisnul Muslim + Azkar (268 duas)
- ⚖️ **Fiqh** — Classical Islamic jurisprudence (6,900 entries)
- **Total: 60,000+ authenticated chunks**

**Languages:** Arabic, English, Urdu, Hindi, Roman Urdu

**How I work:** Every answer comes ONLY from retrieved authenticated sources. I never generate Islamic content from memory. Every response includes source, reference number, and grade.
"""
