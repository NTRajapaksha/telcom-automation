from site_decision.models import Decision, CheckStatus, Severity, CheckResult
from site_decision.checks import CHECK_REGISTRY

def evaluate(site: dict, config: dict) -> Decision:
    site_type = site.get("site_type")
    check_names = config.get("site_types", {}).get(site_type, {}).get("checks", [])

    results = []
    for name in check_names:
        checker = CHECK_REGISTRY.get(name)
        if not checker:
            continue
        
        result = checker.run(site, config.get("checks", {}).get(name, {}))
        results.append(result)
        if result.status == CheckStatus.FAIL and result.severity == Severity.BLOCKING:
            break  # short-circuit: no point running further checks

    outcome, prereqs = _aggregate(results)
    return Decision(site.get("site_id"), outcome, results, prereqs)


def _aggregate(results: list[CheckResult]) -> tuple[str, list[str]]:
    if not results:
        # If no checks were run (e.g., unknown site_type), it needs review
        return "NEEDS_REVIEW", []

    if any(r.status == CheckStatus.FAIL and r.severity == Severity.BLOCKING for r in results):
        return "REJECTED", []
    if any(r.status == CheckStatus.NEEDS_REVIEW for r in results):
        return "NEEDS_REVIEW", []

    prereqs = [r.reason for r in results
               if r.status == CheckStatus.FAIL and r.severity == Severity.DEGRADING]
    return "APPROVED", prereqs
