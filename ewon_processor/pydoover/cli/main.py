import logging

from .cli import CLI

def main():
    logging.basicConfig(level=logging.INFO)
    CLI().main()