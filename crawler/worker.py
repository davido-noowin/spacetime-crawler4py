#Workerless: from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

#HARDCODE filters
import re


#map domain to time last accessed for hopefully faster crawling
from urllib.parse import urlparse
from collections import defaultdict
DOMAIN_LAST_ACCESSED = defaultdict(float)


# TODO ANGELA: ARE THESE NUMBERS GOOD?
# stop crawling if webpage takes too long to respond, download, scrape
import timeout_decorator            # pip install timeout-decorator
MAX_WEBPAGE_TIMEOUT = 10            # timeout period for each webpage
# AI Tutor suggested to use the timeout_decorator package (information on timeout_decorator was found through this link: https://pypi.org/project/timeout-decorator/)


#Workerless: class Worker(Thread):
class Worker:
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        #Workerless: super().__init__(daemon=True)


    @timeout_decorator.timeout(MAX_WEBPAGE_TIMEOUT)
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
        return download(tbd_url, self.config, self.logger)
        #DOMAIN_LAST_ACCESSED is updated in outside finally:


    def run(self):
        while True:
            #gets pair(url, bfs_depth)
            tbd_url, bfs_depth = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                return
            print(f"{'DEBUG':=^100}")

            if re.match(r"https://archive.ics.uci.edu/ml/datasets.php\?format=.*&task=.*&att=.*&area=.*&numAtt=.*&numIns=.*&type=.*&sort=.*&view=.*$", tbd_url) or \
                re.match(r"https://grape.ics.uci.edu/wiki/(asterix|public).*\?.*$", tbd_url) or \
                    tbd_url.startswith("https://swiki.ics.uci.edu/doku.php") or \
                        tbd_url.startswith("https://www.ics.uci.edu/community/news/view_news.php?id") or \
                            tbd_url.startswith("http://www.ics.uci.edu/download/download.inc.php?"):
                self.logger.info(f"HARDCODE {tbd_url}")
                print(f"HARDCODE {tbd_url}")
                continue

            #map domain to time last accessed for faster crawling
            domain = urlparse(tbd_url).netloc
            # we time accessing robots.txt and downloading each webpage
            try:
                # Attempt to access robots.txt and download each webpage
                resp = self.timeddownload(tbd_url, domain)

            except timeout_decorator.TimeoutError:
                # if download times out
                print(f"TIMEOUT ERROR: Downloading {tbd_url} did not complete within {MAX_WEBPAGE_TIMEOUT} seconds")
                resp = False

            finally:
                DOMAIN_LAST_ACCESSED[domain] = time.time()
                # if we cannot download, we skip this iteration
                # failed downloads (due to timeout error, too many redirects, other exceptions) do not get scraped
                if resp is False:
                    print(f"Failed to download {tbd_url}.")
                    #url, bfs_depth
                    self.frontier.mark_url_complete(tbd_url, bfs_depth)    # mark complete even if url timed out
                    continue
                else:
                    self.logger.info( f"{bfs_depth:<2}) Downloaded {tbd_url}, status <{resp.status}>, " f"using cache {self.config.cache_server}.")
                    scraped_urls = scraper.scraper(tbd_url, resp, bfs_depth)
                    for scraped_url in scraped_urls:
                        self.frontier.add_url(scraped_url, bfs_depth + 1)
                        
                    self.frontier.mark_url_complete(tbd_url, bfs_depth)