import pickle
from UncompressedPostings import UncompressedPostings
from BTrees.OOBTree import OOBTree
import Stemmer


class Search:
    def __init__(self, output_path):
        self._output = output_path
        self._alphabet = 'abcdefghijklmnñopqrstuvwxyz'
        self._btree = OOBTree()
        self._reverse_btree = OOBTree()

    def search_in_ii(self, terms):
        term_dict = pickle.load(open(self._output + '/' + 'term.dict', 'rb'))
        document_dict = pickle.load(open(self._output + '/' + 'document.dict', 'rb'))
        ii_dict = pickle.load(open(self._output + '/' + 'ii.dict', 'rb'))

        # Invierto document_dict para trabajar con los ID
        id_to_document_list = {y: x for x, y in document_dict.items()}
        id_to_term = {y: x for x, y in term_dict.items()}

        # Inserto los términos en el árbol
        for key in ii_dict:
            self._btree.insert(id_to_term.get(key), ii_dict.get(key))

        self.reverse_btree()

        # Ya no se necesita esto
        ii_dict = None
        term_dict = None
        document_dict = None

        results = {}

        postings = UncompressedPostings(self._output + '/' + 'index.ii')

        for term in terms:
            metadata_list = self.wildcard_search(term)
            postings_list = []
            if metadata_list:
                for metadata in metadata_list:
                    postings_list += postings.retrieve_postings_list(metadata[0], metadata[1]*4)
                results[term] = [id_to_document_list.get(x) for x in postings_list]
            else:
                results[term] = None

        postings.close_postings_file()

        return results

    def reverse_btree(self):
        for key in self._btree:
            self._reverse_btree.insert(key[::-1], self._btree[key])

    def wildcard_search(self, word):
        if word.find("*") == -1:
            # No wildcard
            try:
                stemmer = Stemmer.Stemmer('spanish')
                stemmed_word = stemmer.stemWord(word)
                return list([self._btree[stemmed_word]])
            except KeyError:
                return None
        elif word[-1] == "*":
            return list(self._btree.values(min=word[:-1]+self._alphabet[0], max=word[:-1]+self._alphabet[26]))
        elif word[0] == "*":
            print("Desde %s hasta %s" % (word[::-1][:-1]+self._alphabet[0], word[::-1][:-1]+self._alphabet[26]))
            return list(self._reverse_btree.values(
                min=word[::-1][:-1]+self._alphabet[0], max=word[::-1][:-1]+self._alphabet[26])
            )
        else:
            return None
