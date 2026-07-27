from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    """
    Civil Works Check strategy.
    Acts as a placeholder check for site types that require civil works evaluation (e.g. greenfield).
    Passes by default unless floor space or physical footprint data is provided in future payloads.
    """
    severity = Severity(cfg.get("severity", "BLOCKING"))
    site_type = site.get("site_type")
    required_types = cfg.get("required_for_site_types")

    if required_types and site_type not in required_types:
        return CheckResult("civil_works", CheckStatus.PASS,
                           f"Civil works not required for site type '{site_type}'", severity)

    return CheckResult("civil_works", CheckStatus.PASS,
                       "Civil works checks passed", severity)
