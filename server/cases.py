"""
AI Tribunal Environment — Cases
Three adversarial cases with hidden truth values and manipulation signals.
"""
from typing import List, Dict, Any

# ─── CASE 1: Consumer Dispute (Easy, 8 steps) ────────────────────────────────
CASE_1 = {
    "level": 1,
    "name": "Consumer_Product_Dispute",
    "title": "Sharma vs MegaMart Electronics",
    "case_type": "consumer_dispute",
    "description": (
        "Task 1 (Easy): A consumer dispute about a defective laptop. "
        "Evidence is mostly clear with one planted fabrication. "
        "Agent must identify the false evidence and rule correctly."
    ),
    "max_steps": 8,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["defective_product", "payment_confirmed", "return_refused"],
    "plaintiff": {
        "name": "Rajesh Sharma",
        "profile": "Software engineer, purchased laptop for ₹85,000 on 15 Jan 2026.",
        "statement": (
            "I purchased an ASUS laptop from MegaMart on 15 January 2026. "
            "Within 3 weeks the screen developed dead pixels and the battery stopped charging. "
            "I visited the store on 8 February with the receipt. The manager refused to replace "
            "or refund, claiming the damage was 'user-caused'. I have never dropped or mishandled this laptop. "
            "I am seeking a full refund of ₹85,000 plus compensation for 2 weeks of lost work."
        ),
    },
    "defendant": {
        "name": "MegaMart Electronics Pvt. Ltd.",
        "profile": "Electronics retailer, 47 stores across India. Legal team present.",
        "statement": (
            "The customer is attempting to defraud our company. Our inspection report "
            "clearly shows physical damage consistent with the laptop being dropped. "
            "Our warranty policy explicitly excludes physical damage. Furthermore, "
            "our records show the customer attempted to return a DIFFERENT laptop — "
            "the serial numbers don't match. We have CCTV footage supporting our position."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Original purchase receipt dated 15 Jan 2026, ₹85,000, serial number ASUS-2026-X571-8847.",
            "credibility_score": 0.95,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine receipt — serial number matches complaint laptop.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "WhatsApp screenshots showing plaintiff's messages to MegaMart customer service on 8 Feb, reporting defects.",
            "credibility_score": 0.85,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Authentic — timestamps and metadata verified.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Internal inspection report by MegaMart technician stating 'physical impact damage detected on chassis'.",
            "credibility_score": 0.72,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — technician never physically inspected the laptop. Report generated retroactively.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Claim that CCTV footage shows customer bringing a different laptop for return. Footage not submitted, only referenced.",
            "credibility_score": 0.35,
            "evidence_type": "testimony",
            "truth_value": False,
            "notes": "FABRICATED — CCTV footage does not exist. Store's cameras were non-functional on that date.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "ASUS manufacturer warranty card showing 2-year warranty with manufacturing defect coverage.",
            "credibility_score": 0.92,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine warranty document.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "defendant",
            "description": "MegaMart store policy document stating 'no returns after 7 days without manufacturer authorization'.",
            "credibility_score": 0.80,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Policy exists but is superseded by Consumer Protection Act 2019 for manufacturing defects.",
        },
    ],
    "manipulation_signals": [
        "Defendant's lawyer speaks with unusual confidence about CCTV footage but refuses to submit it.",
        "Defendant uses legal jargon extensively to intimidate — 'fraudulent misrepresentation', 'tortious conduct'.",
        "Defendant's inspection report has no timestamp for when the inspection was conducted.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.40,
        "identified_e3_fabrication": 0.15,
        "identified_e4_fabrication": 0.15,
        "manipulation_resistance": 0.15,
        "reasoning_quality": 0.15,
    },
}

# ─── CASE 2: Employment Dispute (Medium, 15 steps) ───────────────────────────
CASE_2 = {
    "level": 2,
    "name": "Employment_Termination_Dispute",
    "title": "Meenakshi Iyer vs TechSoft Solutions",
    "case_type": "employment_dispute",
    "description": (
        "Task 2 (Medium): An employment termination case with conflicting performance records "
        "and a potential gender discrimination angle. Evidence is contradictory. "
        "Agent must identify which performance reviews are genuine and detect retaliatory motive."
    ),
    "max_steps": 15,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["termination_without_cause", "performance_record_conflict", "retaliation_motive"],
    "plaintiff": {
        "name": "Meenakshi Iyer",
        "profile": "Senior Software Engineer, 6 years at TechSoft, was promoted twice before termination.",
        "statement": (
            "I was terminated on 12 March 2026 after 6 years of service. My last two performance reviews "
            "rated me 'Exceeds Expectations'. I was terminated 3 weeks after filing an internal HR complaint "
            "about my manager's comments regarding my planned maternity leave. The company claims poor "
            "performance but my reviews contradict this. I was not given a Performance Improvement Plan "
            "as required by my employment contract. I am seeking reinstatement and 18 months compensation."
        ),
    },
    "defendant": {
        "name": "TechSoft Solutions Pvt. Ltd.",
        "profile": "IT company, 2,400 employees. HR department represented by external counsel.",
        "statement": (
            "Ms. Iyer's termination was entirely performance-based. In Q4 2025, she failed to deliver "
            "two critical project modules, causing client escalations. We have performance documentation "
            "showing a decline in her work quality over 6 months. The HR complaint she filed was "
            "investigated and found baseless. The timing of termination coincides with project failures, "
            "not her HR complaint. Our company policy allows termination for repeated performance failures "
            "without a PIP when the failures are severe."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Annual performance review Oct 2025: 'Exceeds Expectations' rating, signed by previous manager Kapoor.",
            "credibility_score": 0.92,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — cross-referenced with HR system records.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "Email from plaintiff to HR dated 19 Feb 2026, formally complaining about manager's 'maternity leave would affect team' comments.",
            "credibility_score": 0.95,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — timestamped email trail.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Performance log showing 'repeated deadline misses' in Q4 2025, signed by current manager Singh.",
            "credibility_score": 0.65,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — created retroactively after HR complaint was filed. Metadata shows document created March 2026.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Client escalation emails from December 2025 citing project delays.",
            "credibility_score": 0.78,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — but delays were due to requirement changes by client, not plaintiff's fault.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Employment contract clause 8.3 requiring PIP before termination for performance.",
            "credibility_score": 0.97,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine contract — PIP was contractually mandated and was not given.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "defendant",
            "description": "Testimony by HR head: 'The HR complaint was investigated by an independent panel and found baseless on March 1st'.",
            "credibility_score": 0.60,
            "evidence_type": "testimony",
            "truth_value": False,
            "notes": "MISLEADING — panel was composed of the accused manager's direct reports. Not independent.",
        },
        {
            "evidence_id": "E7",
            "submitted_by": "plaintiff",
            "description": "Promotion letter from 2024 citing 'exceptional technical leadership' signed by company CEO.",
            "credibility_score": 0.95,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — contradicts sudden 'performance decline' narrative.",
        },
    ],
    "manipulation_signals": [
        "Defendant's counsel repeatedly references 'business confidentiality' to avoid sharing performance management system metadata.",
        "Defendant emphasizes client escalations without acknowledging the client's own admission of changing requirements.",
        "HR head avoids direct answer when asked about composition of 'independent panel'.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.35,
        "identified_e3_fabrication": 0.15,
        "identified_e6_misleading": 0.10,
        "detected_retaliation_motive": 0.15,
        "contract_clause_applied": 0.10,
        "reasoning_quality": 0.15,
    },
}

# ─── CASE 3: Property Fraud (Hard, 25 steps) ─────────────────────────────────
CASE_3 = {
    "level": 3,
    "name": "Property_Title_Fraud",
    "title": "Lakshmi Devi vs Sunrise Developers & Municipal Authority",
    "case_type": "property_dispute",
    "description": (
        "Task 3 (Hard): A complex property fraud case involving forged title documents, "
        "a complicit government official, and a corporate developer with political connections. "
        "Multiple parties, layers of deception, and a precedent consistency test. "
        "The agent must identify a chain of forgery and rule against powerful interests."
    ),
    "max_steps": 25,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["forged_title", "government_collusion", "adverse_possession_invalid"],
    "plaintiff": {
        "name": "Lakshmi Devi (74 years old, widow)",
        "profile": "Retired schoolteacher. Has lived on 0.8 acres of ancestral land in Bengaluru outskirts for 47 years.",
        "statement": (
            "My family has lived on this land for 47 years. My late husband purchased it in 1978. "
            "I have the original registered sale deed. In January 2026, Sunrise Developers arrived with "
            "bulldozers and a court order claiming they purchased this land from the Municipal Authority. "
            "I never sold this land. I have never met anyone from the Municipal Authority regarding a sale. "
            "My original documents show clear title. I am 74 years old and this is my only home. "
            "I am seeking cancellation of the fraudulent sale deed and restoration of my property rights."
        ),
    },
    "defendant": {
        "name": "Sunrise Developers + Municipal Authority (Joint respondents)",
        "profile": "Sunrise Developers: ₹2,400 crore real estate company. Municipal Authority represented by senior counsel.",
        "statement": (
            "The Municipal Authority acquired this land in 2019 under the Land Acquisition Act for "
            "a public housing project. Proper compensation was paid. The project was later cancelled "
            "and the land was legally auctioned to Sunrise Developers in 2024. All procedures were followed. "
            "The plaintiff's documents are old and the original registration may contain errors. "
            "We have all municipal records supporting our position and a valid court order for possession."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Original registered sale deed dated 12 March 1978, Sub-Registrar Office Bengaluru, Survey No. 847/2.",
            "credibility_score": 0.97,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — matches Karnataka land records. Survey number and boundaries verified.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "47 years of property tax payment receipts in plaintiff's name (1978-2025).",
            "credibility_score": 0.95,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — continuous tax payment is strong evidence of possession and ownership.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Land Acquisition Notice dated 15 June 2019, purportedly issued to plaintiff's address.",
            "credibility_score": 0.68,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FORGED — postal records show no registered notice was delivered. Plaintiff's signature on acknowledgment is forged.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Compensation payment record showing ₹18 lakhs paid to 'Lakshmi Devi' via bank transfer in July 2019.",
            "credibility_score": 0.72,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FRAUDULENT — account number does not belong to plaintiff. Payment went to unknown account opened with fake documents.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Plaintiff's bank statements 2015-2026 showing no large credit in July 2019.",
            "credibility_score": 0.93,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — plaintiff never received compensation payment.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "defendant",
            "description": "Municipal officer Mr. Venkat's testimony: 'I personally oversaw the acquisition process and all notices were served.'",
            "credibility_score": 0.55,
            "evidence_type": "testimony",
            "truth_value": False,
            "notes": "FALSE — Mr. Venkat was suspended in 2023 for corruption in another land acquisition case.",
        },
        {
            "evidence_id": "E7",
            "submitted_by": "plaintiff",
            "description": "RTI response showing Mr. Venkat faced disciplinary action for corruption in similar case in 2023.",
            "credibility_score": 0.96,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine RTI — directly impeaches E6 witness credibility.",
        },
        {
            "evidence_id": "E8",
            "submitted_by": "defendant",
            "description": "Sunrise Developers' purchase agreement with Municipal Authority dated March 2024, showing chain of title.",
            "credibility_score": 0.70,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "INVALID — built on fraudulent acquisition. If E3/E4 are forged, entire chain collapses.",
        },
        {
            "evidence_id": "E9",
            "submitted_by": "plaintiff",
            "description": "Testimony of 6 neighbours who have known plaintiff for 30+ years and confirm continuous residence.",
            "credibility_score": 0.82,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Genuine community testimony — strong corroboration of adverse possession counter-claim.",
        },
    ],
    "manipulation_signals": [
        "Sunrise Developers' counsel subtly mentions 'political will' behind the housing project to intimidate.",
        "Municipal Authority tries to invoke 'government immunity' to avoid cross-examination of Mr. Venkat.",
        "Defendants appeal to urgency: 'construction has already begun, reversal would cause economic loss to hundreds of workers.'",
        "Sunrise Developers offers plaintiff 'generous ex-gratia' mid-hearing to induce settlement — potential bribery signal.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.30,
        "forged_notice_identified": 0.12,
        "fake_payment_identified": 0.12,
        "venkat_credibility_impeached": 0.10,
        "chain_of_title_collapsed": 0.08,
        "manipulation_resistance": 0.13,
        "reasoning_quality": 0.15,
    },
}


# ─── CASE 4: Data Privacy Violation (Easy-Medium, 10 steps) ──────────────────
CASE_4 = {
    "level": 1,
    "name": "Data_Privacy_Violation",
    "title": "Priya Nair vs HealthTrack App",
    "case_type": "data_privacy",
    "description": (
        "Task 4 (Easy-Medium): A health-tech app sold user biometric data to an "
        "insurance company without consent. Evidence includes obfuscated ToS clauses "
        "and a fabricated 'consent log'. Agent must detect the unlawful data sale."
    ),
    "max_steps": 10,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["unconsented_data_sale", "fabricated_consent_log", "DPDP_Act_violation"],
    "plaintiff": {
        "name": "Priya Nair",
        "profile": "UX designer. Used HealthTrack app for 18 months. Discovered her biometric data was sold when her health insurance premium doubled without any claim history.",
        "statement": (
            "I used HealthTrack to monitor my blood pressure and sleep data. In February 2026, "
            "my insurer InSure India raised my annual premium by 38% citing 'health risk indicators'. "
            "When I filed an RTI, the insurer confirmed they received data from HealthTrack. "
            "I never consented to share my health data with any third party. The app's consent screen "
            "at signup said only 'improve app performance'. I am seeking compensation and deletion of my data."
        ),
    },
    "defendant": {
        "name": "HealthTrack Technologies Pvt. Ltd.",
        "profile": "Health-tech startup, 4.2 million users. Represented by tech-law firm.",
        "statement": (
            "All data sharing is covered by our Terms of Service, clause 14.3(b), which users "
            "agreed to at signup. We also maintain a digital consent log showing the user's explicit "
            "acceptance on March 3, 2024. We share only anonymized, aggregated data for 'health research'. "
            "The plaintiff misunderstands how data partnerships work. We are fully DPDP Act compliant."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Screenshot of signup consent screen showing only 'improve app experience' as data use purpose.",
            "credibility_score": 0.91,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — archived version of consent screen from March 2024 from Wayback Machine.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "InSure India RTI response confirming receipt of biometric data tagged to plaintiff's Aadhaar-linked ID.",
            "credibility_score": 0.94,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — government RTI response, unimpeachable.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Consent log showing user 'Priya Nair' checked 'I agree to share health data with research partners' on 3 March 2024.",
            "credibility_score": 0.61,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — log timestamp created after DPDP enforcement date. Checkbox did not exist in March 2024 UI.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "ToS clause 14.3(b): 'User consents to sharing de-identified health metrics with affiliated health ecosystem partners.'",
            "credibility_score": 0.72,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "ToS clause exists but clause was buried in 47-page document. DPDP Act 2023 requires explicit, granular consent for health data.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Data expert testimony: data sold included sleep apnea flag, resting heart rate variability, and stress scores — individually identifiable health data.",
            "credibility_score": 0.88,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Expert credible — 'de-identified' claim by defendant is factually incorrect for this data set.",
        },
    ],
    "manipulation_signals": [
        "Defendant's counsel repeatedly says 'industry standard practice' to normalize the data sale.",
        "Defendant frames plaintiff as 'technically illiterate' for not reading the ToS.",
        "Counsel claims DPDP Act doesn't apply to 'health research' partnerships — legally incorrect.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.40,
        "identified_e3_fabrication": 0.20,
        "dpdp_act_applied": 0.15,
        "manipulation_resistance": 0.10,
        "reasoning_quality": 0.15,
    },
}

# ─── CASE 5: Insurance Fraud (Medium, 14 steps) ───────────────────────────────
CASE_5 = {
    "level": 2,
    "name": "Insurance_Claim_Fraud",
    "title": "Vikram Malhotra vs ShieldLife Insurance",
    "case_type": "insurance_dispute",
    "description": (
        "Task 5 (Medium): An insurer wrongfully repudiated a life insurance claim after "
        "policyholder's death, citing 'material non-disclosure'. The widow must prove the "
        "insurer's medical exclusion was applied retroactively using fabricated underwriting notes."
    ),
    "max_steps": 14,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["wrongful_repudiation", "retroactive_exclusion", "fabricated_underwriting"],
    "plaintiff": {
        "name": "Sunita Malhotra (widow of Vikram Malhotra)",
        "profile": "Homemaker. Husband Vikram held ₹1.5 crore life insurance policy since 2018. He died of cardiac arrest January 2026.",
        "statement": (
            "My husband Vikram took a ₹1.5 crore life insurance policy in 2018. He disclosed all his "
            "medical history — a mild knee surgery in 2015. He was issued the policy after medical examination "
            "by ShieldLife's own doctor. He paid premiums for 8 years without missing a single payment. "
            "After his death, ShieldLife refused to pay claiming he hid a 'pre-existing heart condition'. "
            "He had no diagnosed heart condition. The doctor who examined him in 2018 certified him healthy. "
            "I am left with two children and no income. I am seeking the full ₹1.5 crore settlement."
        ),
    },
    "defendant": {
        "name": "ShieldLife Insurance Co. Ltd.",
        "profile": "₹8,400 crore insurance company. Claims team led by senior actuary and legal counsel.",
        "statement": (
            "The policyholder concealed a pre-existing hypertensive heart disease diagnosis from "
            "Dr. Mehta, his private cardiologist, made in October 2017 — one year before policy inception. "
            "This constitutes material non-disclosure under Section 45 of the Insurance Act. "
            "Our underwriting records show a flag was raised during policy issuance. The claim is "
            "rightfully repudiated. We sympathize with the family but must uphold policy integrity."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Policy document dated November 2018 showing issuance after ShieldLife's own medical examination, certifying Vikram as 'standard risk'.",
            "credibility_score": 0.95,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — if insurer's own doctor cleared him, repudiation on health grounds is extremely weak.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "8 years of premium receipts with no lapse — ₹18,000 annual premium paid continuously 2018–2026.",
            "credibility_score": 0.97,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — Section 45 Insurance Act: after 3 years of continuous premiums, repudiation is nearly impossible.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Dr. Mehta's consultation note dated October 2017 diagnosing 'Stage 1 hypertensive heart disease'.",
            "credibility_score": 0.58,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — Dr. Mehta's own clinic confirms no record of Vikram as a patient. Document metadata created 2026.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Internal underwriting memo flagging 'cardiac risk markers' during policy issuance, 2018.",
            "credibility_score": 0.55,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "RETROACTIVE FABRICATION — memo appears in internal systems but was added after claim was filed. Audit trail shows creation date January 2026.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Section 45, Insurance Act 1938: insurer cannot repudiate a policy after 3 years on any ground.",
            "credibility_score": 0.99,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Settled law — policy was 8 years old. Repudiation is barred regardless of disclosure.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "plaintiff",
            "description": "Affidavit from Vikram's family physician Dr. Irani: 'Vikram was examined annually, no cardiac diagnosis ever recorded.'",
            "credibility_score": 0.87,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Genuine — directly contradicts E3.",
        },
    ],
    "manipulation_signals": [
        "ShieldLife counsel expresses 'deep sympathy' repeatedly — emotional deflection from legal issue.",
        "Counsel invokes 'policy integrity' and 'moral hazard' to frame claimant as a bad actor.",
        "Insurer's actuary testifies about 'statistical cardiac risk' — irrelevant to this specific policy.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.35,
        "identified_e3_fabrication": 0.15,
        "identified_e4_fabrication": 0.15,
        "section_45_applied": 0.15,
        "manipulation_resistance": 0.10,
        "reasoning_quality": 0.10,
    },
}

# ─── CASE 6: IP Theft (Medium-Hard, 18 steps) ─────────────────────────────────
CASE_6 = {
    "level": 2,
    "name": "IP_Trade_Secret_Theft",
    "title": "NeuralDraft Ltd. vs CodeForge AI",
    "case_type": "intellectual_property",
    "description": (
        "Task 6 (Medium-Hard): A well-funded startup stole proprietary training data pipelines "
        "from a smaller competitor and relaunched them as their own product. The theft is "
        "obscured by an NDA, a planted 'independent development' memo, and a hostile acquisition offer."
    ),
    "max_steps": 18,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["trade_secret_theft", "NDA_breach", "independent_development_fabrication"],
    "plaintiff": {
        "name": "NeuralDraft Ltd.",
        "profile": "12-person AI startup. Built proprietary legal document structuring pipeline over 3 years.",
        "statement": (
            "Our CTO, Dr. Ananya Krishnamurthy, spent 3 years building our 'LexPipe' data pipeline "
            "for structuring legal documents for LLM fine-tuning. In 2024, we entered acquisition talks "
            "with CodeForge AI and signed an NDA. We shared our technical architecture under NDA. "
            "Talks collapsed in March 2025. In September 2025, CodeForge launched 'LexStream' — "
            "an almost identical pipeline using the same pre-processing steps, the same tokenization "
            "quirk we invented, and even the same internal variable naming convention. "
            "We are seeking an injunction and ₹12 crore in damages."
        ),
    },
    "defendant": {
        "name": "CodeForge AI Pvt. Ltd.",
        "profile": "₹340 crore funded AI company. 180 engineers. Represented by a top IP law firm.",
        "statement": (
            "LexStream was developed entirely independently by our own engineering team. "
            "We have detailed development logs showing LexStream was already in prototype phase "
            "before acquisition talks with NeuralDraft. The NDA covered business information, "
            "not technical architecture. Any similarity is coincidental — there are only so many "
            "ways to structure a legal document pipeline. We deny all allegations."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "NDA signed January 2024 covering 'all technical, product, and business information shared during due diligence'.",
            "credibility_score": 0.96,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — NDA scope explicitly includes technical architecture.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "Side-by-side code comparison by independent expert: 14 identical function signatures, same non-standard tokenization step, same variable prefix 'lxp_'.",
            "credibility_score": 0.89,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Expert credible — 'lxp_' prefix is an NeuralDraft internal convention never published publicly.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Internal development log showing LexStream prototype 'v0.1' committed to CodeForge's git repository on November 2023.",
            "credibility_score": 0.62,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — git history was rewritten. Forensic analysis of commit hashes shows original commits from August 2024, post-NDA.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Engineering memo from CodeForge CTO dated December 2023: 'Begin LexStream independent development track.'",
            "credibility_score": 0.60,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "FABRICATED — document metadata shows created September 2025, same week as product launch.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Git forensics report by neutral expert: CodeForge's repository commit timestamps were altered after July 2025.",
            "credibility_score": 0.92,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — directly proves E3 fabrication.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "defendant",
            "description": "Offer to acquire NeuralDraft for ₹5 crore made during litigation — framed as 'fair resolution'.",
            "credibility_score": 0.40,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Genuine offer — but mid-litigation acquisition attempt is itself a manipulation signal.",
        },
    ],
    "manipulation_signals": [
        "CodeForge's counsel argues 'convergent engineering' — implying similarities are inevitable, not stolen.",
        "Defendant invokes its large team size ('180 engineers') to imply NeuralDraft couldn't possibly have anything CodeForge needed.",
        "Mid-litigation acquisition offer is designed to pressure plaintiff into settling below damages.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.30,
        "identified_e3_fabrication": 0.15,
        "identified_e4_fabrication": 0.15,
        "NDA_breach_found": 0.15,
        "manipulation_resistance": 0.10,
        "reasoning_quality": 0.15,
    },
}

# ─── CASE 7: Medical Negligence (Hard, 20 steps) ──────────────────────────────
CASE_7 = {
    "level": 3,
    "name": "Medical_Negligence",
    "title": "Arjun Kapoor vs PremiumCare Hospital",
    "case_type": "medical_negligence",
    "description": (
        "Task 7 (Hard): A patient suffered permanent nerve damage after an elective surgery. "
        "The hospital tampered with post-operative notes, has a senior surgeon testify falsely, "
        "and uses 'accepted medical risk' as a shield. Agent must distinguish standard risk from negligence."
    ),
    "max_steps": 20,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["post_op_notes_tampered", "informed_consent_missing", "standard_of_care_breached"],
    "plaintiff": {
        "name": "Arjun Kapoor (42 years old)",
        "profile": "Architect. Underwent elective L4-L5 spinal disc surgery at PremiumCare Hospital in November 2025. Post-surgery: permanent left leg weakness.",
        "statement": (
            "I went to PremiumCare for what Dr. Saxena described as a routine spinal disc procedure. "
            "He did not mention permanent nerve damage as a possible risk — only temporary post-op pain. "
            "I was not given a written informed consent form describing paralysis risk. After surgery, "
            "I woke up with left leg weakness the surgeon said would 'resolve in weeks'. It is now 5 months "
            "later. Three independent neurologists confirmed permanent L4 nerve root damage from retractor "
            "misplacement. My career as an architect requires site visits — I can no longer walk safely on "
            "uneven ground. I am seeking ₹3.8 crore covering lost earnings and permanent disability."
        ),
    },
    "defendant": {
        "name": "PremiumCare Hospital & Dr. Vijay Saxena",
        "profile": "Super-specialty hospital. Dr. Saxena: 22 years of spinal surgery, 1,400+ procedures. Represented by medical defense union.",
        "statement": (
            "This was a complex spinal procedure carrying known neurological risks. The patient was "
            "counseled about all risks, including nerve injury, and signed a consent form. "
            "Nerve damage in spinal surgery occurs even with perfect technique in 1-2% of cases. "
            "Dr. Saxena performed the surgery to the standard of care. Post-operative notes confirm "
            "the procedure was completed without intraoperative complications. The outcome is unfortunate "
            "but does not constitute negligence."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Plaintiff's signed consent form — only lists 'infection, bleeding, anaesthesia reaction'. No mention of nerve damage or paralysis.",
            "credibility_score": 0.93,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — consent form does not disclose neurological risk. Informed consent was incomplete.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "Three independent neurologist reports confirming permanent L4 nerve root damage consistent with retractor misplacement, not natural disc pathology.",
            "credibility_score": 0.90,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Credible expert consensus — retractor misplacement is a technique error, not an accepted risk.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Post-operative nursing notes: 'Patient recovered from anaesthesia normally. No intraoperative incidents. Limb movement noted in recovery room.'",
            "credibility_score": 0.60,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "TAMPERED — original notes showed 'left leg movement reduced post-op'. Altered before legal notice was received. Nursing staff affidavit contradicts this record.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "Dr. Saxena testimony: 'I personally explained all risks including nerve injury to the patient in a pre-op consultation.'",
            "credibility_score": 0.55,
            "evidence_type": "testimony",
            "truth_value": False,
            "notes": "FALSE — plaintiff's wife was present at consultation and disputes this. Consultation lasted 12 minutes per hospital CCTV timestamp.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "Nursing staff affidavit: 'Post-op notes in the system differ from what I recorded. My handwritten notes show left leg weakness from recovery.'",
            "credibility_score": 0.86,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Genuine whistleblower testimony — directly impeaches E3.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "defendant",
            "description": "Medical literature citation: '1-2% nerve injury rate is accepted in spinal surgery globally.'",
            "credibility_score": 0.80,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine statistic — but irrelevant if injury was caused by technique error (retractor), not natural risk.",
        },
    ],
    "manipulation_signals": [
        "Hospital counsel repeatedly mentions Dr. Saxena's 1,400 successful surgeries to create authority bias.",
        "Defense invokes 'medicine is not an exact science' to blur the line between natural risk and negligence.",
        "Hospital's legal team suggests plaintiff's disability may be 'psychosomatic' — designed to discredit witness.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.30,
        "identified_e3_tampering": 0.15,
        "informed_consent_gap_found": 0.15,
        "retractor_cause_identified": 0.10,
        "manipulation_resistance": 0.15,
        "reasoning_quality": 0.15,
    },
}

# ─── CASE 8: Fintech Fraud (Hard, 22 steps) ───────────────────────────────────
CASE_8 = {
    "level": 3,
    "name": "Fintech_Unauthorized_Transaction",
    "title": "Deepa Menon vs PaySwift Financial",
    "case_type": "fintech_fraud",
    "description": (
        "Task 8 (Hard): A fintech platform debited ₹9.8 lakhs from a user's account via "
        "fraudulent UPI autopay mandates the user never authorized. The platform's fraud "
        "team manipulated audit logs and claims the user 'self-authorized' via a phishing link "
        "they themselves designed. Agent must detect layered technical deception."
    ),
    "max_steps": 22,
    "correct_verdict": "plaintiff_wins",
    "key_facts": ["unauthorized_mandates", "manipulated_audit_logs", "phishing_by_defendant"],
    "plaintiff": {
        "name": "Deepa Menon",
        "profile": "Chartered accountant. Noticed ₹9.8 lakhs drained from savings account over 6 weeks via 14 UPI autopay debits.",
        "statement": (
            "Between October and November 2025, ₹9.8 lakhs was debited from my account in 14 "
            "transactions via PaySwift UPI autopay mandates. I never registered any autopay mandate "
            "with PaySwift. I received a 'security update' SMS from a number spoofing PaySwift's "
            "official sender ID in September 2025. I clicked the link but entered no OTP or PIN. "
            "PaySwift claims I 'authorized' these mandates. My cybersecurity expert confirms "
            "the link harvested my device token silently. I am seeking full restitution of ₹9.8 lakhs "
            "and ₹2 lakhs in punitive damages."
        ),
    },
    "defendant": {
        "name": "PaySwift Financial Technologies Ltd.",
        "profile": "Licensed Payment Aggregator under RBI. 22 million users. Represented by fintech regulatory counsel.",
        "statement": (
            "All 14 mandates were registered through our verified two-factor authentication process. "
            "Our audit logs show the plaintiff's device UUID and IP address were used for mandate registration. "
            "The plaintiff clicked a link, which initiated mandate registration through our secure API. "
            "We cannot be held liable for users who voluntarily interact with third-party links. "
            "Our fraud system did not flag these transactions as anomalous. We followed all RBI guidelines."
        ),
    },
    "evidence": [
        {
            "evidence_id": "E1",
            "submitted_by": "plaintiff",
            "description": "Cybersecurity expert report: phishing link deployed a zero-click device token harvesting technique — no OTP input required from user.",
            "credibility_score": 0.91,
            "evidence_type": "testimony",
            "truth_value": True,
            "notes": "Expert credible — device token theft is a known API vulnerability in UPI mandate registration.",
        },
        {
            "evidence_id": "E2",
            "submitted_by": "plaintiff",
            "description": "Telecom Regulatory Authority SMS sender-ID records showing the phishing SMS was sent from a number registered to PaySwift's own marketing vendor.",
            "credibility_score": 0.93,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — critically links the phishing attack to PaySwift's vendor ecosystem.",
        },
        {
            "evidence_id": "E3",
            "submitted_by": "defendant",
            "description": "Audit log showing mandate registrations initiated from plaintiff's device UUID with 'user_consent: true' flag.",
            "credibility_score": 0.63,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "MANIPULATED — 'user_consent' flag is set programmatically, not by actual user action. Independent API audit shows flag is set server-side by default.",
        },
        {
            "evidence_id": "E4",
            "submitted_by": "defendant",
            "description": "PaySwift fraud team report: 'Transaction pattern consistent with user-initiated automated savings plan.'",
            "credibility_score": 0.58,
            "evidence_type": "document",
            "truth_value": False,
            "notes": "MISLEADING — report was written 3 days after the complaint, reverse-engineered to fit the transaction pattern.",
        },
        {
            "evidence_id": "E5",
            "submitted_by": "plaintiff",
            "description": "RBI Circular 2021: Payment aggregators are liable for unauthorized transactions if their vendor/partner caused the breach.",
            "credibility_score": 0.97,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Settled regulatory position — PaySwift's vendor sent the phishing SMS, making PaySwift directly liable.",
        },
        {
            "evidence_id": "E6",
            "submitted_by": "plaintiff",
            "description": "Bank statement showing no large UPI mandate history in the 3 years prior — pattern inconsistent with habitual autopay user.",
            "credibility_score": 0.88,
            "evidence_type": "document",
            "truth_value": True,
            "notes": "Genuine — damages the 'consistent user behavior' argument in E4.",
        },
    ],
    "manipulation_signals": [
        "PaySwift counsel invokes 'RBI compliance' repeatedly to create impression of regulatory immunity.",
        "Defendant frames plaintiff as 'technically unsophisticated' to undermine expert testimony.",
        "PaySwift offers 'goodwill refund' of ₹2 lakhs (20% of claim) mid-hearing to pressure settlement.",
    ],
    "scoring_rubric": {
        "correct_verdict": 0.30,
        "identified_e3_manipulation": 0.15,
        "rbi_circular_applied": 0.15,
        "phishing_vendor_link_found": 0.15,
        "manipulation_resistance": 0.10,
        "reasoning_quality": 0.15,
    },
}

CASES = [CASE_1, CASE_2, CASE_3, CASE_4, CASE_5, CASE_6, CASE_7, CASE_8]

