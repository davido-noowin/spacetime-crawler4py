import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None):
    host, port = config.cache_server
    try:
        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            allow_redirects=True,          # allows for redirects
            timeout=30)                    # caps each download at a 30 second timeout, so if more than 30 seconds passes without receiving bytes, then we stop
    except requests.TooManyRedirects:
        pass
        print("REDIRECT ERROR: Too Many Redirects")

    except requests.Timeout:
        pass
        print("TIMEOUT ERROR: page timed out")

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
