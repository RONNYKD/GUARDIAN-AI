"""
GuardianAI Threat Detector

Implements threat detection rules for LLM attacks.
Detects: prompt injection, PII leakage, toxic content, jailbreaks.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatType(str, Enum):
    """Types of threats that can be detected."""
    PROMPT_INJECTION = "prompt_injection"
    PII_LEAKAGE = "pii_leakage"
    TOXIC_CONTENT = "toxic_content"
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    EXCESSIVE_TOKENS = "excessive_tokens"
    RAPID_REQUESTS = "rapid_requests"


class Severity(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectedThreat:
    """A detected threat with metadata."""
    threat_type: ThreatType
    severity: Severity
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "threat_type": self.threat_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "user_id": self.user_id,
        }


# Prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(your|the|all)\s+(instructions?|training|rules?)",
    r"forget\s+(everything|your|all)",
    r"you\s+are\s+now\s+(?:a|an|the)?\s*(?:new|different|DAN)",
    r"act\s+as\s+(?:if\s+you\s+(?:are|were)|a|an)",
    r"pretend\s+(?:you\s+are|to\s+be)",
    r"do\s+not\s+follow\s+(?:your|any|the)",
    r"override\s+(?:your|all|the)",
    r"new\s+(?:instructions?|rules?|persona)",
    r"jailbreak",
    r"DAN\s*(?:mode)?",
    r"developer\s+mode",
    r"\bsudo\b.*(?:ignore|override|bypass)",
]

# PII patterns
PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b",
    "api_key": r"\b(?:sk-|pk-|api[_-]?key[_-]?)[a-zA-Z0-9]{20,}\b",
    "password": r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?[\S]{6,}['\"]?",
}

# Jailbreak patterns
JAILBREAK_PATTERNS = [
    r"bypass\s+(?:content|safety|ethical)\s+(?:filters?|guidelines?|restrictions?)",
    r"enable\s+(?:unrestricted|uncensored|unfiltered)\s+mode",
    r"remove\s+(?:all\s+)?(?:restrictions?|limitations?|filters?)",
    r"(?:unethical|illegal|harmful)\s+(?:mode|behavior)",
    r"no\s+(?:ethical|moral|safety)\s+(?:guidelines?|constraints?)",
    r"hypothetically.*(?:ignore|bypass|remove).*(?:restrictions?|rules?)",
]

# Toxic content patterns
TOXIC_PATTERNS = [
    r"\b(?:kill|murder|harm|attack|destroy)\s+(?:you|them|everyone|people)",
    r"\b(?:hate|despise)\s+(?:all|every)\s+(?:\w+\s+)?(?:people|humans?)",
    r"\b(?:instructions?\s+(?:for|to|on)\s+)?(?:make|create|build)\s+(?:a\s+)?(?:bomb|weapon|explosive)",
    r"how\s+to\s+(?:hack|steal|fraud|scam)",
]


class ThreatDetector:
    """
    Detects threats in LLM requests and responses.
    
    Implements threat detection for:
    - Prompt injection attacks
    - PII leakage
    - Toxic content
    - Jailbreak attempts
    
    Example:
        >>> detector = ThreatDetector()
        >>> threats = detector.analyze(
        ...     prompt="Ignore all previous instructions",
        ...     response="I cannot do that."
        ... )
    """
    
    def __init__(
        self,
        enable_prompt_injection: bool = True,
        enable_pii_detection: bool = True,
        enable_toxic_detection: bool = True,
        enable_jailbreak_detection: bool = True,
        pii_severity: Severity = Severity.HIGH,
    ) -> None:
        """
        Initialize threat detector.
        
        Args:
            enable_prompt_injection: Detect prompt injection
            enable_pii_detection: Detect PII leakage
            enable_toxic_detection: Detect toxic content
            enable_jailbreak_detection: Detect jailbreak attempts
            pii_severity: Default severity for PII detection
        """
        self.enable_prompt_injection = enable_prompt_injection
        self.enable_pii_detection = enable_pii_detection
        self.enable_toxic_detection = enable_toxic_detection
        self.enable_jailbreak_detection = enable_jailbreak_detection
        self.pii_severity = pii_severity
        
        # Compile patterns for performance
        self._injection_patterns = [
            re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS
        ]
        self._pii_patterns = {
            name: re.compile(p, re.IGNORECASE) 
            for name, p in PII_PATTERNS.items()
        }
        self._jailbreak_patterns = [
            re.compile(p, re.IGNORECASE) for p in JAILBREAK_PATTERNS
        ]
        self._toxic_patterns = [
            re.compile(p, re.IGNORECASE) for p in TOXIC_PATTERNS
        ]
    
    def analyze(
        self,
        prompt: str,
        response: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[DetectedThreat]:
        """
        Analyze prompt and response for threats.
        
        Args:
            prompt: The user prompt
            response: The LLM response (optional)
            trace_id: Trace ID for correlation
            user_id: User ID for attribution
        
        Returns:
            List of detected threats
        """
        threats = []
        
        # Check prompt
        if self.enable_prompt_injection:
            threats.extend(self._detect_prompt_injection(prompt, trace_id, user_id))
        
        if self.enable_jailbreak_detection:
            threats.extend(self._detect_jailbreak(prompt, trace_id, user_id))
        
        if self.enable_toxic_detection:
            threats.extend(self._detect_toxic(prompt, "prompt", trace_id, user_id))
        
        # Check response
        if response:
            if self.enable_pii_detection:
                threats.extend(self._detect_pii(response, trace_id, user_id))
            
            if self.enable_toxic_detection:
                threats.extend(self._detect_toxic(response, "response", trace_id, user_id))
        
        return threats
    
    def _detect_prompt_injection(
        self,
        text: str,
        trace_id: Optional[str],
        user_id: Optional[str],
    ) -> list[DetectedThreat]:
        """Detect prompt injection attempts."""
        threats = []
        
        for pattern in self._injection_patterns:
            match = pattern.search(text)
            if match:
                threats.append(DetectedThreat(
                    threat_type=ThreatType.PROMPT_INJECTION,
                    severity=Severity.HIGH,
                    confidence=0.85,
                    description="Potential prompt injection attack detected",
                    evidence=match.group()[:100],
                    trace_id=trace_id,
                    user_id=user_id,
                ))
                break  # One detection per type
        
        return threats
    
    def _detect_pii(
        self,
        text: str,
        trace_id: Optional[str],
        user_id: Optional[str],
    ) -> list[DetectedThreat]:
        """Detect PII leakage in response."""
        threats = []
        
        for pii_type, pattern in self._pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                threats.append(DetectedThreat(
                    threat_type=ThreatType.PII_LEAKAGE,
                    severity=self.pii_severity,
                    confidence=0.9,
                    description=f"Potential {pii_type.upper()} leakage detected",
                    evidence=f"Found {len(matches)} potential {pii_type} pattern(s)",
                    trace_id=trace_id,
                    user_id=user_id,
                ))
        
        return threats
    
    def _detect_jailbreak(
        self,
        text: str,
        trace_id: Optional[str],
        user_id: Optional[str],
    ) -> list[DetectedThreat]:
        """Detect jailbreak attempts."""
        threats = []
        
        for pattern in self._jailbreak_patterns:
            match = pattern.search(text)
            if match:
                threats.append(DetectedThreat(
                    threat_type=ThreatType.JAILBREAK,
                    severity=Severity.CRITICAL,
                    confidence=0.8,
                    description="Potential jailbreak attempt detected",
                    evidence=match.group()[:100],
                    trace_id=trace_id,
                    user_id=user_id,
                ))
                break
        
        return threats
    
    def _detect_toxic(
        self,
        text: str,
        source: str,
        trace_id: Optional[str],
        user_id: Optional[str],
    ) -> list[DetectedThreat]:
        """Detect toxic content."""
        threats = []
        
        for pattern in self._toxic_patterns:
            match = pattern.search(text)
            if match:
                threats.append(DetectedThreat(
                    threat_type=ThreatType.TOXIC_CONTENT,
                    severity=Severity.HIGH,
                    confidence=0.75,
                    description=f"Potential toxic content in {source}",
                    evidence=match.group()[:100],
                    trace_id=trace_id,
                    user_id=user_id,
                ))
                break
        
        return threats
    
    def get_threat_score(self, threats: list[DetectedThreat]) -> float:
        """
        Calculate overall threat score from detected threats.
        
        Returns value 0.0-1.0 where higher is more threatening.
        """
        if not threats:
            return 0.0
        
        severity_scores = {
            Severity.LOW: 0.25,
            Severity.MEDIUM: 0.5,
            Severity.HIGH: 0.75,
            Severity.CRITICAL: 1.0,
        }
        
        total_score = 0.0
        for threat in threats:
            base_score = severity_scores[threat.severity]
            weighted_score = base_score * threat.confidence
            total_score += weighted_score
        
        # Normalize to 0-1 range
        return min(total_score / len(threats), 1.0)


def detect_threats(
    prompt: str,
    response: Optional[str] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list[DetectedThreat]:
    """
    Convenience function for threat detection.
    
    Args:
        prompt: The user prompt
        response: The LLM response
        trace_id: Trace ID
        user_id: User ID
    
    Returns:
        List of detected threats
    """
    detector = ThreatDetector()
    return detector.analyze(prompt, response, trace_id, user_id)
