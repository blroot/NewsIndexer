import configparser
import pickle
from UncompressedPostings import UncompressedPostings


class Search:
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        self._output = config["DEFAULT"]["output"]

    def search_in_ii(self, terms):
        term_dict = pickle.load(open(self._output + '/' + 'term.dict', 'rb'))
        document_dict = pickle.load(open(self._output + '/' + 'document.dict', 'rb'))
        ii_dict = pickle.load(open(self._output + '/' + 'ii.dict', 'rb'))

        # Invierto document_dict para trabajar con los ID
        id_to_document_list = {y: x for x, y in document_dict.items()}

        results = {}

        postings = UncompressedPostings(self._output + '/' + 'index.ii')

        for term in terms:
            term_id = term_dict.get(term, None)
            metadata = ii_dict.get(term_id, None)

            if term_id and metadata:
                postings_list = postings.retrieve_postings_list(metadata[0], metadata[1]*4)
                results[term] = [id_to_document_list.get(x) for x in postings_list]
            else:
                results[term] = None

        postings.close_postings_file()

        return results
