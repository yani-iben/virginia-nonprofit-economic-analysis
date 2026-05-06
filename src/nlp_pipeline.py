import spacy
import pandas as pd
from gensim import corpora
from gensim.models import LdaModel
from gensim.corpora import Dictionary

# Load once at the top of the script
try:
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
except OSError:
    # This acts as a fallback if the model isn't found
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    texts_out = []
    for text in texts:
        if pd.isna(text) or text == "":
            texts_out.append("")
            continue
        doc = nlp(text)
        new_text = [token.lemma_ for token in doc if token.pos_ in allowed_postags]
        texts_out.append(" ".join(new_text))
    return texts_out