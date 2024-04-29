from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server, MAX_SERVER_TIMEOUT
from utils.config import Config
from crawler import Crawler

from time import sleep

# stop program if server takes too long to connect
import timeout_decorator


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)

    # TODO ANGELA: ARE THESE NUMBERS GOOD?
    retries_left = 5            # arbitrary 5 tries
    polite_sleep_period = 20    # each retry after sleeping for 20 sec
    while retries_left > 0:
        try:
            # attempt to connect to server with timeout
            config.cache_server = get_cache_server(config, restart)
            crawler = Crawler(config, restart)
            crawler.start()

        # if server takes too long to connect, retry
        except timeout_decorator.TimeoutError:
            retries_left -= 1
            print(f"TIMEOUT ERROR: server timed out with over {MAX_SERVER_TIMEOUT} seconds")
            print(f"Retrying in {polite_sleep_period} seconds. After this, {retries_left} retries remaining.")
            sleep(polite_sleep_period)
    
        # if server encounters a connection error, retry
        except Exception as e:
            retries_left -= 1
            print("Uncaught error occurred:")
            print(e)
            print(f"Retrying in {polite_sleep_period} seconds. After this, {retries_left} retries remaining.")
            sleep(polite_sleep_period)

        # if server connection is successful, exit loop
        else:
            break


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    print(f"{'LAUNCH.MAIN() ENTER':=^100}") #debug
    main(args.config_file, args.restart)
    print(f"{'LAUNCH.MAIN() EXIT':=^100}")  #debug