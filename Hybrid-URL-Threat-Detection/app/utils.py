from pathlib import Path

import re
import math
import joblib
import numpy as np
import tldextract
import torch
import json

from urllib.parse import urlparse
from transformers import AutoTokenizer, AutoModel


# ======================================
# BASE DIRECTORY
# ======================================

BASE_DIR = Path(__file__).resolve().parent

SCALER_PATH = BASE_DIR / "model" / "feature_scaler.pkl"

BRAND_NAMES_PATH = BASE_DIR / "model" / "brand_names.json"

with open(BRAND_NAMES_PATH) as f:
    POPULAR_BRAND_NAMES = json.load(f)

# ======================================
# CONFIG
# ======================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MAX_LEN = 200

MAX_VOCAB_INDEX = 60


SUSPICIOUS_TLDS = {
    'tk', 'ml', 'ga', 'cf', 'gq',
    'pw', 'top', 'xyz', 'club',
    'online', 'site'
}


# ======================================
# CUSTOM CHARACTER TOKENIZER
# ======================================

VOCAB_CHARS = list(
    "abcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=%"
)

char2idx = {
    c: i + 2
    for i, c in enumerate(VOCAB_CHARS)
}

char2idx['<PAD>'] = 0
char2idx['<UNK>'] = 1


# ======================================
# LOAD MODELS
# ======================================

print("Loading MiniLM tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

print("Loading MiniLM model...")

minilm_model = AutoModel.from_pretrained(
    MODEL_NAME
)

minilm_model.eval()

print(f"Loading scaler from: {SCALER_PATH}")

scaler = joblib.load(
    SCALER_PATH
)

print("Scaler loaded successfully")


# ======================================
# FEATURE FUNCTIONS
# ======================================

def feat_url_length(u):
    return len(str(u))


def feat_digit_count(u):
    return sum(c.isdigit() for c in str(u))


def feat_special_count(u):
    return sum(
        c in "-._~:/?#[]@!$&'()*+,;=%"
        for c in str(u)
    )


def feat_hyphen_count(u):
    return str(u).count('-')


def feat_dot_count(u):
    return str(u).count('.')


def feat_at_symbol(u):
    return int('@' in str(u))


def feat_double_slash(u):
    stripped = re.sub(r'^https?://', '', str(u))
    return int('//' in stripped)


def feat_has_ip(u):
    return int(bool(
        re.search(r'(\d{1,3}\.){3}\d{1,3}', str(u))
    ))


def feat_subdomain_count(u):

    e = tldextract.extract(str(u))

    return len(
        e.subdomain.split('.')
    ) if e.subdomain else 0


def feat_path_depth(u):

    return urlparse(
        "http://" + str(u)
    ).path.count('/')


def feat_query_length(u):

    return len(
        urlparse(
            "http://" + str(u)
        ).query
    )


def feat_has_https(u):
    return int(str(u).startswith('https'))


def feat_entropy(u):

    u = str(u)

    prob = [
        u.count(c)/len(u)
        for c in set(u)
    ]

    return -sum(
        p * math.log2(p)
        for p in prob if p > 0
    )


def feat_digit_ratio(u):

    u = str(u)

    return sum(
        c.isdigit()
        for c in u
    ) / max(len(u), 1)


def feat_consonant_ratio(u):

    u = str(u).lower()

    return sum(
        c in 'bcdfghjklmnpqrstvwxyz'
        for c in u
    ) / max(len(u), 1)


def feat_longest_word(u):

    words = re.split(
        r'[.\-/_?=&]',
        str(u)
    )

    return max(
        (len(w) for w in words),
        default=0
    )


def feat_tld_length(u):

    return len(
        tldextract.extract(str(u)).suffix
    )


def feat_suspicious_tld(u):

    return int(
        tldextract.extract(str(u)).suffix.lower()
        in SUSPICIOUS_TLDS
    )

def feat_homoglyph_score(u):
    try:
        domain = tldextract.extract(str(u)).domain.lower()
        normalized = ''.join(
            HOMOGLYPH_REVERSE.get(c, c) for c in domain
        )
        print(f"DEBUG homoglyph → domain: {domain}, normalized: {normalized}")  # ← add here
        for brand in POPULAR_BRAND_NAMES:
            if normalized == brand and domain != brand:
                return 1
        return 0
    except Exception:
        return 0


def feat_levenshtein_min(u):
    try:
        from Levenshtein import distance as lev
        domain = tldextract.extract(str(u)).domain.lower()
        if not domain or len(domain) < 3:
            return 99
        return min(lev(domain, brand) for brand in POPULAR_BRAND_NAMES)
    except Exception:
        return 99


def feat_is_exact_brand(u):
    """Returns 1 if domain exactly matches a popular brand (not a typosquat)."""
    try:
        domain = tldextract.extract(str(u)).domain.lower()
        return int(domain in POPULAR_BRAND_NAMES)
    except Exception:
        return 0

FEATURE_FUNCS = [
    feat_url_length,
    feat_digit_count,
    feat_special_count,
    feat_hyphen_count,
    feat_dot_count,
    feat_at_symbol,
    feat_double_slash,
    feat_has_ip,
    feat_subdomain_count,
    feat_path_depth,
    feat_query_length,
    feat_has_https,
    feat_entropy,
    feat_digit_ratio,
    feat_consonant_ratio,
    feat_longest_word,
    feat_tld_length,
    feat_suspicious_tld,
    feat_homoglyph_score,   
    feat_levenshtein_min,   
    feat_is_exact_brand,  
]


# ======================================
# MEAN POOLING
# ======================================

def mean_pool(output, mask):

    token_emb = output.last_hidden_state

    expanded = mask.unsqueeze(-1).expand(
        token_emb.size()
    ).float()

    return torch.sum(
        token_emb * expanded,
        1
    ) / expanded.sum(1).clamp(min=1e-9)


# ======================================
# SAFE TOKENIZER
# ======================================

def safe_tokenize(url):

    tokens = []

    for c in url[:MAX_LEN]:

        idx = char2idx.get(c, 1)

        tokens.append(idx)

    return tokens


# ======================================
# MAIN PREPROCESS FUNCTION
# ======================================

def preprocess_url(url):

    # ==================================
    # CLEAN URL
    # ==================================

    url = str(url).lower().strip()
    url = re.sub(r'^https?://', '', url) 
    url = re.sub(r'^www\.', '', url)      
    url = url.rstrip('/')


    # ==================================
    # CUSTOM TOKENIZATION
    # ==================================

    token_list = safe_tokenize(url)

    token_list += [0] * (
        MAX_LEN - len(token_list)
    )

    tokens = np.array(
        [token_list],
        dtype=np.int64
    )


    # ==================================
    # FEATURE EXTRACTION
    # ==================================

    features = np.array([
        fn(url)
        for fn in FEATURE_FUNCS
    ]).reshape(1, -1)

    features = scaler.transform(
        features
    ).astype(np.float32)


    # ==================================
    # MINILM EMBEDDINGS
    # ==================================

    encoded = tokenizer(
        url,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors='pt'
    )

    with torch.no_grad():

        output = minilm_model(**encoded)

        embeddings = mean_pool(
            output,
            encoded['attention_mask']
        )

        embeddings = torch.nn.functional.normalize(
            embeddings,
            p=2,
            dim=1
        )

        embeddings = embeddings.numpy().astype(
            np.float32
        )


    return tokens, features, embeddings