from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    headroom = site.get("power_headroom_kw")
    required = site.get("power_required_kw")
    severity = Severity(cfg.get("severity", "BLOCKING"))

    if headroom is None:
        return CheckResult("power", CheckStatus.NEEDS_REVIEW,
                           "Missing power_headroom_kw data", severity)

    min_headroom = cfg.get("min_headroom_kw", 0.0)
    target_required = required if required is not None else min_headroom

    if headroom >= target_required and headroom >= min_headroom:
        reason_msg = (f"Power headroom {headroom}kW >= {target_required}kW required"
                      if required is not None else f"Power headroom {headroom}kW >= {min_headroom}kW")
        return CheckResult("power", CheckStatus.PASS, reason_msg, severity)

    return CheckResult("power", CheckStatus.FAIL,
                       f"Insufficient power headroom ({headroom}kW < {target_required}kW required)", severity)
