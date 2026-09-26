"""End-to-end NLP pipeline for Indian cybercrime complaint narratives."""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from nlp.preprocessing.text_preprocessor import TextPreprocessor
from nlp.extractors.hybrid_extractor import HybridEntityExtractor
from nlp.classifiers.scam_classifier import ScamCategoryClassifier
from nlp.normalizers.entity_normalizer import EntityNormalizer, NormalizedEntity
from nlp.linking.entity_linker import EntityLinker


@dataclass
class ComplaintExtractionResult:
    """Complete output of the NLP complaint analysis pipeline."""
    original_text: str
    cleaned_text: str
    scam_type: str
    confidence: float
    category_probabilities: Dict[str, float]
    entities: List[NormalizedEntity]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to clean JSON-serializable dictionary."""
        return {
            "scam_type": self.scam_type,
            "confidence": self.confidence,
            "category_probabilities": self.category_probabilities,
            "entities": [e.to_dict() for e in self.entities],
            "metadata": {
                "processing_time_ms": round(self.processing_time_ms, 2),
                "entities_count": len(self.entities),
                "text_length": len(self.cleaned_text),
                **self.metadata,
            },
        }


class CybercrimeNLPPipeline:
    """Production NLP pipeline orchestrating preprocessing, NER, classification, normalization, and linking."""

    def __init__(
        self,
        hybrid_extractor: Optional[HybridEntityExtractor] = None,
        entity_linker: Optional[EntityLinker] = None,
    ):
        self.extractor = hybrid_extractor or HybridEntityExtractor()
        self.classifier = ScamCategoryClassifier()
        self.normalizer = EntityNormalizer()
        self.linker = entity_linker or EntityLinker()

    def process(self, text: str, link_entities: bool = True) -> ComplaintExtractionResult:
        """Execute end-to-end analysis on raw cyber incident narrative."""
        start_time = time.perf_counter()

        # 1. Preprocessing
        cleaned_text = TextPreprocessor.preprocess(text)

        # 2. Extract Entities via Hybrid SpaCy + Regex Engine
        raw_entities = self.extractor.extract_all(cleaned_text)

        # 3. Classify Scam Category & Calibrate Confidence
        scam_type, confidence, probs = self.classifier.classify_with_distribution(cleaned_text)

        # 4. Normalize Entities
        normalized_entities: List[NormalizedEntity] = [
            self.normalizer.normalize(raw) for raw in raw_entities
        ]

        # 5. Entity Linking (optional)
        if link_entities:
            normalized_entities = [
                self.linker.link_entity(ent) for ent in normalized_entities
            ]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ComplaintExtractionResult(
            original_text=text,
            cleaned_text=cleaned_text,
            scam_type=scam_type,
            confidence=confidence,
            category_probabilities=probs,
            entities=normalized_entities,
            processing_time_ms=elapsed_ms,
        )
