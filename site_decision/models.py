from dataclasses import dataclass, field
from enum import Enum

class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class Severity(str, Enum):
    BLOCKING = "BLOCKING"       # a FAIL here stops the process -> REJECTED
    DEGRADING = "DEGRADING"     # a FAIL here can continue with a flagged prerequisite

@dataclass
class CheckResult:
    check_name: str
    status: CheckStatus
    reason: str
    severity: Severity

@dataclass
class Decision:
    site_id: str
    outcome: str                     # APPROVED | REJECTED | NEEDS_REVIEW
    check_results: list[CheckResult]
    prerequisites: list[str] = field(default_factory=list)
