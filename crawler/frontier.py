import os
import shelve

from threading import Thread, RLock
#Peter: using Queue
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

#Peter: updated to do BFS, with depths

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = Queue()
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                #Peter: seeds get bfs_depth 0
                self.add_url(url, 0)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    #Peter: seeds get bfs_depth 0
                    self.add_url(url, 0)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        #Peter: save file has triplet (url, completed, bfs_depth)
        for url, completed, bfs_depth in self.save.values():
            if not completed and is_valid(url):
                #Peter: appending pair (url, bfs_depth)
                self.to_be_downloaded.put((url, bfs_depth))
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    #Peter: returns pair (url, bfs_depth)
    def get_tbd_url(self):
        try:
            #he skeleton function also returned None upon IndexError. default block=True blocks indefinitely
            return self.to_be_downloaded.get(block=False)
        except:
            return None

    #Peter: now takes url, bfs_depth instead of url
    def add_url(self, url, bfs_depth):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            #Peter: saves triplet (url, complete, bfs_depth)
            self.save[urlhash] = (url, False, bfs_depth)
            self.save.sync()
            #Peter: appends pair(url, bfs_depth)
            self.to_be_downloaded.put((url, bfs_depth))
    
    #Peter: now takes url, bfs_depth instead of url
    def mark_url_complete(self, url, bfs_depth):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        #Peter: saves triplet (url, complete, bfs_depth)
        self.save[urlhash] = (url, True, bfs_depth)
        self.save.sync()
