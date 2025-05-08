"""
Danish pronunciation rules and configuration.
"""

# Vowel sounds
VOWELS = {
    'a': 'ɑ',  # as in "kat"
    'e': 'e',  # as in "ben"
    'i': 'i',  # as in "bil"
    'o': 'o',  # as in "sol"
    'u': 'u',  # as in "hus"
    'y': 'y',  # as in "lyd"
    'æ': 'ɛ',  # as in "bæk"
    'ø': 'ø',  # as in "bølge"
    'å': 'ɔ'   # as in "bål"
}

# Consonant sounds
CONSONANTS = {
    'b': 'b',  # as in "bil"
    'd': 'd',  # as in "dør"
    'f': 'f',  # as in "fisk"
    'g': 'g',  # as in "gul"
    'h': 'h',  # as in "hus"
    'j': 'j',  # as in "jord"
    'k': 'k',  # as in "kat"
    'l': 'l',  # as in "lam"
    'm': 'm',  # as in "mus"
    'n': 'n',  # as in "næse"
    'p': 'p',  # as in "pind"
    'r': 'ʁ',  # as in "rød"
    's': 's',  # as in "sol"
    't': 't',  # as in "tand"
    'v': 'v',  # as in "vand"
}

# Special combinations
SPECIAL_COMBINATIONS = {
    'ng': 'ŋ',  # as in "sang"
    'sj': 'ɕ',  # as in "sjov"
    'sk': 'sg', # as in "skov"
    'st': 'sd', # as in "stol"
    'rd': 'ɐ',  # as in "bord"
}

# Stress patterns
STRESS_PATTERNS = {
    'en': 'ən',  # unstressed ending
    'et': 'əd',  # unstressed ending
    'er': 'ɐ',   # unstressed ending
}

# Pronunciation rules
RULES = [
    # Rule 1: Soft d at end of words
    (r'd$', 'ð'),
    
    # Rule 2: Silent d after n
    (r'nd$', 'n'),
    
    # Rule 3: Silent e at end of words
    (r'e$', ''),
    
    # Rule 4: Soft g before i, e, æ, ø, y
    (r'g([ieæøy])', r'j\1'),
    
    # Rule 5: Silent h at start of words
    (r'^h', ''),
]

def get_pronunciation_rules():
    """Return all pronunciation rules."""
    return {
        'vowels': VOWELS,
        'consonants': CONSONANTS,
        'special_combinations': SPECIAL_COMBINATIONS,
        'stress_patterns': STRESS_PATTERNS,
        'rules': RULES
    } 