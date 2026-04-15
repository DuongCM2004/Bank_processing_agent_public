from __future__ import annotations

from fastapi import APIRouter, status

from ops_agent.api.dependencies import SystemHealthServiceDep
from ops_agent.api.schemas import HealthcheckResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthcheckResponse, status_code=status.HTTP_200_OK)
def read_healthcheck(health_service: SystemHealthServiceDep) -> HealthcheckResponse:
    overall_status, checks = health_service.get_health_status()
    return HealthcheckResponse(
        status=overall_status,
        service="ops-agent-backend",
        checks=checks,
    )

