import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None):
    host, port = config.cache_server
    try:
        s = requests.Session()
        s.max_redirects = 3     # sets the max number of redirects that a link can have to 3

        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            allow_redirects=True,          # allows for redirects
            timeout=0.001)                 # caps each download at a 0.001 second timeout
        
    except requests.TooManyRedirects:   # if a link exceeds the maximum number of redirects
        print("REDIRECT ERROR: Too Many Redirects")
        return False

    except requests.Timeout:    # if more than 0.001 seconds passes without receiving a byte, we raise a timeout error
        print("TIMEOUT ERROR: page timed out")
        return False
    
    except Exception as e:
        print(e)

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
