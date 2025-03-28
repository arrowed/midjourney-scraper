import argparse
import logging
import os

from dotenv import load_dotenv

from scraper.commands import command_arg_parsers


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--env', dest='envfile', type=str, default='.env',
                        help='Path to the configuration file')

    subparsers = parser.add_subparsers(dest='command')

    for command_class in command_arg_parsers:  # pylint: disable=possibly-used-before-assignment
        impl = command_class()
        subparser = subparsers.add_parser(impl.name, help=impl.help)
        impl.add_arguments(subparser)

    return parser


def main() -> None:

    parser = get_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not load_dotenv(args.envfile):
        logging.error("Could not load environment file %s", args.config)
        return

    [command for command in command_arg_parsers if command().name ==
     args.command][0]().run(args)


def init_logging():

    os.makedirs("log", exist_ok=True)

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)

    logging.getLogger('discord.http').setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(
        filename='log/discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(
        '[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    discord_logger.addHandler(handler)

    return discord_logger


if __name__ == '__main__':
    init_logging()
    main()
