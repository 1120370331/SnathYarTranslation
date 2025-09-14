import asyncio
from src.db import get_db_session
from src.api.translate import create_services

samples = [
    "Aglathrax hig’ thrixa！",
    "  AGLATHRAX  hig'   thrixa.  ",
    "gul'kafh an'qov n'zoth",
]

async def run():
    gen = get_db_session()
    db = next(gen)
    try:
        services = create_services(db)
        translator = services['translator']
        for t in samples:
            try:
                res = await translator.translate(t, 'shathyar')
                print('OK:', t, '->', res.translated_text)
            except Exception as e:
                print('ERR:', t, type(e).__name__, str(e))
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

asyncio.run(run())
