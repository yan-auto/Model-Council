"""Provider API —— 供应商管理"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.data.models import ProviderCreate, ProviderUpdate
from src.data.repositories.provider_repo import (
    create_provider, get_provider, list_providers,
    update_provider, delete_provider, validate_provider,
)
from src.data.repositories.model_repo import list_models

router = APIRouter(prefix="/api", tags=["providers"])


@router.post("/providers")
async def api_create_provider(data: ProviderCreate):
    """添加供应商"""
    if not data.base_url:
        from src.data.models import ProviderType
        defaults = {
            ProviderType.OPENAI_COMPATIBLE: "https://api.openai.com/v1",
            ProviderType.ANTHROPIC: "https://api.anthropic.com",
            ProviderType.MINIMAX: "https://api.minimax.chat/v1",
        }
        data.base_url = defaults.get(data.provider_type, "")
    p = await create_provider(data)
    return _provider_response(p)


@router.get("/providers")
async def api_list_providers():
    """获取供应商列表"""
    providers = await list_providers(status="active")
    return {"providers": [_provider_response(p) for p in providers]}


@router.get("/providers/{provider_id}")
async def api_get_provider(provider_id: str):
    """获取供应商详情"""
    p = await get_provider(provider_id)
    if not p:
        return JSONResponse(status_code=404, content={"error": "供应商不存在"})
    return _provider_response(p)


@router.put("/providers/{provider_id}")
async def api_update_provider(provider_id: str, data: ProviderUpdate):
    """更新供应商"""
    p = await update_provider(provider_id, data)
    if not p:
        return JSONResponse(status_code=404, content={"error": "供应商不存在"})
    return _provider_response(p)


@router.delete("/providers/{provider_id}")
async def api_delete_provider(provider_id: str):
    """删除供应商"""
    ok = await delete_provider(provider_id)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "供应商不存在"})
    return {"status": "deleted"}


@router.post("/providers/{provider_id}/validate")
async def api_validate_provider(provider_id: str):
    """验证供应商连接"""
    p = await get_provider(provider_id)
    if not p:
        return JSONResponse(status_code=404, content={"error": "供应商不存在"})
    valid = await validate_provider(p)
    return {"valid": valid}


@router.get("/providers/{provider_id}/models")
async def api_list_provider_models(provider_id: str):
    """获取该供应商的模型列表"""
    p = await get_provider(provider_id)
    if not p:
        return JSONResponse(status_code=404, content={"error": "供应商不存在"})
    models = await list_models(provider_id=provider_id, status="active")
    return {
        "provider": _provider_response(p),
        "models": [
            {"id": m.id, "model_name": m.model_name, "display_name": m.display_name}
            for m in models
        ],
    }


def _provider_response(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "provider_type": p.provider_type.value,
        "api_key": "••••••••" if p.api_key else "",
        "base_url": p.base_url,
        "group_id": p.group_id,
        "status": p.status,
    }
