"""Punto de entrada: python main.py"""

import logging

from crypto_bot.bot import Bot
from crypto_bot.config import Config


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    Bot(Config.from_env()).run()


if __name__ == "__main__":
    main()
