"""
translator.py — Multilingual agent
Detects language → translates query to English → translates answer back.
Translation is LITERAL only — no paraphrasing or interpretation.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from intent import detect_language
from config import LLM_MODEL
import os

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=LLM_MODEL,
            temperature=0.0,
            max_tokens=800
        )
    return _llm


TRANSLATE_TO_ENGLISH = PromptTemplate(
    input_variables=["lang", "text"],
    template="""Translate the following {lang} text to English.
Rules:
- Provide ONLY the English translation, nothing else.
- Keep Islamic terms as-is: Allah, Prophet, Salah, Zakat, Hadith, Quran, etc.
- Do NOT add explanations, notes, or commentary.
- Translate literally and accurately.

Text to translate:
{text}

English translation:"""
)

TRANSLATE_TO_LANG = PromptTemplate(
    input_variables=["lang", "text"],
    template="""Translate the following English Islamic text to {lang}.
Rules:
- Provide ONLY the translation, nothing else.
- Keep Islamic terms in their original Arabic form: Allah, Prophet ﷺ, Salah, etc.
- Keep all citations intact: (Sahih Bukhari #123), (Quran 2:255), etc.
- Do NOT add explanations or commentary.
- Translate literally and accurately.
- Keep Arabic text blocks [Arabic] exactly as-is — do not translate Arabic script.

Text to translate:
{text}

{lang} translation:"""
)

TRANSLATE_ARABIC_ONLY = PromptTemplate(
    input_variables=["arabic_text"],
    template="""Translate ONLY this Arabic Islamic text to English literally.
Rules:
- Literal translation only — no interpretation, no explanation.
- Keep Arabic honorifics: ﷺ, رضي الله عنه, etc.
- Output ONLY the English translation.

Arabic text:
{arabic_text}

Literal English translation:"""
)


def translate_to_english(text: str, lang: str) -> str:
    """Translate query to English for ChromaDB search."""
    if lang == "english":
        return text
    try:
        chain = TRANSLATE_TO_ENGLISH | _get_llm() | StrOutputParser()
        lang_names = {
            "arabic": "Arabic", "urdu": "Urdu",
            "hindi": "Hindi", "roman_urdu": "Roman Urdu (Hinglish)"
        }
        result = chain.invoke({
            "lang": lang_names.get(lang, lang),
            "text": text
        })
        return result.strip() or text
    except Exception:
        return text


def translate_answer(answer: str, target_lang: str) -> str:
    """Translate final answer back to user's language."""
    if target_lang == "english":
        return answer
    try:
        chain = TRANSLATE_TO_LANG | _get_llm() | StrOutputParser()
        lang_names = {
            "arabic": "Arabic", "urdu": "Urdu",
            "hindi": "Hindi", "roman_urdu": "Roman Urdu (Hinglish)"
        }
        result = chain.invoke({
            "lang": lang_names.get(target_lang, target_lang),
            "text": answer
        })
        return result.strip() or answer
    except Exception:
        return answer


def translate_arabic_chunk(arabic_text: str) -> str:
    """Translate Arabic text found in retrieved chunk to English literally."""
    if not arabic_text or len(arabic_text.strip()) < 10:
        return ""
    try:
        chain = TRANSLATE_ARABIC_ONLY | _get_llm() | StrOutputParser()
        result = chain.invoke({"arabic_text": arabic_text})
        return result.strip()
    except Exception:
        return ""
