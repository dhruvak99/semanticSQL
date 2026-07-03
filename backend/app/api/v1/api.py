from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    cache,
    database,
    dashboard,
    databases,
    health,
    history,
    model_management,
    models,
    query,
    queries,
    research,
    schema,
    schemas,
    settings,
    system_monitor,
    validation,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(query.router, prefix="/query", tags=["query-pipeline"])
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
api_router.include_router(cache.router, prefix="/cache", tags=["semantic-cache"])
api_router.include_router(database.router, prefix="/database", tags=["database-explorer"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(databases.router, prefix="/databases", tags=["databases"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(schema.router, prefix="/schema", tags=["schema"])
api_router.include_router(schemas.router, prefix="/schemas", tags=["schemas"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(model_management.router, prefix="/model-management", tags=["model-management"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(system_monitor.router, prefix="/system-monitor", tags=["system-monitor"])
