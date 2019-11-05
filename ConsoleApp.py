from NewsReader import NewsReader
from Index import Index
from Search import Search
import configparser
import time


class ConsoleApp:
    def __init__(self, config_file_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_file_path, encoding='utf-8')

        self.menu_options = {
            1: self.collect_news,
            2: self.build_ii,
            3: None,
            4: None,
            5: self.search,
            6: exit
        }

    def collect_news(self):
        try:
            newsreader = NewsReader(self._config, callback=self.print_callback)
            newsreader.collect_news()
        except KeyboardInterrupt:
            print("Cancelando recolección de artículos")
            self.display_menu()

    def build_ii(self):
        index = Index(self._config, callback=self.print_callback)
        index.process_blocks()
        index.merge_blocks()

    def search(self):
        output = self._config["DEFAULT"]["output"]
        print("Ingrese las palabras a buscar, separadas por blancos para búsqueda múltiple")
        terms = str(input()).split()
        start = time.time()
        search = Search(output)
        results = search.search_in_ii(terms)

        for term, docs in results.items():
            print("---- Resultados de la búsqueda por término %s ----" % term)
            if docs is not None:
                for doc in docs:
                    print(doc)
            else:
                print("No se encontraron resultados.")
        end = time.time()
        print("La búsqueda demoró %s" % (end - start))

    @staticmethod
    def print_callback(message, *args):
        """
        Método callback para recibir mensajes e imprimir un texto adecuado por consola
        """
        messages = {
            "DLERR": "No se pudo descargar el XML de %s",
            "PARSEERR": "No se pudo parsear el XML de %s",
            "NEWARTICLE": "Agregado %s - %s - %s",
            "BADFORMAT": "Mal formato de título o fecha, salteando...",
            "WAITING": "Esperando %s segundos para reiniciar descargas",
            "CANINTERR": "Si lo desea presione CTRL+C para cancelar y volver al menú principal",
            "BLKNE": "El archivo intermedio %s no existe, salteando...",
            "INDERR": "No se puede indexar el artículo con título %s",
            "XMLNF": "No existe el archivo XML %s",
            "MERGEOK": "Construcción del índice invertido finalizada"
        }
        print(messages.get(message) % args)

    def display_menu(self):
        print("Bienvenido.... Por favor, seleccione una opción")
        print("1 - Recolectar Noticias")
        print("2 - Construír índice invertido")
        print("3 - Recuperar índice invertido desde disco")
        print("4 - Comprimir lista de apariciones")
        print("5 - Buscar")
        print("6 - Salir")

        try:
            option = int(input("Seleccione una opción [1-5]: "))

            option_function = self.menu_options.get(option, None)
            if not option_function:
                print("%s no es una opción válida" % option)
            else:
                option_function()
        except ValueError:
            print("la opción ingresada no corresponde a un número")
