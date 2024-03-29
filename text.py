import base64
import binascii
from itertools import zip_longest

import base58
import morse


def try_decode_bytes(data):
    data = data.strip()

    if data.isascii():
        decoded = data.decode('ascii')
        _log('Valid ASCII.')
        yield from try_decode_text(decoded)
        _log('Trying reversed.')
        yield from try_decode_text(decoded[::-1])

    else:
        if len(data) % 4 == 0:
            try:
                decoded = data.decode('utf-32-be')
            except ValueError:
                pass
            else:
                _log('Valid UTF-32-BE.')
                yield from try_decode_text(decoded)
            try:
                decoded = data.decode('utf-32-le')
            except ValueError:
                pass
            else:
                _log('Valid UTF-32-LE.')
                yield from try_decode_text(decoded)

        if len(data) % 2 == 0:
            try:
                decoded = data.decode('utf-16-be')
            except ValueError:
                pass
            else:
                _log('Valid UTF-16-BE.')
                yield from try_decode_text(decoded)
            try:
                decoded = data.decode('utf-16-le')
            except ValueError:
                pass
            else:
                _log('Valid UTF-16-LE.')
                yield from try_decode_text(decoded)

        try:
            decoded = data.decode('utf-8')
        except ValueError:
            pass
        else:
            _log('Valid UTF-8.')
            yield from try_decode_text(decoded)


def try_decode_text(text):
    is_normal = all(' ' <= c <= '~' or ord(c) in (0, 4, 10, 13) for c in text)
    _log(f'{"Normal" if is_normal else "Weird"}'
         f' {"ASCII" if text.isascii() else "non-ASCII"}'
         ' text:'
         f' "{pprint(text)}"')

    sanitised = ''.join(text.lower().split())

    if all('0' <= c <= '1' for c in sanitised):
        _log('Binary values or morse code.')
        yield bytes(int(''.join(bits), 2)
                    for bits in grouper(sanitised, 8, '0'))
        yield from morse.try_decode(text)
    elif all('0' <= c <= '7' for c in sanitised):
        _log('Octal values.')
        raise NotImplementedError
    elif all('0' <= c <= '9' or 'a' <= c <= 'f' for c in sanitised):
        _log('Hexadecimal values.')
        yield bytes.fromhex(text)
    elif all('2' <= c <= '7' or 'A' <= c <= 'Z' or c == '='
             for c in sanitised):
        try:
            decoded = base64.b32decode(text)
            _log(f'Base32-decoded: {pprint(decoded)}')
            yield decoded
        except binascii.Error:
            _log('Not base32-decodable.')
    elif all('0' <= c <= '9' or 'a' <= c <= 'z' or c in '=/+'
             for c in sanitised):
        if not any(c in '0OlI+/' for c in text):
            decoded = base58.decode(text, 'BTC')
            _log(f'Base58-decoded (BTC): {pprint(decoded)}')
            yield decoded

            decoded = base58.decode(text, 'RIPPLE')
            _log(f'Base58-decoded (RIPPLE): {pprint(decoded)}')
            yield decoded

            try:
                decoded = base64.b64decode(text)
                _log(f'Base64-decoded: {pprint(decoded)}')
                yield decoded
            except binascii.Error:
                _log('Not base64-decodable.')
        else:
            try:
                decoded = base64.b64decode(text)
                _log(f'Base85-decoded: {pprint(decoded)}')
                yield decoded
            except binascii.Error:
                _log('Not base64-decodable.')
    elif all('!' <= c <= 'u' or c == '~' for c in text):
        if text.startswith('<~') and text.endswith('~>'):
            # Adobe-style Ascii85
            try:
                decoded = base64.a85decode(text, adobe=True)
                _log(f'Ascii85-decoded (Adobe): {pprint(decoded)}')
                yield decoded
            except ValueError:
                _log('Not Ascii85-decodable (Adobe).')
        else:
            try:
                decoded = base64.b85decode(text)
                _log(f'Base85-decoded: {pprint(decoded)}')
                yield decoded
            except ValueError:
                _log('Not base85-decodable.')
            try:
                decoded = base64.a85decode(text)
                _log(f'Ascii85-decoded: {pprint(decoded)}')
                yield decoded
            except ValueError:
                _log('Not Ascii85-decodable.')
    elif '\r' in text or '\n' in text and ' ' not in text:
        _log('Newlines detected: stripping them out.')
        yield text.translate(str.maketrans('', '', '\r\n')).encode()
    else:
        _log('Just human-readable text perhaps? Printing in full:')
        print(text)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def pprint(text):
    return str(text[:200]) + ('<snip>' if len(text) > 200 else '')


def _log(*args):
    print('Text:', *args)
