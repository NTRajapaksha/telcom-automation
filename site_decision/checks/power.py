from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    headroom = site.get("power_headroom_kw")
    severity = Severity(cfg.get("severity", "BLOCKING"))

    if headroom is None:
        return CheckResult("power", CheckStatus.NEEDS_REVIEW,
                           "Missing power_headroom_kw data", severity)

    min_headroom = cfg["min_headroom_kw"]

    if headroom >= min_headroom:
        return CheckResult("power", CheckStatus.PASS,
                           f"Power headroom {headroom}kW >= {min_headroom}kW", severity)

    return CheckResult("power", CheckStatus.FAIL,
                       f"Insufficient power headroom ({headroom}kW < {min_headroom}kW)", severity)
