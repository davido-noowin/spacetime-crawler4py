import shelve

def listUniquePages():
    '''
    Writes down the number of pages scraped
    '''
    with shelve.open('unique_urls.db', 'r') as shelf:
        with open('unique_urls.txt', 'w') as txt:
            txt.write(str(len(shelf['unique_urls'])))


def listMostWords():
    '''
    Finds the document with the largest number of words
    '''
    with shelve.open('max_num_words.db', 'r') as shelf:
        with open('max_num_words.txt', 'w') as txt:
            for key in shelf:
                value = shelf[key]
                txt.write(f'{key}, {value}')
                txt.write('\n')


def listSubdomainCounts():
    '''
    Lists the subdomain counts of *.ics.uci.edu
    '''
    with shelve.open('subdomain_counts.db', 'r') as shelf:
        with open('subdomain_counts.txt', 'w') as txt:
            for key in shelf:
                value = shelf[key]
                for item in value:
                    txt.write(f'{item}, {value[item]}')
                    txt.write('\n')


def listWordFrequencies():
    '''
    Finds the words that have been used most frequently
    '''
    with shelve.open('word_frequencies.db', 'r') as shelf:
        with open('word_frequencies.txt', 'w') as txt:
            sorted_word_freq = sorted(shelf.items(), key=lambda x: x[1], reverse=True)
            for key, value in sorted_word_freq:
                txt.write(f'{key}, {value}')
                txt.write('\n')


if __name__ == "__main__":
    listUniquePages()
    listMostWords()
    listSubdomainCounts()
    listWordFrequencies()