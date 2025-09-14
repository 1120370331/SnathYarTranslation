from src.db import get_db_session
from src.models.translation_entry import TranslationEntry

g=get_db_session(); db=next(g)
try:
    total = db.query(TranslationEntry).count()
    sh_cnt = db.query(TranslationEntry).filter(TranslationEntry.source_language=='shathyar').count()
    cn_cnt = db.query(TranslationEntry).filter(TranslationEntry.source_language=='chinese').count()
    print('entries_total', total, 'shathyar_src', sh_cnt, 'chinese_src', cn_cnt)
    rows = db.query(TranslationEntry).filter(TranslationEntry.source_language=='shathyar').limit(5).all()
    for r in rows:
        print('sh_src', r.source_text[:50], '->', r.translated_text[:50])
    rows2 = db.query(TranslationEntry).filter(TranslationEntry.source_language=='chinese').limit(5).all()
    for r in rows2:
        print('cn_src', r.source_text[:50], '->', r.translated_text[:50])
finally:
    try:
        next(g)
    except StopIteration:
        pass
