"""
RAGAS evaluation service. Measures RAG pipeline quality using:
  - faithfulness: is the answer grounded in the retrieved context?
  - answer_relevancy: does the answer actually address the question?
  - context_precision: are the retrieved chunks relevant to the question?
  - context_recall: did retrieval surface what was needed (needs ground_truth)?

Uses Groq (via langchain-groq) as the judge LLM and the same local embedding
model used for retrieval, so no extra paid API (e.g. OpenAI) is required.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

from datasets import Dataset
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

from app.core.config import get_settings
from app.core.logging_config import logger
from app.services.rag_pipeline import answer_question

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "eval" / "test_dataset.json"


def _load_default_items() -> List[Dict[str, Any]]:
    with open(DEFAULT_DATASET_PATH, "r") as f:
        return json.load(f)


def run_ragas_evaluation(items: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    settings = get_settings()
    items = items or _load_default_items()

    questions, answers, contexts, ground_truths = [], [], [], []

    for item in items:
        question = item["question"]
        answer, sources, _, _ = answer_question(question)
        questions.append(question)
        answers.append(answer)
        contexts.append([s.text for s in sources] or [""])
        ground_truths.append(item.get("ground_truth") or "")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    judge_llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=0)
    judge_embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)

    logger.info(f"Running RAGAS evaluation on {len(items)} questions...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )

    scores_df = result.to_pandas()
    aggregate = {
        "faithfulness": float(scores_df["faithfulness"].mean()),
        "answer_relevancy": float(scores_df["answer_relevancy"].mean()),
        "context_precision": float(scores_df["context_precision"].mean()),
        "context_recall": float(scores_df["context_recall"].mean()),
    }
    per_question = scores_df.to_dict(orient="records")

    return {"scores": aggregate, "per_question": per_question, "n_items": len(items)}
