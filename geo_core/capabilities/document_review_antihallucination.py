"""
Document Review Anti-Hallucination Module
=========================================

CRITICAL MODULE: Prevents hallucination when reviewing scientific documents.

The Problem (demonstrated in geochem_doc review incident):
- LLMs can hallucinate details about papers they haven't fully read
- Claims about observations, sample sizes, instruments can be invented
- Specific numbers (isotopic values, sample sizes) are particularly prone to error
- This severely damages credibility and trust

The Solution:
1. MANDATORY source document verification before any factual claim
2. Explicit claim extraction and verification against source text
3. Numerical data must be directly quoted from source
4. Instrument names must match source exactly
5. Sample sizes must be verified against source
6. Anti-hallucination table in all review reports

Key Rules:
- NEVER claim an isotopic value unless explicitly stated in source
- NEVER claim sample sizes unless verified in source
- NEVER claim instrument details unless stated in source
- ALWAYS provide verification trail for numerical claims

Date: 2026-03-24
Version: 1.0.0
Motivation: geochem_doc review incident (δ¹³C = -28‰, 29 chert nodules, 12 SIMS spots - all WRONG)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re
import hashlib


class ClaimCategory(Enum):
    """Category of document review claim."""
    OBSERVATION_FREQUENCY = "observation_frequency"
    SAMPLE_SIZE = "sample_size"
    INSTRUMENT_NAME = "instrument_name"
    AUTHOR_INFO = "author_info"
    KEY_FINDING = "key_finding"
    NUMERICAL_RESULT = "numerical_result"
    METHODOLOGY = "methodology"
    REFERENCE = "reference"


class VerificationStatus(Enum):
    """Status of claim verification."""
    VERIFIED_IN_SOURCE = "verified_in_source"  # Direct match in source document
    DERIVED_FROM_SOURCE = "derived_from_source"  # Logically derived from source
    NOT_FOUND_IN_SOURCE = "not_found_in_source"  # Could not verify in source
    CONTRADICTS_SOURCE = "contradicts_source"  # Contradicts source document
    HALLUCINATED = "hallucinated"  # Known to be false


@dataclass
class DocumentClaim:
    """A claim made about a document that needs verification."""
    claim_type: ClaimCategory
    claim_text: str
    claimed_value: Any  # The value claimed (e.g., -28.0, 29, "SIMS")
    source_text: Optional[str] = None  # Text from source document
    source_location: Optional[str] = None  # Where in source (section, page, line)
    verification_status: VerificationStatus = VerificationStatus.NOT_FOUND_IN_SOURCE
    actual_value: Optional[Any] = None  # Correct value if different from claimed
    notes: List[str] = field(default_factory=list)


@dataclass
class DocumentReviewVerification:
    """Complete verification report for a document review."""
    document_title: str
    document_path: str
    claims_verified: int = 0
    claims_not_found: int = 0
    claims_contradicted: int = 0
    claims_hallucinated: int = 0
    total_claims: int = 0
    verification_table: List[DocumentClaim] = field(default_factory=list)
    safe_to_publish: bool = True
    hallucination_incidents: List[str] = field(default_factory=list)

    def get_verification_table_markdown(self) -> str:
        """Generate markdown verification table."""
        lines = ["| Claim in Report | Source Verification | Status |"]
        lines.append("|-----------------|---------------------|--------|")
        for claim in self.verification_table:
            status_emoji = {
                VerificationStatus.VERIFIED_IN_SOURCE: "VERIFIED",
                VerificationStatus.DERIVED_FROM_SOURCE: "DERIVED",
                VerificationStatus.NOT_FOUND_IN_SOURCE: "NOT FOUND",
                VerificationStatus.CONTRADICTS_SOURCE: "CONTRADICTS",
                VerificationStatus.HALLUCINATED: "HALLUCINATED"
            }.get(claim.verification_status, "UNKNOWN")
            source = claim.source_text or "Not found in source"
            if len(source) > 50:
                source = source[:47] + "..."
            lines.append(f"| {claim.claim_text[:40]} | {source[:40]} | {status_emoji} |")
        return "\n".join(lines)


class DocumentReviewAntiHallucination:
    """
    Anti-hallucination system specifically for document review tasks.

    CRITICAL: This must be used for ALL document review tasks to prevent
    the kind of errors seen in the geochem_doc review incident.

    Usage:
        verifier = DocumentReviewAntiHallucination(source_text)
        verifier.verify_frequency_claim("δ¹³C = -28‰", claimed_value=-28.0)
        verifier.verify_sample_size_claim("29 chert nodules", claimed_value=29)
        report = verifier.generate_report()
    """

    # Known hallucination patterns to check for
    HALLUCINATION_PATTERNS = {
        # Pattern: (regex_pattern, typical_hallucinated_value, common_correct_values)
        "sims_d13c_value": (
            r"-?28\s*[‰]",
            -28.0,
            [-25.0, -30.0, -28.0]  # Common δ¹³C_org values
        ),
        "small_sample_detection": (
            r"(\d+)\s*(?:chert\s+nodules|samples?|specimens?|formations?)\s+(?:detected|analyzed)",
            None,  # Variable
            None
        ),
    }

    def __init__(self, source_document_text: str = "", source_document_path: str = ""):
        """
        Initialize anti-hallucination verifier.

        Args:
            source_document_text: Full text of the source document being reviewed
            source_document_path: Path to the source document
        """
        self.source_text = source_document_text
        self.source_path = source_document_path
        self.claims: List[DocumentClaim] = []
        self.extractions: Dict[str, Any] = {}

        # Extract key information from source
        if source_document_text:
            self._extract_key_information()

    def _extract_key_information(self):
        """Extract key factual information from source document."""
        text = self.source_text.lower()

        # Extract measurement values (isotopic values, concentrations)
        measurement_patterns = [
            r'd1?3c[^a-z]*?(-?\d+(?:\.\d+)?)\s*[‰]',
            r'd34s[^a-z]*?(-?\d+(?:\.\d+)?)\s*[‰]',
            r'toc[^a-z]*?(\d+(?:\.\d+)?)\s*(?:wt%|wt\s*%)',
        ]
        measurements = []
        for pattern in measurement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            measurements.extend([float(m) for m in matches])
        self.extractions['measurement_values'] = list(set(measurements))

        # Extract sample sizes
        sample_patterns = [
            r'(\d+)\s*(?:chert\s+nodules|samples?|specimens?|formations?|beds?)',
            r'sample\s+of\s+(\d+)',
            r'(\d+)\s*(?:were\s+)?analyzed',
        ]
        sample_sizes = []
        for pattern in sample_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sample_sizes.extend([int(m) for m in matches])
        self.extractions['sample_sizes'] = list(set(sample_sizes))

        # Extract instrument/survey names
        instrument_patterns = [
            r'(sims|icp-ms|xrd|sem|tem|ea-irms|gc-ms|ftir|raman)',
            r'(secondary\s+ion\s+mass\s+spectrom)',
        ]
        instruments = []
        for pattern in instrument_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            instruments.extend([m.upper() for m in matches])
        self.extractions['instruments'] = list(set(instruments))

        # Extract author information
        author_match = re.search(r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and)\s+)?)', self.source_text[:500])
        if author_match:
            self.extractions['first_author'] = author_match.group(1).strip()

    def verify_frequency_claim(self, claim_description: str, claimed_value: float,
                                unit: str = "‰") -> DocumentClaim:
        """
        Verify a measurement value claim against the source document.

        Args:
            claim_description: Description of the claim (e.g., "δ¹³C = -28‰")
            claimed_value: The measurement value claimed
            unit: Unit of measurement (‰, wt%, ppm, etc.)

        Returns:
            DocumentClaim with verification status
        """
        claim = DocumentClaim(
            claim_type=ClaimCategory.OBSERVATION_FREQUENCY,
            claim_text=f"{claim_description} ({claimed_value} {unit})",
            claimed_value=claimed_value
        )

        # Check if value appears in extracted measurements
        values = self.extractions.get('measurement_values', [])

        # Check for exact or near match
        for val in values:
            if abs(val - claimed_value) < 1:  # Within 1 unit
                claim.verification_status = VerificationStatus.VERIFIED_IN_SOURCE
                claim.source_text = f"Found {val} {unit} in source"
                self.claims.append(claim)
                return claim

        # Not found - check if source mentions different value
        if values:
            claim.verification_status = VerificationStatus.CONTRADICTS_SOURCE
            claim.actual_value = values
            claim.notes.append(f"Source mentions values: {values}, not {claimed_value} {unit}")
        else:
            claim.verification_status = VerificationStatus.NOT_FOUND_IN_SOURCE
            claim.notes.append(f"Could not find value {claimed_value} {unit} in source")

        self.claims.append(claim)
        return claim

    def verify_sample_size_claim(self, claim_description: str, claimed_value: int) -> DocumentClaim:
        """
        Verify a sample size claim against the source document.

        Args:
            claim_description: Description (e.g., "29 chert nodules analyzed")
            claimed_value: The sample size claimed

        Returns:
            DocumentClaim with verification status
        """
        claim = DocumentClaim(
            claim_type=ClaimCategory.SAMPLE_SIZE,
            claim_text=f"{claim_description} (n={claimed_value})",
            claimed_value=claimed_value
        )

        # Check if sample size appears in extracted values
        sizes = self.extractions.get('sample_sizes', [])

        if claimed_value in sizes:
            claim.verification_status = VerificationStatus.VERIFIED_IN_SOURCE
            claim.source_text = f"Found sample size {claimed_value} in source"
        elif sizes:
            # Check for close match
            for size in sizes:
                if abs(size - claimed_value) <= 2:
                    claim.verification_status = VerificationStatus.DERIVED_FROM_SOURCE
                    claim.source_text = f"Found similar value {size} in source"
                    break
            else:
                claim.verification_status = VerificationStatus.CONTRADICTS_SOURCE
                claim.actual_value = sizes
                claim.notes.append(f"Source mentions sample sizes: {sizes}, not {claimed_value}")
        else:
            claim.verification_status = VerificationStatus.NOT_FOUND_IN_SOURCE
            claim.notes.append(f"Could not find sample size {claimed_value} in source")

        self.claims.append(claim)
        return claim

    def verify_instrument_claim(self, claim_description: str, claimed_instrument: str) -> DocumentClaim:
        """
        Verify an instrument/survey claim.

        Args:
            claim_description: Description (e.g., "SIMS spot analyses")
            claimed_instrument: The instrument name claimed

        Returns:
            DocumentClaim with verification status
        """
        claim = DocumentClaim(
            claim_type=ClaimCategory.INSTRUMENT_NAME,
            claim_text=f"{claim_description}",
            claimed_value=claimed_instrument
        )

        instruments = self.extractions.get('instruments', [])
        claimed_upper = claimed_instrument.upper()

        # Check for exact match
        if claimed_upper in instruments:
            claim.verification_status = VerificationStatus.VERIFIED_IN_SOURCE
            claim.source_text = f"Found {claimed_instrument} in source"
        else:
            # Check for partial match
            found_partial = False
            for inst in instruments:
                if claimed_upper in inst or inst in claimed_upper:
                    claim.verification_status = VerificationStatus.DERIVED_FROM_SOURCE
                    claim.source_text = f"Found related instrument {inst} in source"
                    found_partial = True
                    break

            if not found_partial:
                claim.verification_status = VerificationStatus.CONTRADICTS_SOURCE
                claim.actual_value = instruments
                claim.notes.append(f"Source mentions instruments: {instruments}, not {claimed_instrument}")

        self.claims.append(claim)
        return claim

    def verify_general_claim(self, claim_text: str, expected_in_source: str) -> DocumentClaim:
        """
        Verify a general claim by searching for expected text in source.

        Args:
            claim_text: The claim being made
            expected_in_source: Text expected to appear in source if claim is true

        Returns:
            DocumentClaim with verification status
        """
        claim = DocumentClaim(
            claim_type=ClaimCategory.KEY_FINDING,
            claim_text=claim_text,
            claimed_value=expected_in_source
        )

        if not self.source_text:
            claim.verification_status = VerificationStatus.NOT_FOUND_IN_SOURCE
            self.claims.append(claim)
            return claim

        # Search for expected text in source
        if expected_in_source.lower() in self.source_text.lower():
            claim.verification_status = VerificationStatus.VERIFIED_IN_SOURCE
            # Find the actual occurrence
            idx = self.source_text.lower().find(expected_in_source.lower())
            context_start = max(0, idx - 50)
            context_end = min(len(self.source_text), idx + len(expected_in_source) + 50)
            claim.source_text = f"...{self.source_text[context_start:context_end]}..."
        else:
            claim.verification_status = VerificationStatus.NOT_FOUND_IN_SOURCE
            claim.notes.append(f"Expected text '{expected_in_source}' not found in source")

        self.claims.append(claim)
        return claim

    def generate_report(self, document_title: str = "Unknown Document") -> DocumentReviewVerification:
        """
        Generate complete verification report.

        Args:
            document_title: Title of the reviewed document

        Returns:
            DocumentReviewVerification with full report
        """
        report = DocumentReviewVerification(
            document_title=document_title,
            document_path=self.source_path,
            total_claims=len(self.claims),
            verification_table=self.claims
        )

        for claim in self.claims:
            if claim.verification_status == VerificationStatus.VERIFIED_IN_SOURCE:
                report.claims_verified += 1
            elif claim.verification_status == VerificationStatus.NOT_FOUND_IN_SOURCE:
                report.claims_not_found += 1
            elif claim.verification_status == VerificationStatus.CONTRADICTS_SOURCE:
                report.claims_contradicted += 1
                report.hallucination_incidents.append(
                    f"Claim '{claim.claim_text}' contradicts source. "
                    f"Source shows: {claim.actual_value}"
                )
            elif claim.verification_status == VerificationStatus.HALLUCINATED:
                report.claims_hallucinated += 1
                report.hallucination_incidents.append(
                    f"HALLUCINATION: '{claim.claim_text}' is false"
                )

        # Determine if safe to publish
        report.safe_to_publish = (
            report.claims_contradicted == 0 and
            report.claims_hallucinated == 0
        )

        return report

    def get_anti_hallucination_section(self, document_title: str = "Unknown") -> str:
        """
        Generate the anti-hallucination verification section for a review.

        This should be included at the TOP of any review report.
        """
        report = self.generate_report(document_title)

        lines = [
            "## Anti-Hallucination Verification",
            "",
            "This report has been generated with explicit verification against the source document.",
            "The following factual claims have been verified:",
            "",
            report.get_verification_table_markdown(),
            "",
            f"**Verification Summary**: {report.claims_verified}/{report.total_claims} claims verified",
        ]

        if report.hallucination_incidents:
            lines.append("")
            lines.append("**HALLUCINATION INCIDENTS DETECTED**:")
            for incident in report.hallucination_incidents:
                lines.append(f"- {incident}")

        if not report.safe_to_publish:
            lines.append("")
            lines.append("**WARNING**: This report contains claims that contradict the source document.")
            lines.append("DO NOT PUBLISH without correction.")

        return "\n".join(lines)


# Convenience functions

def verify_document_review(source_text: str, claims: List[Dict]) -> DocumentReviewVerification:
    """
    Verify multiple claims about a document.

    Args:
        source_text: Full text of source document
        claims: List of claim dictionaries with keys:
                - 'type': 'frequency', 'sample_size', 'instrument', or 'general'
                - 'description': Claim description
                - 'value': Claimed value

    Returns:
        DocumentReviewVerification report
    """
    verifier = DocumentReviewAntiHallucination(source_text)

    for claim in claims:
        claim_type = claim.get('type', 'general')
        description = claim.get('description', '')
        value = claim.get('value')

        if claim_type == 'frequency':
            verifier.verify_frequency_claim(description, value)
        elif claim_type == 'sample_size':
            verifier.verify_sample_size_claim(description, value)
        elif claim_type == 'instrument':
            verifier.verify_instrument_claim(description, value)
        else:
            verifier.verify_general_claim(description, str(value))

    return verifier.generate_report()


def register_known_hallucination(claim: str, correct_value: Any, category: str = "document_review"):
    """
    Register a known hallucination for future reference.

    This should be called when a hallucination is detected to prevent
    future repetition.

    Args:
        claim: The hallucinated claim
        correct_value: The correct value
        category: Category of hallucination
    """
    hallucination_entry = {
        'claim': claim,
        'correct_value': correct_value,
        'category': category,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }

    # Log to hallucination register
    register_path = Path(__file__).parent / ".hallucination_register.json"
    try:
        if register_path.exists():
            with open(register_path, 'r') as f:
                register = __import__('json').load(f)
        else:
            register = {'hallucinations': []}

        register['hallucinations'].append(hallucination_entry)

        with open(register_path, 'w') as f:
            __import__('json').dump(register, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save hallucination register: {e}")


# Register the geochem_doc incident as a known hallucination
GEOCHEM_DOCUMENT_HALLUCINATIONS = [
    {
        'claim': 'δ¹³C = -28‰ for Proterozoic chert nodules',
        'correct_value': 'δ¹³C = -25‰ (EA-IRMS)',
        'category': 'observation_frequency',
        'notes': 'The paper reports δ¹³C_org = -25‰ via EA-IRMS, not -28‰'
    },
    {
        'claim': '29 chert nodules analyzed with 12 SIMS spots',
        'correct_value': '198 chert nodules analyzed, 61 with isotopic data',
        'category': 'sample_size',
        'notes': 'The paper analyzed 198 chert nodules across 3 formations'
    },
    {
        'claim': 'SIMS spot analyses',
        'correct_value': 'EA-IRMS bulk analyses',
        'category': 'instrument',
        'notes': 'The study used bulk EA-IRMS, not in-situ SIMS spot analyses'
    }
]


__all__ = [
    'DocumentReviewAntiHallucination',
    'DocumentReviewVerification',
    'DocumentClaim',
    'ClaimCategory',
    'VerificationStatus',
    'verify_document_review',
    'register_known_hallucination',
    'GEOCHEM_DOCUMENT_HALLUCINATIONS'
]
