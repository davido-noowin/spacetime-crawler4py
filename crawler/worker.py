from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
import urllib.robotparser


#map domain to time last accessed for hopefully faster crawling
from urllib.parse import urlparse
from collections import defaultdict
DOMAIN_LAST_ACCESSED = defaultdict(float)


# TODO ANGELA: ARE THESE NUMBERS GOOD?
# stop crawling if webpage takes too long to respond, download, scrape
from concurrent.futures import ThreadPoolExecutor, TimeoutError
MAX_WEBPAGE_TIMEOUT = 30 # timeout period for each webpage
# AI Tutor suggested to use concurrent.futures


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)


    def timeddownload(self, tbd_url, domain):
        '''
        Accesses robots.txt and the webpage contents within a given timeout period.
        Returns False if we are prohibited to access the webpage, otherwise returns its contents.
        '''
        if (wait_time := self.config.time_delay - (time.time() - DOMAIN_LAST_ACCESSED[domain])) >= 0.0:
            time.sleep(wait_time)

        #Michael: check if robots.txt file says it's okay to crawl before downloading
        if not scraper.checkRobotsTxt(tbd_url):
            print("This URL cannot be crawled due to robots.txt")
            return False
        
        time.sleep(self.config.time_delay) #robots check, and then download
        
        # download file contents
        resp = download(tbd_url, self.config, self.logger)
        #TODO TODO TODO in try except catching timeout-decorator, finally: set DOMAIN_LAST_ACCESSED[domain] = time.time()
        DOMAIN_LAST_ACCESSED[domain] = time.time()  # update when the domain last accessed
        return resp


    def run(self):
        while True:
            #gets pair(url, bfs_depth)
            tbd_url, bfs_depth = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            print(f"{'DEBUG':=^100}")

            #map domain to time last accessed for faster crawling
            domain = urlparse(tbd_url).netloc

            # we time accessing robots.txt and downloading each webpage
            # (ThreadPoolExecutor base code from AI Tutor)
            with ThreadPoolExecutor(max_workers=1) as executor:
                # Submit the download function to the executor
                future = executor.submit(self.timeddownload, tbd_url, domain)
                
                try:
                    # Attempt to access robots.txt and download each webpage (timer starts here)
                    resp = future.result(timeout=MAX_WEBPAGE_TIMEOUT)

                except TimeoutError:
                    # if download times out
                    print(f"TIMEOUT ERROR: Downloading {tbd_url} did not complete within {MAX_WEBPAGE_TIMEOUT} seconds")
                    resp = False

                finally:
                    # if we cannot download, we skip this iteration
                    if resp is False:
                        print(
                            f"Failed to download {tbd_url}.")
                        #url, bfs_depth
                        self.frontier.mark_url_complete(tbd_url, bfs_depth)    # mark complete even if url timed out
                        continue
                        
                    else:
                        self.logger.info(
                            f"Downloaded {tbd_url}, status <{resp.status}>, "
                            f"using cache {self.config.cache_server}.")
                        scraped_urls = scraper.scraper(tbd_url, resp, bfs_depth)
                        for scraped_url in scraped_urls:
                            self.frontier.add_url(scraped_url, bfs_depth + 1)

                        self.frontier.mark_url_complete(tbd_url, bfs_depth)

                        #map domain to time last accessed for hopefully faster crawling
                        #time.sleep(self.config.time_delay)