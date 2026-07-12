"""
CLI entrypoint to run a RAGAS evaluation without going through the API.
Usage: python -m eval.run_evaluation
"""
import json
from app.services.evaluation import run_ragas_evaluation

if __name__ == "__main__":
    result = run_ragas_evaluation()
    print(json.dumps(result["scores"], indent=2))
