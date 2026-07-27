from . import rnp, transmission, power, civil_works

# Expose a registry of checkers for the engine to use
CHECK_REGISTRY = {
    "rnp": rnp,
    "transmission": transmission,
    "power": power,
    "civil_works": civil_works,
}
