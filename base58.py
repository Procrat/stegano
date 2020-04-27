BITCOIN_ALPHABET = \
    '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
RIPPLE_ALPHABET = 'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'


def decode(s, alphabet='BTC'):
    alphabet = {'BTC': BITCOIN_ALPHABET, 'RIPPLE': RIPPLE_ALPHABET}[alphabet]
    acc = decode_as_int(s, alphabet)
    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)
    return bytes(reversed(result))


def decode_as_int(s, alphabet):
    decimal = 0
    for char in s:
        decimal = decimal * 58 + alphabet.index(char)
    return decimal
