"""
Text normalization utilities used for database-level normalized columns.

Normalization rules:
- Lowercase
- Strip leading/trailing whitespace
- Remove common ASCII punctuation and common Chinese punctuation
- Remove inner whitespace characters

This mirrors the fuzzy match behavior in services/shathyar_translator.py
so that queries can leverage precomputed normalized columns + indices.
"""

import string

# Common ASCII punctuation + common Chinese punctuation + whitespace
# Common Chinese punctuation plus extra look‑alike marks
_CHINESE_PUNCTS = "，。！？；：、（）【】《》〈〉—…·『』「」“”‘’　"

# Extra apostrophe/hyphen lookalikes seen in copy/paste text
# \u02BC: modifier letter apostrophe; \u02B9: modifier letter prime; \u201B: single high-reversed-9 quotation mark
# Various hyphen/minus dashes to normalize away
_EXTRA_STRIP = "ʼʹˈ`´ʾʿ‧‐‑‒–—―−﹘﹣"

_PUNCTUATIONS = string.punctuation + _CHINESE_PUNCTS + _EXTRA_STRIP + "\t\n\r "
_TRANS_TABLE = str.maketrans('', '', _PUNCTUATIONS)


def normalize_text(s: str) -> str:
    if not s:
        return ''
    lowered = s.lower().strip()
    cleaned = lowered.translate(_TRANS_TABLE)
    # Remove any remaining spaces (including full-width)
    cleaned = cleaned.replace(' ', '').replace('\u3000', '')
    return cleaned
