# NLP Pipeline for Cybercrime Incident Narratives

## Overview
The Natural Language Processing (NLP) subsystem ingests unstructured cyber incident complaint narratives (from NCRP 1930 reports) and extracts structured forensic evidence, normalizes entities, links them to knowledge base registries, and categorizes incidents across 10 cyber scam typologies.

```
Raw Narrative ──> [Text Preprocessor] ──> [Hybrid Extractor (spaCy + Regex)]
                                                      │
                                                      ├──> [Scam Category Classifier]
                                                      │
                                                      ├──> [Entity Normalizer]
                                                      │
                                                      └──> [Entity Linker]
                                                               │
                                                               ▼
                                                  [Structured Forensic Result]
```

---

## 1. Extracted Entities (10 Types)
- **`PERSON`**: Complainant, victim, suspect alias, or impersonated officer names (e.g. `Neha Singh`, `Ramesh Roy`, `DCP Crime Branch`).
- **`BANK`**: Financial institutions and banks mentioned (e.g. `State Bank of Synth`, `Synth ICICI Banking Corp`, `HDFC`).
- **`ACCOUNT`**: Bank account numbers (`SYN1000004465`, 9-18 digit accounts).
- **`PHONE`**: Indian mobile numbers (`+919836271527`, 10-digit mobile formats).
- **`UPI_ID`**: UPI VPAs / payment handles (`nikhil.mishra.971@synoksbi`, `mule.88@synfree`).
- **`AMOUNT`**: Monetary losses (`₹49,999.00`, `Rs. 25,000`, `10000 INR`).
- **`LOCATION`**: Cities, states, or cybercrime hotspots (`Mumbai`, `Lucknow`, `Jamtara-Karmatanr`).
- **`DATE`**: Incident dates and timestamps (`2024-08-15`, `14-hour`, `tonight at 9:30 PM`).
- **`TRANSACTION_ID`**: Transaction reference numbers (`TXN_00038001`, `UTR123456789012`, `RRN987654321012`).
- **`SCAM_TYPE`**: Modus operandi or typology mentioned in text (`UPI fraud`, `digital arrest scam`, `loan scam`).

---

## 2. Pipeline Components

1. **Preprocessing (`nlp.preprocessing.TextPreprocessor`)**:
   - Unicode NFKC normalization.
   - Stripping zero-width and invisible control characters (`\u200B`, `\uFEFF`).
   - Normalizing quotes, dashes, and whitespace without corrupting character offsets.

2. **Entity Extraction (`nlp.extractors.ner_extractor.SpacyNERExtractor`)**:
   - Uses `spacy` (`en_core_web_sm`) statistical NER for `PERSON`, `GPE`/`LOC`, `ORG`, `DATE`.
   - PhraseMatcher gazetteers for known banks, locations, and scam labels.
   - Complainant name pattern matching.

3. **Regex Extraction for Structured Values (`nlp.extractors.regex_extractor.RegexStructuredExtractor`)**:
   - High-precision regular expressions capturing phone numbers, UPI handles, synthetic accounts, transaction references, amounts, and dates.
   - Merged in `nlp.extractors.HybridEntityExtractor` with priority-ordered conflict resolution.

4. **Scam Category Classifier (`nlp.classifiers.scam_classifier.ScamCategoryClassifier`)**:
   - Multi-class classification across 10 scam categories:
     1. `UPI fraud`
     2. `KYC fraud`
     3. `investment fraud`
     4. `fake customer care`
     5. `phishing`
     6. `loan scam`
     7. `job scam`
     8. `impersonation`
     9. `digital arrest scam`
     10. `online shopping fraud`
   - Uses weighted lexical n-grams, softmax normalization, and margin-based confidence calibration.

5. **Entity Normalization (`nlp.normalizers.EntityNormalizer`)**:
   - `PHONE` -> Standard E.164 (`+919836271527`).
   - `AMOUNT` -> Numeric float (`49999.0`).
   - `UPI_ID` -> Lowercase stripped (`nikhil.mishra.971@synoksbi`).
   - `BANK` -> Canonical institution name (`State Bank of Synth`).
   - `ACCOUNT` -> Uppercase standardized (`SYN1000004465`).

6. **Entity Linking (`nlp.linking.EntityLinker`)**:
   - Resolves entities against synthetic databases (`accounts`, `upi_ids`, `phone_numbers`, `locations`).
   - Attaches risk indicators (e.g. `is_mule: True`, `mule_tier: 1`, `is_cybercrime_hotspot: True`).

7. **Ground-Truth Evaluation (`nlp.evaluation.ComplaintGroundTruthEvaluator`)**:
   - Evaluates pipeline against `complaints.csv` ground truth.
   - Calculates Precision, Recall, and F1 score per entity type and macro/micro averages.

---

## 3. REST API Microservice

Run the standalone FastAPI microservice:
```bash
uvicorn nlp.api.service:app --host 127.0.0.1 --port 8003
```

### Endpoints:

#### `POST /nlp/extract`
**Request:**
```json
{
  "text": "Citizen Neha Singh reports unauthorized UPI transfer of ₹49,999.00 from account SYN1000004465. Clicked on link sent by suspect (+919836271527). Funds were routed to suspect VPA nikhil.mishra.971@synoksbi and beneficiary account SYN1000002170.",
  "link_entities": true
}
```

**Response:**
```json
{
  "scam_type": "UPI fraud",
  "confidence": 0.98,
  "category_probabilities": {
    "UPI fraud": 0.5062,
    "KYC fraud": 0.0549,
    ...
  },
  "entities": [
    {
      "text": "Neha Singh",
      "label": "PERSON",
      "start": 8,
      "end": 18,
      "normalized_value": "Neha Singh",
      "confidence": 0.95,
      "extractor": "spacy_matcher",
      "linked_entity": null
    },
    {
      "text": "SYN1000004465",
      "label": "ACCOUNT",
      "start": 68,
      "end": 81,
      "normalized_value": "SYN1000004465",
      "confidence": 0.99,
      "extractor": "regex",
      "linked_entity": {
        "entity_type": "Account",
        "account_number": "SYN1000004465",
        "bank_name": "Union Synth Bank of India",
        "is_mule": false,
        "is_known_entity": true
      }
    }
  ],
  "metadata": {
    "processing_time_ms": 14.2,
    "entities_count": 5,
    "text_length": 258
  }
}
```

#### `POST /nlp/evaluate`
**Request:**
```json
{
  "sample_size": 100
}
```
**Response:**
```json
{
  "evaluated_complaints_count": 100,
  "scam_classification_accuracy": 1.0,
  "macro_averages": {
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0
  },
  "micro_averages": {
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0
  },
  "per_entity_metrics": { ... }
}
```

#### `GET /nlp/health`
Health probe for readiness and model status.
