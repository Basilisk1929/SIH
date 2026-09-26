"""Tests for scam category classifier covering all 10 typologies."""

import pytest
from nlp.classifiers.scam_classifier import ScamCategoryClassifier


@pytest.mark.parametrize(
    "text,expected_category",
    [
        (
            "Suspect sent QR code saying scan to receive advance payment. Entered UPI PIN and unauthorized debit happened.",
            "UPI fraud",
        ),
        (
            "SMS received stating electricity will be disconnected tonight due to pending KYC update. Asked to download APK.",
            "KYC fraud",
        ),
        (
            "Telegram group promising 300% weekly returns on institutional IPO and block trading. Transferred principal margin money.",
            "investment fraud",
        ),
        (
            "Called fake airline customer helpline on Google for flight cancellation refund. Reverse validation link sent.",
            "fake customer care",
        ),
        (
            "Email received regarding ITR tax refund direct deposit. Entered netbanking username and OTP on replicated official portal.",
            "phishing",
        ),
        (
            "QuickRupee loan app accessed full contacts and gallery. Recovery agents threatening to send morphed photos to relatives.",
            "loan scam",
        ),
        (
            "Offered part-time remote work rating 5-star hotels and YouTube videos. Demanded prepaid crypto deposit for VIP task.",
            "job scam",
        ),
        (
            "Automated call stating FedEx courier from Mumbai with illegal contraband and MDMA seized. Forwarded to fake DCP Crime Branch.",
            "impersonation",
        ),
        (
            "Senior citizen held under 14-hour digital arrest via Skype video call by fake CBI officers presenting arrest warrants.",
            "digital arrest scam",
        ),
        (
            "Ordered discounted phone on Instagram page SuperDeals. Consignment tracking was fake and suspect blocked complainant.",
            "online shopping fraud",
        ),
    ],
)
def test_classifier_identifies_all_ten_scam_categories(text, expected_category):
    category, confidence, probs = ScamCategoryClassifier.classify_with_distribution(text)
    assert category == expected_category
    assert confidence >= 0.70
    assert len(probs) == 10
