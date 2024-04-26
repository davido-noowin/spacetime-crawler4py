import pickle
import shelve

def listUniquePages():
    with shelve.open('unique_urls.db', 'r') as shelf:
        print(len(shelf['unique_urls']))


def listMostWords():
    with shelve.open('max_num_words.db', 'r') as shelf:
        for key in shelf:
            value = shelf[key]
            print(f'Key: {key}, Value: {value}')


def listSubdomainCounts():
    with shelve.open('subdomain_counts.db', 'r') as shelf:
        for key in shelf:
            value = shelf[key]
            print(f'Key: {key}, Value: {value}')


def listWordFrequencies():
    with shelve.open('word_frequencies.db', 'r') as shelf:
        for key in shelf:
            value = shelf[key]
            print(f'Key: {key}, Value: {value}')


listUniquePages()
print()
listMostWords()
print()
listSubdomainCounts()
print()
listWordFrequencies()
print()