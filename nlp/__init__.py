"""Natural Language Processing module for cybercrime narrative analysis."""

from nlp.preprocessing.text_preprocessor import TextPreprocessor
from nlp.extractors.regex_extractor import RawEntity, RegexStructuredExtractor
from nlp.extractors.ner_extractor import SpacyNERExtractor
from nlp.extractors.hybrid_extractor import HybridEntityExtractor
from nlp.classifiers.scam_classifier import ScamCategoryClassifier
from nlp.normalizers.entity_normalizer import EntityNormalizer, NormalizedEntity
from nlp.linking.entity_linker import EntityLinker
from nlp.pipelines.cybercrime_nlp_pipeline import CybercrimeNLPPipeline, ComplaintExtractionResult
from nlp.evaluation.evaluator import ComplaintGroundTruthEvaluator, NLPEvaluationMetrics

# Maintain backward compatibility with initial prototype
CybercrimeEntityExtractor = RegexStructuredExtractor

__all__ = [
    "TextPreprocessor",
    "RawEntity",
    "RegexStructuredExtractor",
    "SpacyNERExtractor",
    "HybridEntityExtractor",
    "ScamCategoryClassifier",
    "EntityNormalizer",
    "NormalizedEntity",
    "EntityLinker",
    "CybercrimeNLPPipeline",
    "ComplaintExtractionResult",
    "ComplaintGroundTruthEvaluator",
    "NLPEvaluationMetrics",
    "CybercrimeEntityExtractor",
]
