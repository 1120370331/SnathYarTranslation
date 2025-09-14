import asyncio
from src.db import get_db_session
from src.api.translate import create_services

async def run():
    gen = get_db_session()
    db = next(gen)
    try:
        services = create_services(db)
        translator = services['translator']
        # Assume previous Chinese->Shathyar created this
        sh = "Vael'eth, kyr'ath."
        res = await translator.translate(sh, 'shathyar')
        print('OK:', sh, '->', res.translated_text)
    except Exception as e:
        print('ERR:', type(e).__name__, str(e))
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

asyncio.run(run())
