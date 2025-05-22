from pydantic import BaseModel
from typing import List, Optional, TypeVar

T = TypeVar('T')

class PaginationRequest(BaseModel):
    page: int = 1
    page_size: int = 10

class CursorPaginationRequest(BaseModel):
    cursor: Optional[str] = None  # MongoDB ObjectId as string
    page_size: int = 10
    with_total: bool = False


class CursorPaginationResponse(BaseModel):
    items: List[T]
    next_cursor: Optional[str]
    page_size: int
    total: Optional[int] = None