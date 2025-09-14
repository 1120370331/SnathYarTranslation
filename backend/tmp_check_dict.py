from src.db import get_db_session
from src.models.official_dictionary import OfficialDictionary

g = get_db_session()
db = next(g)
try:
    c = db.query(OfficialDictionary).count()
    print('dict_count', c)
    if c>0:
        rows = db.query(OfficialDictionary).limit(5).all()
        for r in rows:
            print(r.id, r.origin_cn[:20], '|', r.shathyar[:30])
finally:
    try:
        next(g)
    except StopIteration:
        pass
