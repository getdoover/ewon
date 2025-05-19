import logging

from .cli import CLI

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    CLI().main()
