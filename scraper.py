import re
import shelve
import fnmatch
import nltk
from utils.response import Response # located in the utils folder
from urllib.parse import urlparse, urlunparse, urljoin
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize # pip install nltk
import urllib.robotparser
from collections import Counter
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('punkt')

#profiling
import binascii


DOMAINS = ['*.ics.uci.edu/*', 
          '*.cs.uci.edu/*', 
          '*.informatics.uci.edu/*', 
          '*.stat.uci.edu/*']

MAX_BFS_DEPTH = 35
#TODO have to tune
MAX_QUERY_STRIKES = 10
URL_NONRECURRENCE_MINIMUM = 0.6

BAD_EXTENSIONS = \
    r".*\.(css|js|bmp|gif|jpe?g|ico" + \
    r"|png|tiff?|mid|mp2|mp3|mp4" + \
    r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" + \
    r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names" + \
    r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso" + \
    r"|epub|dll|cnf|tgz|sha1|ppsx|pps|mat" + \
    r"|thmx|mso|arff|rtf|jar|csv" + \
    r"|py|sql|c|cpp|out|test|mod|tag|info|Z|lisp|cc" + \
    r"|col|r|apk|img|war|java|bam" + \
    r"|rm|smil|wmv|swf|wma|zip|rar|gz)$"      

num_words = 0


def bfsDepthOkay(bfs_depth: int) -> bool:
    '''
    Checks to see if the bfs depth of the link exceeds the MAX_BFS_DEPTH that has been set.
    '''
    if bfs_depth >= MAX_BFS_DEPTH:
        print("BFS depth limit exceeded. Will not crawl.")
        return False
    return True


def queryStrikesOkay(url: str) -> bool:
    '''
    Increments query strikes for base queryless url.
    Returns whether the base queryless url has had too many strikes.
    That is, too many urls like base?blah=blah.
    '''
    if (upto := url.rfind('?')) != -1:
        with shelve.open("query_strikes.db", writeback=True) as db:
            base = url[:upto]
            if base not in db:
                db[base] = 1
            else:
                db[base] += 1
                #correct, since at MAX_QUERY_STRIKES means this is the MAX_QUERY_STRIKES'th
                if db[base] > MAX_QUERY_STRIKES:
                    print("Query strike limit exceeded. Will not crawl.")
                    return False
    return True


def urlNonrecurrenceOkay(url: str) -> bool:
    '''
    Returns whether the components of the path are nonrecurring enough.
    '''
    url = url[:url.rfind('?')]
    toks = url[url.find('//') + 2:].split('/')
    if len(set(toks)) / len(toks) < URL_NONRECURRENCE_MINIMUM:
        return False
    return True


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
    

def isValidDomain(url: str) -> bool:
    '''
    Checks to see if the domains collected from the sites are within the sites specified by the project
    '''
    for pattern in DOMAINS:
        if fnmatch.fnmatch(url, pattern):
            return True
    return False


def removeFragment(url: str) -> str:
    '''
    Removes the fragment from a url
    '''
    parsed_url = urlparse(url)
    # Remove fragment from the URL
    clean_url = urlunparse(parsed_url._replace(fragment=''))
    return clean_url


def tokenizer(parsed_html: BeautifulSoup, strip: bool) -> list[str]:
    '''
    Tokenizes the html page so that it can be used in other functions
    '''
    text = parsed_html.get_text(strip=strip)
    return word_tokenize(text)


def updateUniqueUrl(url: str) -> None:
    '''
    Appends the current URL to the unique url set. Periodically (50 urls) it will
    write to the pickle file in case something goes wrong then we have some data that
    we can still recover
    '''
    try:
        with shelve.open('unique_urls.db', writeback=True) as db:
            if 'unique_urls' not in db:
                db['unique_urls'] = set()

            db['unique_urls'].add(url)
    except Exception as e:
        print(f"Error saving unique_urls set: {e}")


def crcOkay(get_text: BeautifulSoup.get_text) -> bool:
    with shelve.open("crc.db", writeback=True) as db:
        crc = str(binascii.crc32(get_text.encode(encoding="utf-8")))
        if crc in db:
            print("CRC found exact duplicate. Will not crawl.")
            return False
      
        #only need to store keys, so None as value
        db[crc] = None
        return True


def updateWordCount(tokenized_words: str, url:str) -> None:
    '''
    Checks the text of the parsed html, preprocesses it to remove any whitespace then
    checks to see if it is the longest page
    '''
    global num_words
    try:
        with shelve.open('max_num_words.db', writeback=True) as db:
            if 'num_words' not in db:
                db['num_words'] = 0
            if 'longest_url' not in db:
                db['longest_url'] = ""

            word_count = len(tokenized_words)

            if word_count > num_words:
                num_words = word_count
                db['num_words'] = word_count
                db['longest_url'] = url
    except Exception as e:
        print(f"Error saving the max num words of all pages: {e}")
        

def subDomainCount(url: str):
    '''
    Counts number of unique "ics.uci.edu" subdomains, stores in 
    shelve and needs to be retrieved after the program is done running to get the data.
    Restarting the crawler with --restart will also reset this shelve
    '''
    try:
        with shelve.open('subdomain_counts.db', writeback=True) as db:
            if 'subdomain_counts' not in db:
                db['subdomain_counts'] = {}

            if ".ics.uci.edu" in url:
                parsedUrl = urlparse(url)
                # Reconstruct the URL without the path, then store in shelve + 1
                subdomain_url = parsedUrl.scheme + "://" + parsedUrl.netloc
                subdomain_counts = db['subdomain_counts']
                subdomain_counts[subdomain_url] = subdomain_counts.get(subdomain_url, 0) + 1
                db['subdomain_counts'] = subdomain_counts
                #for key, value in db.items():
                    #print(f"DEBUG ENTIRE SHELF= {key}: {value}")
    except Exception as e:
        print(f"Error finding the subdomain count: {e}")


def wordFreqCount(tokenized_words):
    '''
    Counts frequency of each word, stores in shelve
    shelve file needs to be retrieved and sorted after the program is done running to get the data.
    Restarting the crawler with --restart will also reset this shelve
    '''
    word_counter = Counter()
    words = tokenized_words
    stop_words = set(stopwords.words('english'))
    words = [word.lower() for word in words if word.isalpha() and word not in stop_words]
    word_counter.update(words)
    
    try:
        with shelve.open('word_frequencies.db') as wordFreq:
            for word, count in word_counter.items():
                wordFreq[word] = wordFreq.get(word, 0) + count
            if len(wordFreq) > 10000: #KEEP ONLY TOP 1000 WORDS IF SHELVE GETS TOO FULL 
                sorted_word_freq = sorted(wordFreq.items(), key=lambda x: x[1], reverse=True)
                top_words = sorted_word_freq[:1000]
                wordFreq.clear()
                for word, count in top_words:
                    wordFreq[word] = count
            #sorted_word_freq = sorted(wordFreq.items(), key=lambda x: x[1], reverse=True)
            #print(sorted_word_freq[:50])
    except Exception as e:
        print(f"Error finding finding the word frequency: {e}")


#takes url, resp, bfs_depth
def scraper(url: str, resp: Response, bfs_depth: int) -> list:
    return extract_next_links(url, resp, bfs_depth)


#takes url, resp, bfs_depth
def extract_next_links(url, resp, bfs_depth):
    '''
    Uses the Response content and analyzes the html for possible links to add to the
    frontier. It attempts to filter out pages that have low information value, is not
    within the specified domains, or is not a valid web page

    url: the URL that was used to get the page
    resp.url: the actual url of the page
    resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    resp.error: when status is not 200, you can check the error here, if needed.
    resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
            resp.raw_response.url: the url, again
            resp.raw_response.content: the content of the page!
    Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    '''
    print(f'URL - {url} \nresponse URL - {resp.url} \nResponse Status - {resp.status} \nResponse Error - {resp.error}\nbfs_depth - {bfs_depth}')
    list_of_urls = []

    before_urlNonrecurrenceOkay = 0 #for printing
    #conditions for crawling. bfsDepthOkay and queryStrikesOkay print on fail
    if resp.status == 200 and bfsDepthOkay(bfs_depth) and queryStrikesOkay(resp.url):
        print("ACCESSING VALID URL STATUS 200")
        parsed_html = BeautifulSoup(resp.raw_response.content, "html.parser")
        get_text = parsed_html.get_text(strip=False)

        #check for exact duplicates, printing on fail
        if crcOkay(get_text):
            text = tokenizer(parsed_html, strip=True)
            subDomainCount(resp.url)
            wordFreqCount(text)
            updateUniqueUrl(resp.url) # adding to the counting set
            updateWordCount(text, resp.url)
            
            for link in parsed_html.find_all('a', href=True):
                possible_link = link['href']
                actual_link = ''
                if not checkPath(possible_link):
                    # if the path is not a valid absolute path then we manipulate it so that it becomes one
                    actual_link = convertRelativeToAbsolute(url, possible_link)
                else:
                    actual_link = possible_link

                actual_link = removeFragment(actual_link) # defragment the link
                
                if isValidDomain(actual_link) and is_valid(actual_link):
                    #for printing whether anything was filtered by urlsDifferentEnough
                    before_urlNonrecurrenceOkay += 1
                    if urlNonrecurrenceOkay(url):
                        list_of_urls.append(actual_link)

    print(f"Filtered by urlNonrecurrenceOkay - {before_urlNonrecurrenceOkay - len(list_of_urls)}")
    print(f"Links extracted - {len(list_of_urls)}")
    return list_of_urls #correct and intentional to have a list of only url's without bfs_depth's here
        

def is_valid(url):
    '''
    File extension checks for whether to crawl this url both for path and for query
    '''
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        #if no query, then the empty string does not match and all is well
        return not re.match(BAD_EXTENSIONS, parsed.path.lower()) and not re.match(BAD_EXTENSIONS, parsed.query.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        return False