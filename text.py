import base64
import binascii
from itertools import zip_longest

import base58
import morse


def try_decode(text):
    valid = all(' ' <= c <= '~' or ord(c) in (0, 4, 10, 13) for c in text)
    print(f'{"Valid" if valid else "Weird"} ASCII: "{text}"')

    if all('0' <= c <= '1' for c in text.lower()):
        print('Binary values or morse code.')
        yield bytes(int(''.join(bits), 2) for bits in grouper(text, 8, '0'))
        yield from morse.try_decode(text)
    elif all('0' <= c <= '7' for c in text.lower()):
        print('Octal values.')
        raise NotImplementedError
    elif all('0' <= c <= '9' or 'a' <= c <= 'f' for c in text.lower()):
        print('Hexadecimal values.')
        raise NotImplementedError
    elif all('2' <= c <= '7' or 'A' <= c <= 'Z' or c == '=' for c in text):
        try:
            decoded = base64.b32decode(text)
            print(f'Base32-decoded: {decoded}')
            yield decoded
        except binascii.Error:
            print('Not base32-decodable.')
    elif all('0' <= c <= '9' or 'a' <= c <= 'z' or c in '=/+'
                for c in text.lower()):
        if not any(c in '0OlI+/' for c in text):
            decoded = base58.decode(text, 'BTC')
            print(f'Base58-decoded (BTC): {decoded}')
            yield decoded

            decoded = base58.decode(text, 'RIPPLE')
            print(f'Base58-decoded (RIPPLE): {decoded}')
            yield decoded

            try:
                decoded = base64.b64decode(text)
                print(f'Base64-decoded: {decoded}')
                yield decoded
            except binascii.Error:
                print('Not base64-decodable.')
        else:
            try:
                decoded = base64.b64decode(text)
                print(f'Base85-decoded: {decoded}')
                yield decoded
            except binascii.Error:
                print('Not base64-decodable.')
    elif all('!' <= c <= 'u' for c in text):
        try:
            decoded = base64.b85decode(text)
            print(f'Base85-decoded: {decoded}')
            yield decoded
        except Exception:
            print('Not base85-decodable.')


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
