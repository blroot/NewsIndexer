import configparser
import xml.etree.ElementTree as ET
import requests
import time
import os
from Normalizer import Normalizer


class NewsReader:
    def __init__(self, config_file):
        self.config_file = config_file
        self.output = None

    def collect_news(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')

        self.output = config["DEFAULT"]["output"]
        query_interval = int(config["DEFAULT"]["query_interval"])
        iterations = int(config["DEFAULT"]["iterations"])
        iterations_counter = 0

        while iterations_counter <= iterations:
            for section in config.sections():
                for option in config[section]:
                    url_base = config[section]['url_base']

                    if option not in ['url_base', 'query_interval', 'tmp', 'output', 'iterations']:
                        print("Downloading from url: %s" % url_base + config[section][option])

                        try:
                            xml_data = requests.get(url_base + config[section][option])
                        except requests.exceptions.ChunkedEncodingError:
                            print("No se pudo descargar el XML")
                            continue
                        try:
                            tree = ET.ElementTree(ET.fromstring(xml_data.content))
                        except ET.ParseError:
                            print("No se pudo parsear el XML")
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

                                # print("Searching : %s" % search_filter)

                                all_items = root.findall(search_filter)

                                if len(all_items) == 0:
                                    print("Saving new article -> Title: %s, Date: %s"
                                          % (article_title.text, article_date.text))
                                    root.append(article)
                            except AttributeError:
                                print("Mal formato de título o fecha")

                        tree_output.write(output_xml_file)

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
