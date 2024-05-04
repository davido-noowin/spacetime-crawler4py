import shelve

def listUniquePages():
    '''
    Writes down the number of pages scraped
    '''
    with shelve.open('unique_urls.db', 'r') as shelf:
        with open('Assignment2Report.txt', 'w') as txt:
            txt.write(f"1. We found {str(len(shelf['unique_urls']))} unique pages.")
            txt.write('\n')


def listMostWords():
    '''
    Finds the document with the largest number of words
    '''
    with shelve.open('max_num_words.db', 'r') as shelf:
        with open('Assignment2Report.txt', 'w') as txt:
            max_value = 0
            max_key = ''
            for key in shelf:
                value = shelf[key]
                if value > max_value:
                    max_value = value

            txt.write(f'2. The longest page in terms of words is {max_key}, with {max_value} words.')
            txt.write('\n')


def listSubdomainCounts():
    '''
    Lists the subdomain counts of *.ics.uci.edu
    '''
    with shelve.open('subdomain_counts.db', 'r') as shelf:
        with open('Assignment2Report.txt', 'w') as txt:
            sorted_subdomains = sorted(shelf)
            txt.write(f'4. We found {len(shelf.items())} subdomains. List of subdomains:\n')
            for key in sorted_subdomains:
                txt.write(f'{key}, {shelf[key]}')
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
    with open('Assignment2Report.txt', 'w') as txt:
        txt.write('Names: Michael Gearhart, David Nguyen, Angela Xiang, Peter Young\n')
        txt.write('ID Numbers: 24461227,12943413,77836240,55292320\n')
        txt.write('Assignment 2 Report\n')
        txt.write('\n')

    listUniquePages()
    listMostWords()
    listWordFrequencies()
    listSubdomainCounts()
    