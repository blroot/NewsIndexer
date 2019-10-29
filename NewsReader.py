import xml.etree.ElementTree as ET
import requests
import time
import os
from Normalizer import Normalizer


class NewsReader:
    def __init__(self, config, callback=None):
        self.config = config
        self.output = None
        self._callback = callback

    def collect_news(self):
        self.output = self.config["DEFAULT"]["output"]
        query_interval = int(self.config["DEFAULT"]["query_interval"])
        iterations = int(self.config["DEFAULT"]["iterations"])
        iterations_counter = 0

        while iterations_counter <= iterations:
            for section in self.config.sections():
                for option in self.config[section]:
                    url_base = self.config[section]['url_base']

                    if option not in ['url_base', 'query_interval', 'tmp', 'output', 'iterations']:
                        path = url_base + self.config[section][option]
                        try:
                            xml_data = requests.get(path)
                        except requests.exceptions.ChunkedEncodingError:
                            if self._callback:
                                self._callback("DLERR", path)
                            continue
                        try:
                            tree = ET.ElementTree(ET.fromstring(xml_data.content))
                        except ET.ParseError:
                            if self._callback:
                                self._callback("PARSEERR", path)
                            continue

                        root = tree.getroot()
                        news_list = root.findall('./channel/item')
                        normalized_option = Normalizer.normalize_name(option)

                        self.create_dir_if_not_exists(section)

                        output_xml_file = self.create_output_file_if_not_exists(normalized_option, section)

                        tree_output = ET.parse(output_xml_file)
                        root = tree_output.getroot()

                        for article in news_list:
                            article_title = article.find('title')
                            article_date = article.find('pubDate')

                            try:
                                article_title.text = self.normalize_value(article_title.text)
                                article_date.text = self.normalize_value(article_date.text)

                                search_filter = './item[title=' + '"' + article_title.text + '"' + "]" \
                                                + '[pubDate=' + '"' + article_date.text + '"' + ']'

                                all_items = root.findall(search_filter)

                                if len(all_items) == 0:
                                    if self._callback:
                                        self._callback("NEWARTICLE", section, option, article_title.text)
                                    root.append(article)
                            except AttributeError:
                                if self._callback:
                                    self._callback("BADFORMAT")

                        tree_output.write(output_xml_file)

            if self._callback:
                self._callback("WAITING", query_interval)
                self._callback("CANINTERR")
            time.sleep(query_interval)
            iterations_counter += 1

    def create_output_file_if_not_exists(self, normalized_option, section):
        output_xml_file = self.output + '/' + section + '/' + normalized_option + ".xml"
        if not os.path.exists(output_xml_file):
            root = ET.Element("data")
            tree = ET.ElementTree(root)
            tree.write(output_xml_file)
        return output_xml_file

    @staticmethod
    def normalize_value(value):
        return value.strip("\n").replace('"', "&quot;").strip()

    def create_dir_if_not_exists(self, name):
        if not os.path.exists(self.output + '/' + name):
            os.makedirs(self.output + '/' + name)
