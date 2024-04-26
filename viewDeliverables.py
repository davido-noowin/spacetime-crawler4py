import pickle
import shelve

def listUniquePages():
    # TODO: change to shelf instead of pickle
    with open('unique_urls.pkl', 'rb') as file:
        data = pickle.load(file)

    print(len(data))


def listMostWords():
    # TODO - David
    pass


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