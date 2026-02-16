from fastapi import APIRouter, HTTPException, status

from app.schemas import AIExplainRequest, AIExplainResponse
from app.services.ai import generate_ai_explanation

router = APIRouter(prefix="/v1/ai", tags=["ai"])


@router.post("/explain", response_model=AIExplainResponse)
def explain_endpoint(request: AIExplainRequest) -> AIExplainResponse:
    try:
        provider, model, answer = generate_ai_explanation(
            question=request.question,
            context_type=request.context_type,
            context=request.context,
            provider=request.provider,
            model=request.model,
            max_tokens=request.max_tokens,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AIExplainResponse(provider=provider, model=model, answer=answer)
