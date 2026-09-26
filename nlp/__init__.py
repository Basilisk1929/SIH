"""Natural Language Processing module for cybercrime narrative analysis."""

from nlp.extractors.entity_extractor import CybercrimeEntityExtractor
from nlp.classifiers.scam_classifier import ScamCategoryClassifier

__all__ = ["CybercrimeEntityExtractor", "ScamCategoryClassifier"]
