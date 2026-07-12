from fastapi import APIRouter
from app.models.schemas import EvalRequest, EvalResponse
from app.services.evaluation import run_ragas_evaluation

router = APIRouter(prefix="/api/evaluate", tags=["evaluation"])


@router.post("", response_model=EvalResponse)
def evaluate_rag(request: EvalRequest):
    items = [item.model_dump() for item in request.items] if request.items else None
    result = run_ragas_evaluation(items)
    return EvalResponse(**result)
