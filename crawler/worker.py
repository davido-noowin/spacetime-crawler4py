from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

#Peter: map domain to time last accessed for hopefully faster crawling
from urllib.parse import urlparse
from collections import defaultdict
DOMAIN_LAST_ACCESSED = defaultdict(float)


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        

    # 6. detect and avoid urls that return 200 but have no data
    # (pages that return a 200 code, but can't open)
    # fix in the download area
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            print(f"worker.run(): considering {tbd_url}")
            if not scraper.is_valid(tbd_url):
                print("worker.run(): Filtered by is_valid()")
                self.frontier.mark_url_complete(tbd_url)
                break

            #Peter: map domain to time last accessed for hopefully faster crawling
            domain = urlparse(tbd_url).netloc
            if (wait_time := self.config.time_delay - (time.time() - DOMAIN_LAST_ACCESSED[domain])) >= 0.0:
                time.sleep(wait_time)
            resp = download(tbd_url, self.config, self.logger)
            DOMAIN_LAST_ACCESSED[domain] = time.time()

            # if we encounter some error during the download, we skip this iteration
            if resp is False:
                self.logger.info(
                    f"Failed to download {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                self.frontier.mark_url_complete(tbd_url)    # mark complete, so we don't visit it again
                continue    # failed downloads (due to timeout error, too many redirects, other exceptions) do not get scraped

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            #Peter: map domain to time last accessed for hopefully faster crawling
            #time.sleep(self.config.time_delay)