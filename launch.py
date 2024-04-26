from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

from time import sleep

def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)

    # TODO ANGELA: ARE THESE NUMBERS GOOD?
    retries_left = 5            # arbitrary 5 tries
    polite_sleep_period = 20    # each retry after sleeping for 20 sec
    while retries_left > 0:
        try:
            config.cache_server = get_cache_server(config, restart)
            crawler = Crawler(config, restart)
            crawler.start()
    
        # if server takes too long to connect, retry
        except StopIteration:
            retries_left -= 1
            print("Server timed out error")
            print(f"Retrying in 30 seconds. After this, {retries_left} retries remaining.")
            sleep(polite_sleep_period)

        # if server encounters a connection error, retry
        except Exception as e:
            retries_left -= 1
            print("Uncaught error occurred:")
            print(e)
            print(f"Retrying in 30 seconds. After this, {retries_left} retries remaining.")
            sleep(polite_sleep_period)

        # if server connection is successful, exit loop
        else:
            break


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
