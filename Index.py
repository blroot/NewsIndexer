import configparser
from Normalizer import Normalizer
from XMLUtil import XMLUtil
from UncompressedPostings import UncompressedPostings
from IndexDictionary import IndexDictionary
import os
import heapq


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
        self._block_dict = {}
        self._dictionary_index = IndexDictionary()

    def get_block_dict(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')

        self._output = config["DEFAULT"]["output"]

        self._block_dict = {}

        for section in config.sections():
            self._block_dict[section] = []
            for option in config[section]:
                if option not in ['url_base', 'query_interval', 'tmp', 'output', 'iterations']:
                    normalized_option = Normalizer.normalize_name(option)
                    output_xml_file = self._output + '/' + section + '/' + normalized_option + ".xml"
                    self._block_dict[section].append((option, output_xml_file))

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
        self.get_block_dict()
        self.remove_all_parts()

        for section in self._block_dict:
            channel_list = self._block_dict[section]
            ii_part_out = self._output + '/' + section + "/" + section + ".ii.part"

            try:
                with open(ii_part_out, "wb") as ii_part:
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
                                    self.process_article(doc_key, article_title.text, article_description.text)
                                except (TypeError, AttributeError):
                                    print("No se puede indexar el artículo")
                        except FileNotFoundError:
                            print("No se encontró el archivo XML")
                    self.write_partial_ii_to_file(ii_part)
            except FileNotFoundError:
                print("El archivo intermedio %s no existe, salteando..." % ii_part_out)

    def write_partial_ii_to_file(self, ii_part):
        for x in sorted(self._ii_dict.keys()):
            y = UncompressedPostings.encode(self._ii_dict[x])
            self._ii_list.append((x, y))
        for row in self._ii_list:
            array_size = len(row[1])
            ii_part.write(row[0].to_bytes(4, 'big') + array_size.to_bytes(4, 'big') + row[1])
        self._ii_dict = {}
        self._ii_list = []

    def merge_blocks(self):
        file_handlers = []
        for section in self._block_dict.keys():
            partial_ii_file = self._output + '/' + section + '/' + section + '.ii.part'
            try:
                file_handlers.append(open(partial_ii_file, 'rb'))
            except FileNotFoundError:
                print("El archivo intermedio %s no existe, salteando...")

        heap = []
        heapq.heapify(heap)

        # Pongo los primeros items en el heap
        for fh in file_handlers:
            chunk = self._get_next_chunk(fh)
            heapq.heappush(heap, chunk)

        with open(self._output + '/' + 'index.ii', 'wb') as out:
            previous_term_id = None
            offset = 0
            total_size = 0
            doc_list = b''
            while heap:
                minor = heapq.heappop(heap)
                fh_reference = minor[3]
                next_chunk = self._get_next_chunk(fh_reference)

                if next_chunk[2]:
                    heapq.heappush(heap, next_chunk)

                actual_term_id = minor[0]
                actual_doc_list = minor[2]
                size = minor[1]

                # Si el termID es igual al anterior acumulo doc_list y tamaño
                if actual_term_id == previous_term_id:
                    doc_list += actual_doc_list
                    total_size += size
                # Sino, inserto en el diccionario el termID con los acumulados
                else:
                    if previous_term_id is not None:
                        self._dictionary_index.insert(previous_term_id, (offset, int(total_size/4), total_size))
                        offset += total_size
                        out.write(doc_list)
                        doc_list = actual_doc_list
                        total_size = size

                previous_term_id = minor[0]

    @staticmethod
    def _get_next_chunk(fh):
        term_id = int.from_bytes(fh.read(4), byteorder='big')
        size = int.from_bytes(fh.read(4), byteorder='big')
        doc_list = fh.read(size)

        return term_id, size, doc_list, fh

    def process_article(self, doc_key, title, description):
        normalizer = Normalizer()
        all_terms = title.split() + description.split()
        cleaned_terms = [normalizer.normalize_name(x) for x in all_terms if not normalizer.is_stop_word(normalizer.normalize_name(x))]
        for term in cleaned_terms:
            term_id = self.get_or_create_term_id(term)
            self._ii_dict.setdefault(term_id, set())
            self._ii_dict[term_id].add(self._document_dict.get(doc_key))

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
