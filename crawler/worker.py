from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
import urllib.robotparser


#Peter: map domain to time last accessed for hopefully faster crawling
from urllib.parse import urlparse
from collections import defaultdict
DOMAIN_LAST_ACCESSED = defaultdict(float)


# TODO ANGELA: ARE THESE NUMBERS GOOD?
# stop crawling if webpage takes too long to respond, download, scrape
import timeout_decorator            # pip install timeout-decorator
MAX_WEBPAGE_TIMEOUT = 30            # timeout period for each webpage
# AI Tutor suggested to use the timeout_decorator package (information on timeout_decorator was found through this link: https://pypi.org/project/timeout-decorator/)


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)


    @timeout_decorator.timeout(MAX_WEBPAGE_TIMEOUT, timeout_exception=StopIteration)
    def timeddownload(self, tbd_url, domain):
        '''
        Accesses robots.txt and the webpage contents within a given timeout period.
        Returns False if we are prohibited to access the webpage, otherwise returns its contents.
        '''
        #Michael: check if robots.txt file says it's okay to crawl before downloading
        if not scraper.checkRobotsTxt(tbd_url):
            print("This URL cannot be crawled due to robots.txt")
            return False
        
        resp = download(tbd_url, self.config, self.logger)
        DOMAIN_LAST_ACCESSED[domain] = time.time()
        return resp


    def run(self):
        while True:
            #Peter: gets pair(url, bfs_depth)
            tbd_url, bfs_depth = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            #Peter: map domain to time last accessed for hopefully faster crawling
            domain = urlparse(tbd_url).netloc
            if (wait_time := self.config.time_delay - (time.time() - DOMAIN_LAST_ACCESSED[domain])) >= 0.0:
                time.sleep(wait_time)


            # we time accessing robots.txt and downloading each webpage
            try:
                resp = self.timeddownload(tbd_url, domain)
            
            # if either takes too long, we stop this iteration
            except StopIteration:
                print("PAGE EXCEEDED THE MAXIMUM TIMEOUT PERIOD")

            finally:
                # if we cannot download, we skip this iteration
                if resp is False:
                    self.logger.info(
                        f"Failed to download {tbd_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")
                    #Peter: url, bfs_depth
                    self.frontier.mark_url_complete(tbd_url, bfs_depth)    # mark complete even if url timed out
                    continue                                               # failed downloads (due to timeout error, too many redirects, other exceptions) do not get scraped
                    
                else:
                    #Peter: pretty print
                    #TODO should move this a bit higher. for example, robot output groups under the previous url not this one
                    print(f"{'DEBUG':=^100}")
                    self.logger.info(
                        f"Downloaded {tbd_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")
                    #Peter: takes url, resp, bfs_depth
                    scraped_urls = scraper.scraper(tbd_url, resp, bfs_depth)
                    for scraped_url in scraped_urls:
                        #Peter: appends pair (url, bfs_depth + 1)
                        self.frontier.add_url(scraped_url, bfs_depth + 1)

                    self.frontier.mark_url_complete(tbd_url, bfs_depth)

                    #Peter: map domain to time last accessed for hopefully faster crawling
                    #time.sleep(self.config.time_delay)