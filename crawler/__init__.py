from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker


class Crawler(object):
    #workerless: unchanged to keep original structure
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory

    #workerless: much unchanged to keep the original structure, but there is no async work
    def start_async(self):
        self.workers = [self.worker_factory(worker_id, self.config, self.frontier) for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            #workerless: worker.start()
            worker.run()

    def start(self):
        self.start_async()
        self.join()     

    #workerless: useless function just to keep the original structure
    def join(self):
        pass
        # for worker in self.workers:
        #     worker.join()