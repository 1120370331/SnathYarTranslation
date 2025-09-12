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
_CHINESE_PUNCTS = "，。！？；：、（）【】《》〈〉—…·『』「」“”‘’　"
_PUNCTUATIONS = string.punctuation + _CHINESE_PUNCTS + "\t\n\r "
_TRANS_TABLE = str.maketrans('', '', _PUNCTUATIONS)


def normalize_text(s: str) -> str:
    if not s:
        return ''
    lowered = s.lower().strip()
    cleaned = lowered.translate(_TRANS_TABLE)
    # Remove any remaining spaces (including full-width)
    cleaned = cleaned.replace(' ', '').replace('\u3000', '')
    return cleaned
