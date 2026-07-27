import argparse
import json
import yaml
from site_decision.engine import evaluate
from site_decision.models import Decision

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'value'):
            return obj.value
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def main():
    parser = argparse.ArgumentParser(description="Evaluate site capacity upgrade.")
    parser.add_argument("--input", required=True, help="Path to site data JSON file")
    parser.add_argument("--config", required=True, help="Path to operator config YAML file")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        site = json.load(f)
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    decision = evaluate(site, config)
    print(json.dumps(decision, cls=CustomEncoder, indent=2))

if __name__ == "__main__":
    main()
