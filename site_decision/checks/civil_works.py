from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    severity = Severity(cfg.get("severity", "BLOCKING"))
    # The engine only runs this if it's configured for the site_type.
    # We could check civil works specifics here if there were fields in the payload.
    # For now, it passes by default unless data indicates otherwise.
    
    return CheckResult("civil_works", CheckStatus.PASS,
                       "Civil works checks passed (no specific requirements)", severity)
