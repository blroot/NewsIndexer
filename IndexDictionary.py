
class IndexDictionary:
    def __init__(self):
        self.dictionary = {}

    def insert(self, term_id, metadata):
        self.dictionary[term_id] = metadata

    def load_from_file(self):
        pass

    def save_to_file(self):
        pass
