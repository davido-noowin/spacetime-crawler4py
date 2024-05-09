import requests
import cbor
import time

from utils.response import Response

MAX_REDIRECT = 10
MAX_TIMEOUT_SECONDS = 10
MAX_BYTE_SIZE = 1000000

# # determines whether or not to open a link based on its size
# def checkLinkSize(url: str, host, port, config) -> bool:
#     '''
#     Preliminary check to see if the url is too large.
#     Files that do not have a Content-Length header section will still try to be opened,
#     but if it takes too long then open will stop elsewhere.
#     Returns False if file is too large, otherwise True.
#     '''
#     response = requests.head(f"http://{host}:{port}/",
#             params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
#             allow_redirects=True,               # allows for redirects
#             timeout=MAX_TIMEOUT_SECONDS)        # caps each download at a 20 second timeout
    
#     size = response.headers.get('Content-Length')   # gets content length information from the header

#     try:
#         size = int(size)
#     except:
#         return True     # if there is no Content-Length portion in the header, then we still crawl that link
#     else:
#         return False if size > MAX_BYTE_SIZE else True    # sets the threshold for the maximum size of a url to be 1MB


def download(url, config, logger=None):
    host, port = config.cache_server
    try:
        s = requests.Session()
        s.max_redirects = MAX_REDIRECT     # sets the max number of redirects that a link can have to 10

        # # if content is too large and exceeds a max size of 1MB, raise error
        # if not checkLinkSize(url, host, port, config):
        #     raise Exception('File is too big')
        
        # time.sleep(config.time_delay) #between HEAD and GET

        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            allow_redirects=True,               # allows for redirects
            timeout=MAX_TIMEOUT_SECONDS)        # caps each download at a 20 second timeout
        
        logger.info(f"Pages {[(f'{r.url} (code:{r.status_code}), ') for r in resp.history]} redirected us to {f'{resp.url} (code:{resp.status_code})'}")

        
    except requests.TooManyRedirects:   # if a link exceeds the maximum number of redirects
        print("REDIRECT ERROR: Too Many Redirects")
        return False

    except requests.Timeout:    # if more than 20 seconds passes without receiving a response, we raise a timeout error
        print("TIMEOUT ERROR: Page Timed Out")
        return False
    
    except Exception as e:      # if there are other exceptions, return false to worker.py
        print(e)
        return False

    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError) as e:
        pass
    logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": resp.status_code,
        "url": url})