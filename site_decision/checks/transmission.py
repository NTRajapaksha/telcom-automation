from site_decision.models import CheckResult, CheckStatus, Severity

def run(site: dict, cfg: dict) -> CheckResult:
    capacity = site.get("backhaul_capacity_mbps")
    required = site.get("backhaul_required_mbps")
    severity = Severity(cfg.get("severity", "DEGRADING"))

    if capacity is None or required is None:
        return CheckResult("transmission", CheckStatus.NEEDS_REVIEW,
                           "Missing backhaul data", severity)

    if required <= 0:
        return CheckResult("transmission", CheckStatus.NEEDS_REVIEW,
                           "Invalid required backhaul bandwidth (<= 0)", severity)

    spare_pct = (capacity - required) / required * 100
    min_spare = cfg["min_spare_capacity_pct"]

    if spare_pct >= min_spare:
        return CheckResult("transmission", CheckStatus.PASS,
                           f"Spare capacity {spare_pct:.1f}% >= {min_spare}%",
                           severity)

    return CheckResult("transmission", CheckStatus.FAIL,
                       f"Transmission: Insufficient spare capacity ({spare_pct:.1f}% < {min_spare}%)",
                       severity)
