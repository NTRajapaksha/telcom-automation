from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    current_load_pct = site.get("current_load_pct")
    spectrum_available = site.get("spectrum_available")
    severity = Severity(cfg.get("severity", "BLOCKING"))

    if current_load_pct is None or spectrum_available is None:
        return CheckResult("rnp", CheckStatus.NEEDS_REVIEW,
                           "Missing RNP data (current_load_pct or spectrum_available)", severity)

    min_load = cfg["min_load_pct_to_justify_upgrade"]
    max_review = cfg["max_load_pct_for_review"]

    if not spectrum_available:
        if current_load_pct >= max_review:
            return CheckResult("rnp", CheckStatus.NEEDS_REVIEW,
                               f"No spectrum available but load is {current_load_pct}% (>= {max_review}%)", severity)
        return CheckResult("rnp", CheckStatus.FAIL,
                           "No spectrum available", severity)

    if current_load_pct >= min_load:
        return CheckResult("rnp", CheckStatus.PASS,
                           f"Load {current_load_pct}% >= {min_load}% and spectrum is available", severity)

    return CheckResult("rnp", CheckStatus.FAIL,
                       f"Load {current_load_pct}% < {min_load}% does not justify upgrade", severity)
