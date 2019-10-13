import configparser
from Normalizer import Normalizer
from XMLUtil import XMLUtil


class Index:
    def __init__(self, config_file, document_dict={}, term_dict={}):
        self.config_file = config_file
        self._document_dict = document_dict
        self._term_dict = term_dict
        self._document_dict_next_id = 0
        self._term_dict_next_id = 0
        self._ii = {}

    def get_block_list(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')

        output = config["DEFAULT"]["output"]

        block_list = []

        for section in config.sections():
            for option in config[section]:
                if option not in ['url_base', 'query_interval', 'tmp', 'output', 'iterations']:
                    normalized_option = Normalizer.normalize_name(option)
                    output_xml_file = output + '/' + section + '/' + normalized_option + ".xml"
                    block_list.append((section, option, output_xml_file))

        return block_list

    def process_blocks(self):
        blocks = self.get_block_list()

        for block in blocks:
            xml_util = XMLUtil(block[2])

            try:
                doc_list = xml_util.get_document_list()

                for article in doc_list:
                    article_title = article.find('title')
                    article_date = article.find('pubDate')
                    article_description = article.find('description')
                    try:
                        doc_key = block[0] + '-' + block[1] + '-' + article_title.text + '-' + article_date.text
                        self.insert_doc_id(doc_key)
                        self.build_ii(doc_key, article_title.text, article_description.text)
                    except (TypeError, AttributeError):
                        print("No se puede indexar el artículo")
            except FileNotFoundError:
                print("No se encontró el archivo XML")

    def build_ii(self, doc_key, title, description):
        normalizer = Normalizer()
        all_terms = title.split() + description.split()
        cleaned_terms = [normalizer.normalize_name(x) for x in all_terms if not normalizer.is_stop_word(normalizer.normalize_name(x))]
        for term in cleaned_terms:
            term_id = self.get_or_create_term_id(term)
            self._ii.setdefault(term_id, set())
            self._ii[term_id].add(self._document_dict.get(doc_key))

    def get_or_create_term_id(self, term):
        if term not in self._term_dict.keys():
            doc_id = self._term_dict_next_id
            self._term_dict[term] = doc_id
            self._term_dict_next_id += 1
        else:
            doc_id = self._term_dict[term]

        return doc_id

    def insert_doc_id(self, doc_key):
        self._document_dict[doc_key] = self._document_dict_next_id
        self._document_dict_next_id += 1
