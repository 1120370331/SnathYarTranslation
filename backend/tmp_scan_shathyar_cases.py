import asyncio
from src.db import get_db_session
from src.models.official_dictionary import OfficialDictionary
from src.models.translation_entry import TranslationEntry
from src.api.translate import create_services

async def main():
    g = get_db_session(); db = next(g)
    try:
        services = create_services(db)
        translator = services['translator']
        cases = []
        # From official dictionary
        dict_rows = db.query(OfficialDictionary).limit(50).all()
        cases += [(r.shathyar, 'dict') for r in dict_rows]
        # From user entries where source_language='shathyar'
        user_sh_rows = db.query(TranslationEntry).filter(TranslationEntry.source_language=='shathyar').limit(50).all()
        cases += [(r.source_text, 'user_sh_src') for r in user_sh_rows]
        # From user entries where source_language='chinese' (use translated_text as shathyar)
        user_cn_rows = db.query(TranslationEntry).filter(TranslationEntry.source_language=='chinese').limit(50).all()
        cases += [(r.translated_text, 'user_cn_rev') for r in user_cn_rows]
        failed = []
        for i,(txt,src) in enumerate(cases):
            try:
                res = await translator.translate(txt, 'shathyar')
                # Print only a few successes
                if i<3:
                    print('OK', src, '->', res.translated_text[:50])
            except Exception as e:
                failed.append((src, txt, type(e).__name__, str(e)))
        print('total cases', len(cases), 'failed', len(failed))
        for item in failed[:10]:
            print('FAIL', item[0], '|', item[2], '|', item[1][:80], '|', item[3])
    finally:
        try:
            next(g)
        except StopIteration:
            pass

asyncio.run(main())
