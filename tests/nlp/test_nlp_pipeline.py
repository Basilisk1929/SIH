"""Tests for end-to-end cybercrime NLP pipeline."""

from nlp.pipelines.cybercrime_nlp_pipeline import CybercrimeNLPPipeline


def test_pipeline_end_to_end_extraction_and_classification():
    pipeline = CybercrimeNLPPipeline()
    complaint = (
        "Citizen Neha Singh reports unauthorized UPI transfer of ₹49,999.00 from account SYN1000004465. "
        "Clicked on link sent by suspect (+919836271527) which redirected to a counterfeit payment gateway page. "
        "Funds were routed to suspect VPA nikhil.mishra.971@synoksbi and beneficiary account SYN1000002170."
    )
    result = pipeline.process(complaint, link_entities=True)

    assert result.scam_type == "UPI fraud"
    assert result.confidence >= 0.80
    assert len(result.entities) >= 5

    entity_types = {e.label for e in result.entities}
    assert "ACCOUNT" in entity_types
    assert "AMOUNT" in entity_types
    assert "UPI_ID" in entity_types
    assert "PHONE" in entity_types

    # Verify dictionary serialization
    d = result.to_dict()
    assert d["scam_type"] == "UPI fraud"
    assert "metadata" in d
    assert d["metadata"]["entities_count"] == len(result.entities)
