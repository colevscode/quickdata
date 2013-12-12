import random

def gen_random_str(size, valid_chars):
    new_char = lambda : random.choice(valid_chars)
    val = ''.join(new_char() for x in range(size))
    return val