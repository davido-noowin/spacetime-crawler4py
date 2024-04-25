import re
import shelve
import fnmatch
import pickle
from utils.response import Response # located in the utils folder
from urllib.parse import urlparse, urlunparse, urljoin
from bs4 import BeautifulSoup
import urllib.robotparser



DOMAINS = ['*.ics.uci.edu/*', 
          '*.cs.uci.edu/*', 
          '*.informatics.uci.edu/*', 
          '*.stat.uci.edu/*']

#TODO have to tune
MAX_BFS_DEPTH = 5000

#Peter: might have to tune. the closer to 1, the more stringent
URL_DISSIMILARITY_MINIMUM = 0.8


unique_urls = set()

def checkPath(url: str) -> bool:
    '''
    Checks the provided url and determines whether it is a relative path or absolute path.
    '''
    return True if re.search("(?:[a-z]+:)?//", url) else False


def convertRelativeToAbsolute(url: str, possibleUrl: str) -> str:
    '''
    Converts a relative path to an absolute path so that we can crawl it
    '''
    return urljoin(url, possibleUrl)


def checkRobotsTxt(url: str) -> bool:
    '''
    Sets robot parser object to robot.txt url, then checks if it can be crawled
    '''
    robotUrl = getRobotsUrl(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robotUrl)
    try:
        rp.read()
        return rp.can_fetch("*", url)
    except Exception as e:
        print("Can't find robots.txt, proceed to crawl")
        return True
    
    
def getRobotsUrl(url:str) -> str:
    '''
    Attemps to replace url path with "robots.txt"
    '''
    try:
        parsed_url = urlparse(url)
        parsed_url = parsed_url._replace(path='/robots.txt')
        return urlunparse(parsed_url)
    except Exception as e:
        print("Can't complete robots.txt url replacement")
        return 
    
    
def lowInformationValue(parsed_html: BeautifulSoup) -> bool:
    return False #TODO
    

def isValidDomain(url: str) -> bool:
    '''
    Checks to see if the domains collected from the sites are within the sites specified by the project
    '''
    for pattern in DOMAINS:
        if fnmatch.fnmatch(url, pattern):
            return True
    return False

#TODO also want text tag ratio and still a depth cap as a fallback
def urlsDifferentEnough(parent, child):
    #if child and parent are identical up to the query, then no
    if (parent[:parent.rfind('?')] == child[:child.rfind('?')]):
        return False
    #if child has too many recurring tokens, then no
    toks = child[child.find("//") + 2:].split('/')
    if len(set(toks)) / len(toks) < URL_DISSIMILARITY_MINIMUM:
        return False
    return True


def removeFragment(url: str) -> str:
    '''
    Removes the fragment from a url
    '''
    parsed_url = urlparse(url)
    # Remove fragment from the URL
    clean_url = urlunparse(parsed_url._replace(fragment=''))
    return clean_url

#Peter: takes url, resp, bfs_depth
def scraper(url: str, resp: Response, bfs_depth: int) -> list:
    #Peter: takes url, resp, bfs_depth
    # correct and intentional to have a list of only url's without bfs_depth here; that is handled in worker.py
    return extract_next_links(url, resp, bfs_depth)
    #links = extract_next_links(url, resp)
    #return [link for link in  links if is_valid(link)]


#Peter: takes url, resp, bfs_depth
def extract_next_links(url, resp, bfs_depth):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    '''
    HOW TO APPROACH THIS FUNCTION:

    1. Make an HTTP GET request to the target webpage to get the HTML content.
    2. Create a Beautiful Soup object from the HTML content.
    3. Use the object to find all `<a>` elements.
    4. For each `<a>` element, extract the URL found in the `href` attribute.
    5. Resolve any relative URLs to absolute URLs.
    6. Optionally, filter out any URLs that are not of interest or are disallowed.
    7. Choose the next URL to visit from the remaining list of URLs.

    '''
    print(f'\nDEBUG: url - {url} \nresponse url - {resp.url} \nresponse status - {resp.status} \nresponse error - {resp.error}\n bfs_depth - {bfs_depth}\n')
    list_of_urls = []

    #Peter: used to hardcode against some traps for now to see how many there are
    #  not good, but i am just trying to find patterns

    #Peter: bfs pruning happens here
    if bfs_depth >= MAX_BFS_DEPTH:
        return []

    if resp.status == 200:
        print("ACCESSING VALID URL")
        parsed_html = BeautifulSoup(resp.raw_response.content, "html.parser")

        #TODO should this happen after the BeautifulSoup?
        # check if robots.txt file says it's okay to crawl
        if not checkRobotsTxt(resp.url):
            print("This URL cannot be crawled due to robots.txt")
            return []
        
        #TODO PETER if no significant content, return []
        #  TODO check with group
        if lowInformationValue(parsed_html):
            print("THIS URL WILL NOT BE CRAWLED DUE TO LOW INFORMATION VALUE.")
            return []

        before_urlsDifferentEnough = 0
        for link in parsed_html.find_all('a', href=True):
            possible_link = link['href']
            actual_link = ''
            if not checkPath(possible_link):
                # if the path is not a valid absolute path then we manipulate it so that it becomes one
                actual_link = convertRelativeToAbsolute(url, possible_link)
            else:
                actual_link = possible_link

            actual_link = removeFragment(actual_link) # defragment the link
            
            #Peter: urlsDifferentEnough()
            if isValidDomain(actual_link) and is_valid(actual_link):
                #Peter: urlsDifferentEnough()
                #  putting this count here to print whether anything was filtered by urlsDifferentEnough
                before_urlsDifferentEnough += 1
                if urlsDifferentEnough(url, actual_link):
                    list_of_urls.append(actual_link)

    print(f" Filtered by urlsDifferentEnough - {before_urlsDifferentEnough - len(list_of_urls)}")
    #Peter: correct and intentional to have a list of only url's without bfs_depth here; that is handled in worker.py
    return list_of_urls
        
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|ppsx|pps|mat"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|py|sql|c|cpp|out|test|mod|tag|info|Z|lisp|cc"
            + r"|col|r|apk|img|war|java|bam"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        return False