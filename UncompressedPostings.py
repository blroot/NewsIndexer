import array


class UncompressedPostings:
    def __init__(self, file_name, mode='rb'):
        self._file_name = file_name
        self._fh = open(self._file_name, mode)

    def write(self, data):
        self._fh.write(data)

    def close_postings_file(self):
        self._fh.close()

    def retrieve_postings_list(self, offset, size):
        return self.decode(self._retrieve_chunk(offset, size))

    def _retrieve_chunk(self, offset, size):
        self._fh.seek(offset)
        return self._fh.read(size)

    @staticmethod
    def encode(postings_list):
        return array.array('L', postings_list).tobytes()

    @staticmethod
    def decode(encoded_postings_list):
        decoded_postings_list = array.array('L')
        decoded_postings_list.frombytes(encoded_postings_list)
        return decoded_postings_list.tolist()
