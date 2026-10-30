"""
Tests for TruthLens ML Preprocessing Module
"""
import pytest
from app.ml.preprocessing import clean_text, remove_stopwords, tokenize, preprocess_news


def test_clean_text_basic():
    raw = "BREAKING: NASA confirms Water on Mars! Visit https://nasa.gov/mars for info."
    cleaned = clean_text(raw)
    assert "https" not in cleaned
    assert "nasa.gov" not in cleaned
    assert "!" not in cleaned
    assert ":" not in cleaned
    assert "breaking nasa confirms water on mars visit for info" == cleaned


def test_clean_text_removes_html():
    raw = "<p>Scientists discover <b>new particle</b> in laboratory.</p>"
    cleaned = clean_text(raw)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "scientists discover new particle in laboratory" == cleaned


def test_clean_text_removes_digits():
    raw = "The year 2026 recorded 100 new astronomical events."
    cleaned = clean_text(raw)
    assert "2026" not in cleaned
    assert "100" not in cleaned
    assert "the year recorded new astronomical events" == cleaned


def test_remove_stopwords():
    text = "the president of the united states went to the summit"
    filtered = remove_stopwords(text)
    # 'the', 'of', 'to' must be removed
    assert "the" not in filtered.split()
    assert "president united states went summit" == filtered


def test_preprocess_news_combines_title_and_text():
    title = "Historic Peace Accord Signed"
    text = "Leaders gathered in Geneva today to formally sign the agreement."
    result = preprocess_news(title, text)
    assert "historic" in result
    assert "peace" in result
    assert "accord" in result
    assert "geneva" in result
    assert "agreement" in result


def test_tokenize():
    text = "quick brown fox"
    tokens = tokenize(text)
    assert tokens == ["quick", "brown", "fox"]


def test_empty_input_handling():
    assert preprocess_news("", "") == ""
    assert preprocess_news(None, None) == ""
    assert clean_text("") == ""

