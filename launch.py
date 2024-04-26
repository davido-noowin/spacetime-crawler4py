from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

from time import sleep

# TODO ANGELA: ARE THESE NUMBERS GOOD?
# stop program if server takes too long to connect
from concurrent.futures import ThreadPoolExecutor, TimeoutError
MAX_SERVER_TIMEOUT = 20 # timeout period for the server
# AI Tutor suggested to use concurrent.futures


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)

    # TODO ANGELA: ARE THESE NUMBERS GOOD?
    retries_left = 5            # arbitrary 5 tries
    polite_sleep_period = 20    # each retry after sleeping for 20 sec
    while retries_left > 0:

        # (ThreadPoolExecutor base code from AI Tutor)
        with ThreadPoolExecutor(max_workers=1) as executor:
            # Submit the function to the executor
            future = executor.submit(get_cache_server, config, restart)

            # attempt to connect to server with timeout
            try:
                config.cache_server = future.result(timeout=MAX_SERVER_TIMEOUT)
                crawler = Crawler(config, restart)
                crawler.start()

            # if server takes too long to connect, retry
            except TimeoutError:
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
    main(args.config_file, args.restart)
