from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker

#Peter: crash recovery
from time import sleep

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        #Peter: crash recovery
        #  arbitrary 1000 tries, each after sleeping for 30 sec
        #  TODO verify with group
        retries_left = 1000
        while (retries_left > 0):
            try:
                self.start_async()
                self.join()
            except Exception as e:
                retries_left -= 1
                print("Uncaught error occurred:")
                print(e)
                print(f"Retrying in one minute. After this, {retries_left} retries remaining.")
                sleep(30)

    def join(self):
        for worker in self.workers:
            worker.join()
