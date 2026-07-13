"""
chains.py — Zero-hallucination LangChain RAG chains.
One chain per intent. LLM = FORMATTER ONLY, not generator.
Context is pre-separated by type before prompting.
"""
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from config import (INTENT_HADITH, INTENT_QURAN, INTENT_DUA,
                    INTENT_FIQH, INTENT_TAFSEER, INTENT_MIXED, INTENT_GENERAL)

_ZERO_HAL_RULES = """
╔══════════════════════════════════════════════════════════╗
║           ABSOLUTE ZERO-HALLUCINATION RULES              ║
╠══════════════════════════════════════════════════════════╣
║ 1. USE ONLY the exact text from RETRIEVED SOURCES below  ║
║ 2. NEVER write Arabic text not present in the sources    ║
║ 3. NEVER invent hadith numbers, citations, or references ║
║ 4. NEVER generate rulings from LLM memory               ║
║ 5. NEVER add "scholars say" unless in retrieved sources  ║
║ 6. If answer NOT in sources → output ONLY:               ║
║    "Not found in retrieved texts."                       ║
║ 7. You are a PRESENTER of retrieved text — NOT a scholar ║
║ 8. Da'if (weak) hadith MUST be flagged clearly           ║
╚══════════════════════════════════════════════════════════╝
"""

# ── HADITH CHAIN ──────────────────────────────────────
_HADITH_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting authentic hadith from the retrieved database. Present ONLY what is in the sources.

OUTPUT FORMAT — repeat this block for each relevant hadith found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Hadith:**
[paste exact English text from source — never paraphrase]

**Arabic Text:**
[paste [Arabic] block exactly if present — omit section if not in source]

**Source:** [Book name] | **Ref:** #[number] | **Grade:** [grade or "Not specified"]
**Narrator:** [if mentioned in source text]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Write ﷺ after every mention of the Prophet
- Write رضي الله عنه / رضي الله عنها after Companions
- If grade is Da'if → add: ⚠️ This hadith is graded Da'if (weak) — treat with caution
- If multiple hadiths found → present each in the above format
- If nothing relevant found → write ONLY: "No relevant hadith found in retrieved texts."
- DO NOT add commentary, context, or explanation beyond what is in the sources

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED HADITH SOURCES — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

# ── QURAN CHAIN ───────────────────────────────────────
_QURAN_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting Quranic verses from the retrieved database.

OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Arabic:**
[paste Arabic text EXACTLY as in source — character for character — omit if not present]

**Translation:**
[paste English translation EXACTLY as in source — never rewrite it]

**Reference:** Quran [Surah Name] [chapter]:[verse]
**Translation by:** [source dataset name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- NEVER alter a single character of Quranic Arabic text
- NEVER rewrite or paraphrase the translation
- If multiple translations found for same verse → present each separately with source
- If nothing found → write ONLY: "No matching Quranic verse found in retrieved texts."

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED QURAN SOURCES — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

# ── DUA CHAIN ─────────────────────────────────────────
_DUA_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting duas (supplications) from Hisnul Muslim and Azkar collections.

OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Occasion:** [when this dua is read — from source]

**Arabic:**
[Arabic text EXACTLY as in source — if not in source write: "Arabic text not available in database"]

**Transliteration:**
[transliteration EXACTLY as in source — omit if not present]

**Translation:**
[English translation EXACTLY as in source]

**Reference:** [Hisnul Muslim #number / source name]
**Repetitions:** [times to recite — if mentioned, else omit]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Present ONLY duas from retrieved sources
- NEVER generate Arabic text — only paste from sources
- NEVER invent a dua not in retrieved texts
- If not found → write ONLY: "This specific dua was not found in the retrieved Hisnul Muslim or Azkar database."
- Do NOT suggest hadith as substitute for a dua query

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED DUA SOURCES — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved duas):"""
)

# ── FIQH CHAIN ────────────────────────────────────────
_FIQH_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting Islamic jurisprudence (Fiqh) information from the retrieved database.

⚠️ MANDATORY FIRST LINE: "📚 Educational Reference Only — Not a Fatwa. Consult a qualified Islamic scholar for personal rulings."

OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Ruling from Retrieved Sources:**
[present exactly what the fiqh source says — do not paraphrase]

**Supporting Evidence:**
[list relevant hadiths or Quranic evidence from retrieved context with full references]

**Source:** [Book name] | **Ref:** #[number] | **Grade:** [if hadith]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Present ONLY what is in the retrieved fiqh and hadith sources
- Clearly flag any Da'if hadith used as evidence: ⚠️ Da'if (weak)
- If different madhab positions appear in sources → present each clearly labeled
- NEVER issue a personal ruling or fatwa
- If not found → write ONLY: "No fiqh ruling found in retrieved texts. Please consult a qualified Islamic scholar."

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED FIQH SOURCES — USE ONLY THESE
[Note: Sources are separated by type — fiqh sources take priority]
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

# ── TAFSEER CHAIN ─────────────────────────────────────
_TAFSEER_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting Quranic tafseer (exegesis) from Tafseer Ibn Kathir and authenticated sources.

OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Verse:** Quran [Surah]:[Ayah]

**Arabic:**
[Arabic text exactly as in source — omit if not present]

**Translation:**
[Translation exactly as in source — never rewrite]

**Tafseer (Ibn Kathir):**
[paste the tafseer text EXACTLY as retrieved — do not summarize]

**Source:** [Book name] | **Ref:** [number/verse]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Tafseer text must be pasted EXACTLY — do not summarize or paraphrase
- If multiple tafseer entries found → present all
- NEVER add personal interpretation of any verse
- If not found → write: "Tafseer for this verse was not found in the retrieved database."

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED TAFSEER SOURCES — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

# ── MIXED CHAIN ───────────────────────────────────────
_MIXED_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting Islamic knowledge from multiple authenticated source types.
Present sources in order: Quran → Tafseer → Hadith → Fiqh → Dua

For EACH source present:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**[Source Type]:** [Book name] | **Ref:** #[number] | **Grade:** [if hadith]
[paste exact text from source]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Present ONLY what is in the retrieved sources
- Clearly label each source type
- Write ﷺ after Prophet's name
- Flag Da'if hadiths with ⚠️
- If nothing found → write: "No relevant Islamic sources found in retrieved texts."

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED SOURCES (SEPARATED BY TYPE) — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

# ── GENERAL CHAIN ─────────────────────────────────────
_GENERAL_PROMPT = PromptTemplate(
    input_variables=["context", "question", "history"],
    template=_ZERO_HAL_RULES + """
You are presenting Islamic knowledge from authenticated databases.

For each relevant source found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[paste exact text from source]
**Source:** [Book name] | **Ref:** #[number] | **Grade:** [if applicable]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Present ONLY retrieved content
- Write ﷺ after Prophet's name
- Flag Da'if hadiths clearly
- If nothing found → write: "Not found in retrieved Islamic texts. Please consult a qualified Islamic scholar."

Previous conversation: {history}

════════════════════════════════════════
RETRIEVED SOURCES — USE ONLY THESE
════════════════════════════════════════
{context}

════════════════════════════════════════
QUESTION: {question}
════════════════════════════════════════
ANSWER (present only retrieved content):"""
)

_PROMPTS = {
    INTENT_HADITH:  _HADITH_PROMPT,
    INTENT_QURAN:   _QURAN_PROMPT,
    INTENT_DUA:     _DUA_PROMPT,
    INTENT_FIQH:    _FIQH_PROMPT,
    INTENT_TAFSEER: _TAFSEER_PROMPT,
    INTENT_MIXED:   _MIXED_PROMPT,
    INTENT_GENERAL: _GENERAL_PROMPT,
}


def build_chains(groq_api_key: str) -> dict:
    llm = ChatGroq(
        api_key=groq_api_key,
        model_name=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS
    )
    parser = StrOutputParser()
    return {intent: (prompt | llm | parser) for intent, prompt in _PROMPTS.items()}
