import sqlite_utils
from sqlite_utils.db import NotFoundError
from dataclasses import asdict, dataclass, fields
from typing import Type, TypeVar, List, Optional

T = TypeVar("T")

def get_db(db_path="rgf.db", schema_path="schema.sql"):
    """
    Returns a sqlite_utils.Database instance and ensures the schema is loaded.
    """
    db = sqlite_utils.Database(db_path)
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    db.conn.executescript(schema_sql)
    return db

# --- Dataclasses for each table ---

@dataclass
class Flow:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    parent_flow_id: Optional[int] = None
    parent_flow_match_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: bool = False

@dataclass
class Match:
    id: Optional[int] = None
    line: str = ""
    file_path: str = ""
    file_name: str = ""
    line_no: int = 0
    grep_meta: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: bool = False

@dataclass
class FlowMatch:
    id: Optional[int] = None
    flow_id: int = 0
    match_id: int = 0
    order_index: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: bool = False

@dataclass
class MatchNote:
    id: Optional[int] = None
    match_id: int = 0
    name: str = ""
    description: Optional[str] = None
    note: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: bool = False

@dataclass
class FlowHistory:
    id: Optional[int] = None
    flow_id: int = 0
    created_at: Optional[str] = None

@dataclass
class FlowHistoryResult(FlowHistory):
    name: str = ""
    description: Optional[str] = None

# --- Utility functions ---

def insert_row(db, table: str, row: T) -> int:
    """Insert a dataclass row into the table. Returns the inserted row id."""
    data = asdict(row)
    data = {k: v for k, v in data.items() if v is not None and k != "id"}
    table = db[table].insert(data, pk="id")
    return table.last_pk

def get_row(db, table: str, row_id: int, cls: Type[T]) -> Optional[T]:
    """Get a row by id and return as dataclass instance."""
    try:
        row = db[table].get(row_id)
        if row:
            return cls(**row)
    except NotFoundError:
        return None

def update_row(db, table: str, row_id: int, row):
    """Update a row by id using dataclass."""
    data = asdict(row)
    data = {k: v for k, v in data.items() if k != "id"}
    db[table].update(row_id, data)

def archive_row(db, table: str, row_id: int):
    """Set archived=True for a row by id."""
    db[table].update(row_id, {"archived": True})

def list_rows(db, table: str, cls: Type[T], where: dict = None) -> List[T]:
    """List rows as dataclass instances, optionally filtered by where dict."""
    rows = db[table].rows if where is None else db[table].rows_where(where)
    return [cls(**row) for row in rows]

# Example usage:
# db = get_db()
# flow = Flow(name="My Flow")
# flow_id = insert_row(db, "flows", flow)
# fetched = get_row(db, "flows", flow_id, Flow)
# archive_row(db, "flows", flow_id)
