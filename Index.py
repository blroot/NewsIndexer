import configparser
from Normalizer import Normalizer
from XMLUtil import XMLUtil
from UncompressedPostings import UncompressedPostings
import csv
import os


class Index:
    def __init__(self, config_file, document_dict={}, term_dict={}):
        self.config_file = config_file
        self._document_dict = document_dict
        self._term_dict = term_dict
        self._document_dict_next_id = 0
        self._term_dict_next_id = 0
        self._ii_dict = {}
        self._ii_list = []
        self._output = None

    def get_block_dict(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')

        self._output = config["DEFAULT"]["output"]

        block_list = []
        block_dict = {}

        for section in config.sections():
            block_dict[section] = []
            for option in config[section]:
                if option not in ['url_base', 'query_interval', 'tmp', 'output', 'iterations']:
                    normalized_option = Normalizer.normalize_name(option)
                    output_xml_file = self._output + '/' + section + '/' + normalized_option + ".xml"
                    # block_list.append((section, option, output_xml_file, section))
                    block_dict[section].append((option, output_xml_file))

        return block_dict

    def remove_all_parts(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')
        for section in config.sections():
            filename = self._output + '/' + section + "/" + section + ".ii.part"
            try:
                os.remove(filename)
            except FileNotFoundError:
                print("El archivo intermedio %s no existe, salteando..." % filename)

    def process_blocks(self):
        block_dict = self.get_block_dict()
        self.remove_all_parts()

        for section in block_dict:
            channel_list = block_dict[section]
            for channel in channel_list:
                xml_util = XMLUtil(channel[1])

                try:
                    doc_list = xml_util.get_document_list()

                    for article in doc_list:
                        article_title = article.find('title')
                        article_date = article.find('pubDate')
                        article_description = article.find('description')
                        try:
                            doc_key = section + '-' + channel[0] + '-' + article_title.text + '-' + article_date.text
                            self.insert_doc_id(doc_key)
                            self.build_ii(doc_key, article_title.text, article_description.text, section)
                        except (TypeError, AttributeError):
                            print("No se puede indexar el artículo")
                except FileNotFoundError:
                    print("No se encontró el archivo XML")
                self._ii_dict = {}

    def build_ii(self, doc_key, title, description, section):
        normalizer = Normalizer()
        all_terms = title.split() + description.split()
        cleaned_terms = [normalizer.normalize_name(x) for x in all_terms if not normalizer.is_stop_word(normalizer.normalize_name(x))]
        for term in cleaned_terms:
            term_id = self.get_or_create_term_id(term)
            self._ii_dict.setdefault(term_id, set())
            self._ii_dict[term_id].add(self._document_dict.get(doc_key))

        self._ii_list = [(x, UncompressedPostings.encode(self._ii_dict[x])) for x in sorted(self._ii_dict.keys())]
        with open(self._output + "/" + section + "/" + section + ".ii.part", "a", newline='') as ii_part:
            writer = csv.writer(ii_part)
            writer.writerows(self._ii_list)

        # Reset ii
        self._ii_list = []

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
