from typing import Protocol
from site_decision.models import CheckResult

class Checker(Protocol):
    def run(self, site: dict, cfg: dict) -> CheckResult:
        ...
