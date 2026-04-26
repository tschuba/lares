import asyncio
import sys
from typing import List, Optional

from loguru import logger

from meross2homie.config import CONFIG
from meross2homie.manager import BridgeManager


def main(argv: Optional[List[str]] = None):
    logger.remove()

    if argv is None:
        argv = sys.argv[1:]

    if "-h" in argv or "--help" in argv:
        print(f"Usage: {sys.argv[0]} [config file]")
        return 0

    if argv:
        CONFIG.load(argv[0])
    else:
        CONFIG.load()

    logger.add(sys.stderr, level=CONFIG.log_level)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(amain())
    except (KeyboardInterrupt, EOFError):
        pass


async def amain():
    while True:
        # noinspection PyBroadException
        try:
            async with BridgeManager() as manager:
                await manager.process_events()
        except (KeyboardInterrupt, EOFError):
            logger.info("Exiting")
            break
        except Exception:
            logger.exception("Unhandled error; reconnecting in 5 seconds")
            await asyncio.sleep(5)
