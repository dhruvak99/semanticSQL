from fastapi import APIRouter, HTTPException, Query

from app.services.database_explorer_service import DatabaseExplorerError, get_table_data, list_database_tables

router = APIRouter()


@router.get("/tables")
def database_tables() -> dict[str, list[dict[str, object]]]:
    return list_database_tables()


@router.get("/table/{table_name}")
def database_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, object]:
    try:
        return get_table_data(table_name, page=page, page_size=page_size)
    except DatabaseExplorerError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
