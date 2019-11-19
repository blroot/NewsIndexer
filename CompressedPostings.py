from UncompressedPostings import UncompressedPostings
from bitarray import bitarray


class CompressedPostings(UncompressedPostings):
    def __init__(self, file_name, mode='rb'):
        self._offset = 0
        super(CompressedPostings, self).__init__(file_name, mode)

    def retrieve_postings_list(self, offset, size):
        return self.decode(self._retrieve_chunk(offset, size))

    def compress(self, uncompressed_list):
        uncompressed_list.sort()

        # Hago la lista de saltos
        jump_list = []
        pivot = uncompressed_list[0]
        jump_list.append(pivot)
        for i in uncompressed_list[1:]:
            jump_list.append(i - pivot)
            pivot = i

        # Codifico cada doc_id/salto
        compressed_bitarray = bitarray(endian='big')
        for i in jump_list:
            in_bytes = i.to_bytes(4, 'big')
            in_bitarray = bitarray(endian='big')
            in_bitarray.frombytes(in_bytes)

            # Normalizo la cadena de bits a múltiplo de 7
            while len(in_bitarray) > 1 and in_bitarray[0] is False:
                in_bitarray = in_bitarray[1:]
            while len(in_bitarray) % 7 != 0:
                in_bitarray.insert(0, False)

            len_in_bitaray = len(in_bitarray)
            chunks = [in_bitarray[x:x+7] for x in range(0, len_in_bitaray, 7)]
            for index, j in enumerate(chunks):
                if index == len_in_bitaray//7 - 1:
                    compressed_bitarray += '1'
                else:
                    compressed_bitarray += '0'
                compressed_bitarray += j

        self.write(compressed_bitarray)
        offset = self._offset
        len_compressed_bitarray = len(compressed_bitarray)//8
        self._offset += len_compressed_bitarray

        return offset, 1, len_compressed_bitarray

    @staticmethod
    def decode(encoded_postings_list):
        bitarray_list = bitarray(endian='big')
        bitarray_list.frombytes(encoded_postings_list)
        chunks = [bitarray_list[x:x + 8] for x in range(0, len(bitarray_list), 8)]
        bitarray_item = bitarray(endian='big')
        decoded_postings_list = []
        pivote = int(chunks[0][1:].to01(), 2)
        for index, i in enumerate(chunks):
            bitarray_item += i[1:]
            if i[0] == 1:
                doc_id = int(bitarray_item.to01(), 2)
                if index != 0:
                    doc_id += pivote

                pivote = doc_id
                decoded_postings_list.append(doc_id)
                bitarray_item = bitarray(endian='big')

        return decoded_postings_list
