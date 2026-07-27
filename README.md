# Telecom Site Capacity Upgrade Automation Engine

This repository contains a production-ready, configurable rules engine designed to automate telecom site capacity upgrade decision-making.

In standard telecom operations, when a mobile site (cell tower) requires additional capacity, engineers manually check several operational domains sequentially:
1. **Radio Network Planning (RNP):** Confirms traffic load justifies an upgrade and spectrum is available.
2. **Transmission (Backhaul):** Verifies if backhaul link bandwidth is sufficient.
3. **Power Supply:** Confirms site power supply headroom supports new hardware.
4. **Civil Works:** Evaluates space and physical footprint requirements for specific site types.

This software automates the evaluation of these checks, transforming manual spreadsheets and multi-team approvals into an automated decision engine.

---

## Key Design Principles & Architecture

The codebase is built around three fundamental design principles:

### 1. Separation of Pure Core Logic from I/O
The core evaluation engine (`site_decision.engine.evaluate`) is a pure function taking Python dictionaries as input (site payload and operator configuration) and returning a structured `Decision` object. It has zero network, database, or filesystem dependencies, making it seamlessly invocable via:
* **CLI Command Line Interface** (`site_decision.cli`)
* **REST API Service** (`site_decision.api`)
* **Automated Unit Tests** (`pytest tests/`)

### 2. Fully Config-Driven Pipeline (Multi-Tenant Ready)
Neither check thresholds (e.g., minimum load percentage or spare backhaul bandwidth) nor the list of checks applicable to a site type are hardcoded:
* **Per-Operator Rulesets:** Operator-specific thresholds and check pipelines are defined in YAML files (e.g., `site_decision/config/default_operator.yaml` and `site_decision/config/operator_b.yaml`).
* **Dynamic Site-Type Routing:** Sites of type `rooftop` execute `[rnp, transmission, power]`, while `greenfield` sites automatically execute `[rnp, transmission, power, civil_works]`.

### 3. Explicit Interdependence & Severity Model
Checks are not evaluated as simple independent booleans. Instead, checks carry explicitly defined severities:
* **`BLOCKING` Failure (e.g., RNP, Power):** Halts evaluation immediately (short-circuiting remaining checks) and returns a final decision outcome of **`REJECTED`**.
* **`DEGRADING` Failure (e.g., Transmission):** Allows execution to continue. If all other checks pass, the overall outcome returns **`APPROVED`**, with the transmission failure listed as a flagged **`prerequisite`** (e.g., `Transmission: Insufficient spare capacity`).
* **Missing Data / Borderline Conditions:** Missing payload fields or ambiguous threshold conditions evaluate to **`NEEDS_REVIEW`**, routing the request for human inspection rather than risking incorrect auto-approvals or hard rejections.

---

## Repository Structure

```text
telcom/
├── README.md                           # Complete project documentation
├── requirements.txt                    # Dependencies (FastAPI, Pydantic, PyYAML, pytest, httpx)
├── implementation-plan.md              # Architectural design document and build rationale
├── site_decision/                      # Core python package
│   ├── __init__.py
│   ├── models.py                       # CheckStatus, Severity, CheckResult, and Decision schemas
│   ├── engine.py                       # Rules engine & aggregation logic
│   ├── cli.py                          # Command line interface
│   ├── api.py                          # FastAPI service endpoints (/evaluate, /health)
│   ├── checks/                         # Pluggable check implementations
│   │   ├── __init__.py                 # CHECK_REGISTRY dictionary
│   │   ├── base.py                     # Checker module interface definition
│   │   ├── rnp.py                      # RNP load & spectrum check
│   │   ├── transmission.py             # Backhaul bandwidth check
│   │   ├── power.py                    # Power headroom check
│   │   └── civil_works.py              # Physical footprint check
│   └── config/                         # Operator YAML configurations
│       ├── default_operator.yaml       # Primary operator configuration
│       └── operator_b.yaml             # Secondary operator configuration (reusability proof)
└── tests/                              # Automated test suite
    ├── __init__.py
    ├── test_engine.py                  # Core engine unit tests (short-circuit, severities, configs)
    └── test_api.py                     # FastAPI integration tests
```

---

## Quick Start & Usage

### 1. Prerequisites & Installation

Ensure Python 3.10+ is installed on your system. Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

### 2. Running via Command Line Interface (CLI)

Create a sample JSON site payload file:

```json
{
  "site_id": "SITE-1042",
  "site_type": "rooftop",
  "current_load_pct": 92,
  "spectrum_available": true,
  "backhaul_capacity_mbps": 450,
  "backhaul_required_mbps": 600,
  "power_headroom_kw": 3.2,
  "power_required_kw": 2.8
}
```

Run the engine against an operator configuration:

```bash
python -m site_decision.cli --input sample.json --config site_decision/config/default_operator.yaml
```

**Sample JSON Output:**
```json
{
  "site_id": "SITE-1042",
  "outcome": "APPROVED",
  "check_results": [
    {
      "check_name": "rnp",
      "status": "PASS",
      "reason": "Load 92% >= 80% and spectrum is available",
      "severity": "BLOCKING"
    },
    {
      "check_name": "transmission",
      "status": "FAIL",
      "reason": "Transmission: Insufficient spare capacity (-25.0% < 10%)",
      "severity": "DEGRADING"
    },
    {
      "check_name": "power",
      "status": "PASS",
      "reason": "Power headroom 3.2kW >= 0.0kW",
      "severity": "BLOCKING"
    }
  ],
  "prerequisites": [
    "Transmission: Insufficient spare capacity (-25.0% < 10%)"
  ]
}
```

---

### 3. Running as a REST API Service

Start the FastAPI HTTP server using Uvicorn:

```bash
uvicorn site_decision.api:app --reload --port 8000
```

#### Health Check
```bash
curl http://localhost:8000/health
```
*Response:* `{"status": "ok"}`

#### Evaluate Site Endpoint
```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "SITE-1042",
    "site_type": "rooftop",
    "current_load_pct": 92,
    "spectrum_available": true,
    "backhaul_capacity_mbps": 450,
    "backhaul_required_mbps": 600,
    "power_headroom_kw": 3.2,
    "power_required_kw": 2.8
  }'
```

---

### 4. Running Automated Tests

Run the complete test suite using `pytest`:

```bash
pytest tests/
```

The unit test suite covers:
* **Short-Circuiting:** Verifies that an RNP `BLOCKING` failure halts execution immediately without checking transmission or power.
* **Degraded Approval:** Verifies that a Transmission failure results in `APPROVED` with a populated `prerequisites` list.
* **Missing Data:** Verifies that missing required fields return `NEEDS_REVIEW`.
* **Multi-Operator Swapping:** Evaluates the exact same payload against two different YAML configs to prove rule reusability.
* **Forward Compatibility:** Asserts that unknown/new payload attributes are passed through gracefully without errors.
* **API Equivalence:** Confirms HTTP `/evaluate` endpoint returns identical output to direct engine calls.

---

## Documented Assumptions & Decision Rationale

1. **Missing / Absent Fields → `NEEDS_REVIEW`**
   * Absent fields are interpreted as data that hasn't arrived or requires manual verification, rather than an automatic `FAIL` or `PASS`. If a check encounters missing required fields (e.g., `power_headroom_kw: null`), it outputs `CheckStatus.NEEDS_REVIEW`.
2. **Short-Circuit vs. Continued Execution**
   * `BLOCKING` check failures halt execution immediately. Running subsequent checks after a hard block is redundant and could generate misleading error reports for a site that was already rejected.
   * `DEGRADING` failures do not halt execution, allowing the system to gather all necessary prerequisites before issuing an upgrade authorization.
3. **Forward-Compatible Schema (`extra="allow"`)**
   * Payload inputs use `extra="allow"` in Pydantic. Future telecom field additions ride along in the dictionary without breaking existing evaluations.

---

## Production Recommendations & Future Improvements

If expanding this service for high-volume enterprise production use, the following enhancements are recommended:

* **Strict Config Validation:** Implement schema validation (using Pydantic or JSON Schema) for YAML configuration files at startup to detect missing or mistyped thresholds before receiving requests.
* **Multi-Tenant Dynamic Routing:** Extend the REST API to load configurations dynamically based on request headers (e.g., `X-Operator-ID`) or database-backed configuration stores.
* **Structured Audit Logging:** Emit JSON audit logs containing `site_id`, decision `outcome`, ruleset version, timestamp, and evaluation execution time for regulatory tracking.
* **Idempotency Control:** Include idempotency keys on evaluation calls to prevent accidental duplicate upgrade work orders downstream.
