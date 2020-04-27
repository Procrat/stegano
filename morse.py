from collections import Counter
import re

ALPHABET = {
    '.-': 'a',
    '-...': 'b',
    '-.-.': 'c',
    '-..': 'd',
    '.': 'e',
    '..-.': 'f',
    '--.': 'g',
    '....': 'h',
    '..': 'i',
    '.---': 'j',
    '-.-': 'k',
    '.-..': 'l',
    '--': 'm',
    '-.': 'n',
    '---': 'o',
    '.--.': 'p',
    '--.-': 'q',
    '.-.': 'r',
    '...': 's',
    '-': 't',
    '..-': 'u',
    '...-': 'v',
    '.--': 'w',
    '-..-': 'x',
    '-.--': 'y',
    '--..': 'z',

    '-----': '0',
    '.----': '1',
    '..---': '2',
    '...--': '3',
    '....-': '4',
    '.....': '5',
    '-....': '6',
    '--...': '7',
    '---..': '8',
    '----.': '9',

    '.-.-.-': '.',
    '--..--': ',',
    '..--..': '?',
    '.----.': "'",
    '-.-.--': '!',
    '-..-.': '/',
    '-.--.': '(',
    '-.--.-': ')',
    '.-...': '&',
    '---...': ':',
    '-.-.-.': ';',
    '-...-': '=',
    '.-.-.': '+',
    '-....-': '-',
    '..--.-': '_',
    '.-..-.': '"',
    '...-..-': '$',
    '.--.-.': '@',

    '...-.-': '<END>',
    '........': '<ERROR>',
    '-.-.-': '<START>',
    '.-.-.': '<NEW PAGE>',
    '...-.': '<UNDERSTOOD>',
}


def try_decode(bit_str):
    counter = Counter(len(m) for m in re.findall(r'0+', bit_str))
    if len(counter) <= 3:
        print(f'Morse code possible, histogram: {counter}')
        decoded = decode(bit_str)
        print(f'Morse decoded: "{decoded}"')
        yield decoded.encode('ascii')


def decode(bit_str):
    return ' '.join(decode_word(word) for word in bit_str.split('0000000'))


def decode_word(bit_str):
    return ''.join(decode_letter(letter) for letter in bit_str.split('000'))


def decode_letter(bit_str):
    morse = ''.join({'1': '.', '111': '-'}.get(sign, '?')
                    for sign in bit_str.split('0'))
    return ALPHABET.get(morse, '<?>')
