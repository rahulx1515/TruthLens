"""
TruthLens - Machine Learning Preprocessing Module
Extracts and unifies preprocessing code from notebooks to ensure training
and production inference use the exact same deterministic pipeline.
"""
import re
import string
from typing import Optional, Set

# Comprehensive NLTK English stopwords set (standard 179 words)
# Embedded to guarantee deterministic execution without relying on external network downloads
ENGLISH_STOPWORDS: Set[str] = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll",
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now',
    'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
    "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn',
    "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan',
    "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
    'wouldn', "wouldn't"
}


def clean_text(text: str) -> str:
    """
    Standard text cleaning matching Notebook 02:
    - Lowercase conversion
    - URL removal
    - HTML tag removal
    - Punctuation removal
    - Digit removal
    - Extra whitespace normalization
    """
    if not text:
        return ""
    
    text = str(text).lower()
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)
    # Remove punctuation
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    # Remove digits
    text = re.sub(r"\d+", "", text)
    # Normalize whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_stopwords(text: str, custom_stopwords: Optional[Set[str]] = None) -> str:
    """
    Removes standard stopwords from cleaned string.
    """
    if not text:
        return ""
    
    stopwords_set = custom_stopwords or ENGLISH_STOPWORDS
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords_set and len(word) > 1]
    return " ".join(filtered_words)


def tokenize(text: str) -> list[str]:
    """
    Tokenizes text by whitespace matching Notebook 02.
    """
    return text.split()


def preprocess_news(title: Optional[str] = "", text: Optional[str] = "") -> str:
    """
    Combines headline and text, cleans and removes stopwords.
    This function is used for both offline training and online production inference.
    """
    title_str = str(title or "").strip()
    text_str = str(text or "").strip()
    combined = f"{title_str} {text_str}".strip()
    
    cleaned = clean_text(combined)
    return remove_stopwords(cleaned)

