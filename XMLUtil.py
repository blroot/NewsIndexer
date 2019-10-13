import xml.etree.ElementTree as ET


class XMLUtil:
    def __init__(self, xml_file):
        self._xml_file = xml_file

    def get_document_list(self):
        tree = ET.parse(self._xml_file)
        root = tree.getroot()

        return [x for x in root]
