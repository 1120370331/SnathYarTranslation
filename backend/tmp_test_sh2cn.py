import asyncio
from src.db import get_db_session
from src.api.translate import create_services

async def run(text):
    gen = get_db_session()
    db = next(gen)
    try:
        services = create_services(db)
        translator = services['translator']
        res = await translator.translate(text, 'shathyar')
        print('OK:', res.translated_text)
    except Exception as e:
        print('ERR:', type(e).__name__, str(e))
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

asyncio.run(run("Gul'kafh an'qov N'zoth."))
