"""Synthetic Indian-style cybercrime complaint narrative generator.

Generates realistic NCRP / 1930 incident reports with strict referential consistency
to synthetic bank accounts, UPI IDs, phone numbers, and transactions.
"""

import random
from typing import Any, Dict

NARRATIVE_TEMPLATES = {
    "UPI fraud": [
        (
            "Complainant {victim_name} (A/C: {victim_account}) was attempting to sell home furniture on online classifieds. "
            "The suspect contacting from mobile number {suspect_phone} agreed to purchase for ₹{amount} and sent a QR code stating "
            "'Scan to receive advance token money into your account'. Upon scanning the QR code and entering UPI PIN on mobile app, "
            "an unauthorized debit of ₹{amount} occurred immediately. The money was credited to suspect UPI ID {suspect_upi} "
            "(linked to {suspect_account} at {bank_name}). Suspect subsequently switched off phone."
        ),
        (
            "Citizen {victim_name} reports unauthorized UPI transfer of ₹{amount} from account {victim_account}. "
            "Victim received an alert on phone that cashback reward was approved. Clicked on link sent by suspect ({suspect_phone}) "
            "which redirected to a counterfeit payment gateway page. Entered UPI credentials believing it was a credit transaction. "
            "Funds were routed to suspect VPA {suspect_upi} and beneficiary account {suspect_account}. "
            "Request immediate golden-hour lien hold."
        ),
    ],
    "KYC fraud": [
        (
            "Complainant {victim_name} received an urgent SMS: 'Dear Customer, your electricity connection / SIM card will be "
            "disconnected tonight at 9:30 PM due to pending KYC update. Call executive at {suspect_phone}'. "
            "Complainant called the number; the impersonator instructed download of 'MahaBijli_Update.apk' / QuickSupport. "
            "Upon following instructions to pay ₹10 processing fee, suspect obtained remote device control and executed "
            "unauthorized debit of ₹{amount} transferred to suspect account {suspect_account} via UPI VPA {suspect_upi}."
        ),
        (
            "Victim reports banking KYC suspension scare. Suspect calling from {suspect_phone} claimed to be nodal KYC manager from {bank_name}. "
            "Stated victim's debit card would be permanently blocked unless PAN details re-verified. Victim shared OTP under duress. "
            "Immediately ₹{amount} debited from A/C {victim_account} and credited to suspect account {suspect_account} (UPI: {suspect_upi})."
        ),
    ],
    "investment fraud": [
        (
            "Complainant {victim_name} was added to a Telegram group 'Institutional Wealth & High-Yield IPO Club'. "
            "Admin ({suspect_phone}) promised guaranteed 300% weekly returns on institutional block trading. Complainant initially "
            "tested small amount and was shown virtual profits on a fake web dashboard 'synth-market-pro.com'. "
            "Persuaded to invest principal savings of ₹{amount}, complainant transferred funds from A/C {victim_account} to suspect "
            "current account {suspect_account} (VPA: {suspect_upi}). When requesting withdrawal, suspect demanded 35% tax clearance fee. "
            "Complainant realized fraud when removed from the group."
        ),
        (
            "Victim enticed by Instagram sponsored ad for institutional forex trading. Contacted handler over WhatsApp ({suspect_phone}). "
            "Instructed to deposit margin money of ₹{amount} into beneficiary bank account {suspect_account} ({bank_name}). "
            "Suspect operated via UPI {suspect_upi}. Platform ceased functioning 48 hours post fund transfer. Suspects untraceable."
        ),
    ],
    "fake customer care": [
        (
            "Complainant {victim_name} was seeking refund for an airline ticket cancellation and searched for customer helpline on Google. "
            "Called top sponsored result displaying number {suspect_phone}. Fraudster posing as airline support agent claimed refund "
            "could only be processed via UPI reverse-validation. Instructed complainant to enter ₹{amount} in payment field. "
            "Instead of credit, ₹{amount} was debited from complainant's account {victim_account} to suspect VPA {suspect_upi} "
            "(Account: {suspect_account}). Fraudster disconnected call immediately."
        ),
        (
            "Victim faced failed ATM withdrawal and searched for bank helpline on web. Reached fraud number {suspect_phone}. "
            "Impersonator claiming to be technical officer at {bank_name} sent refund registration link. "
            "Victim filled card credentials, resulting in fraudulent transfer of ₹{amount} to suspect account {suspect_account}."
        ),
    ],
    "phishing": [
        (
            "Victim {victim_name} received email/SMS titled 'ITR Tax Refund Approved: Click to verify bank account for direct deposit'. "
            "Clicked on link 'incometax-refund-gov-in.online' which replicated official portal. Entered netbanking username, password, "
            "and OTP. Unauthorized transaction of ₹{amount} executed within 4 minutes from account {victim_account} to suspect "
            "beneficiary account {suspect_account} (UPI: {suspect_upi})."
        ),
        (
            "Complainant received SMS regarding reward points expiry of credit card. Clicked phishing link and entered credit card CVV and OTP. "
            "Funds amounting to ₹{amount} siphoned off to suspect account {suspect_account} under guise of merchant utility credit."
        ),
    ],
    "loan scam": [
        (
            "Complainant {victim_name} downloaded instant loan application 'QuickRupee Instant Credit' from third-party APK link. "
            "App requested full contacts and gallery permissions. A small loan was disbursed, but within 6 days suspect calling from "
            "{suspect_phone} began severe extortion, threatening to circulate morphed photographs to family and colleagues. "
            "Under extreme duress, complainant transferred ₹{amount} from A/C {victim_account} to suspect account {suspect_account} "
            "via UPI ID {suspect_upi}."
        ),
        (
            "Instant micro-finance extortion report. Victim harassed by recovery executives from number {suspect_phone}. "
            "Complainant coerced into paying inflated penalty charges of ₹{amount} into designated suspect account {suspect_account} "
            "(linked to {bank_name}). Complainant seeks immediate police protection and freezing of suspect receiver account."
        ),
    ],
    "job scam": [
        (
            "Victim {victim_name} was approached on Telegram by recruiter offering part-time remote work rating 5-star hotels and YouTube videos. "
            "Earned initial payout of ₹800 to build trust. Subsequently assigned 'VIP Merchant Evaluation Tasks' requiring prepaid crypto "
            "deposits. Complainant transferred total of ₹{amount} from account {victim_account} to suspect account {suspect_account} "
            "(UPI: {suspect_upi}, Coordinator Phone: {suspect_phone}). Task wallet balance was frozen and admin demanded further ₹1,00,000 "
            "for code unlocking."
        ),
        (
            "Complainant duped in fake Amazon data entry job. Suspect on WhatsApp ({suspect_phone}) collected ₹{amount} across multiple "
            "transfers into beneficiary account {suspect_account} under the pretext of security deposit and server software license fees. "
            "Job offer letter proved counterfeit."
        ),
    ],
    "impersonation": [
        (
            "Complainant {victim_name} received automated call stating: 'This is FedEx Courier Services. A parcel sent from Mumbai to Taiwan "
            "containing 5 passports, 140 grams MDMA and illegal currency has been seized under your Aadhaar number'. "
            "Call was forwarded to fake police officer ({suspect_phone}) posing as DCP Crime Branch. Impersonator threatened imminent "
            "non-bailable warrant and directed transfer of ₹{amount} 'asset verification fund' to government-monitored RBI escrow account "
            "{suspect_account} ({bank_name}, UPI: {suspect_upi}). Complainant complied out of acute panic."
        ),
        (
            "Fraudster posing as TRAI / Mumbai Police officer contacted victim from {suspect_phone}. Stated mobile number was implicated in "
            "terror financing. Demanded security clearance transfer of ₹{amount} from account {victim_account} into suspect account "
            "{suspect_account}. Suspect exhibited fake department ID card over video call."
        ),
    ],
    "digital arrest scam": [
        (
            "CRITICAL CYBER FRAUD INCIDENT: Senior citizen {victim_name} was subjected to a 14-hour 'Digital Arrest' via Skype video call. "
            "Suspects dressed in Indian Police Service and CBI uniforms presented fake Supreme Court arrest warrants and RBI letters. "
            "Victim was forbidden from disconnecting video or alerting family members under threat of immediate SWAT raid. "
            "Instructed to liquidate fixed deposits and wire ₹{amount} from account {victim_account} to an 'interim legal clearance "
            "safekeeping account' {suspect_account} at {bank_name} (UPI: {suspect_upi}). Suspect device operated through coordinated "
            "syndicate network."
        ),
        (
            "Complainant placed under 8-hour digital custody by impostors claiming to be Enforcement Directorate (ED) headquarters New Delhi. "
            "Instructed to break mutual funds and RTGS ₹{amount} into designated suspect account {suspect_account} "
            "(facilitator contact: {suspect_phone}). Realized scam only after consulting real bank branch manager next morning."
        ),
    ],
    "online shopping fraud": [
        (
            "Complainant {victim_name} ordered a heavily discounted electronic appliance / flagship mobile phone from Instagram page "
            "'SuperDeals India' for ₹{amount}. Transferred money via UPI from account {victim_account} to suspect merchant VPA {suspect_upi} "
            "(linked account: {suspect_account}, contact: {suspect_phone}). Consignment tracking number provided was fraudulent. "
            "Suspect blocked complainant on social media and phone remained switched off."
        ),
        (
            "Victim attempted to purchase second-hand motorcycle on online marketplace. Seller ({suspect_phone}) claimed to be Indian Army "
            "officer transferred out of state. Demanded ₹{amount} advance for military transport gate pass into account {suspect_account}. "
            "Neither vehicle delivered nor advance refunded."
        ),
    ],
}


def generate_complaint_narrative(entity_context: Dict[str, Any]) -> str:
    """Generate a context-aware narrative embedding exact synthetic entity identifiers."""
    category = entity_context.get("category", "UPI fraud")
    templates = NARRATIVE_TEMPLATES.get(category, NARRATIVE_TEMPLATES["UPI fraud"])
    template = random.choice(templates)

    narrative = template.format(
        victim_name=entity_context.get("victim_name", "Citizen"),
        victim_account=entity_context.get("victim_account", "SYN1000000001"),
        suspect_account=entity_context.get("suspect_account", "SYN9000000001"),
        suspect_upi=entity_context.get("suspect_upi", "mule@synaxis"),
        suspect_phone=entity_context.get("suspect_phone", "+919876543210"),
        amount=f"{float(entity_context.get('amount', 25000)):,.2f}",
        bank_name=entity_context.get("bank_name", "State Bank of Synth"),
    )
    return narrative
