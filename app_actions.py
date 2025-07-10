from typing import Optional
from db import (
    get_db,
    Flow, Match, FlowMatch, MatchNote, FlowHistory,
    insert_row, get_row, update_row, archive_row, list_rows
)

def new_flow(db, flow: Flow) -> int:
    """Create a new flow and return its id."""
    return insert_row(db, "flows", flow)

def rename_flow(db, flow: Flow, new_name: str):
    """Rename a flow."""
    flow.name = new_name
    update_row(db, "flows", flow.id, flow)

def save_match(db, match: Match) -> int:
    """Save a new match and return its id."""
    return insert_row(db, "matches", match)

def add_match_note(db, match_note: MatchNote) -> int:
    """Add a note to a match and return its id."""
    return insert_row(db, "match_notes", match_note)

def add_match_to_flow(db, flow_match: FlowMatch) -> int:
    """Add a match to a flow at a specific order index."""
    return insert_row(db, "flow_matches", flow_match)

def archive_flow(db, flow: Flow):
    """Archive a flow."""
    archive_row(db, "flows", flow.id)

def archive_match(db, match: Match):
    """Archive a match."""
    archive_row(db, "matches", match.id)

def archive_flow_match(db, flow_match: FlowMatch):
    """Archive a flow_match."""
    archive_row(db, "flow_matches", flow_match.id)

def archive_match_note(db, match_note: MatchNote):
    """Archive a match_note."""
    archive_row(db, "match_notes", match_note.id)

def activate_flow(db, flow_id: int) -> int:
    """Activate a flow by adding it to flow_history and return the history id."""
    flow_history = FlowHistory(flow_id=flow_id)
    return insert_row(db, "flow_history", flow_history)

def get_active_flow_id(db) -> Optional[int]:
    """Get the currently active flow id (most recent in flow_history)."""
    result = db.execute("""
        SELECT flow_id FROM flow_history 
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """).fetchone()
    return result[0] if result else None

def get_active_flow(db) -> Optional[Flow]:
    """Get the currently active flow object."""
    flow_id = get_active_flow_id(db)
    if flow_id:
        return get_row(db, "flows", flow_id, Flow)
    return None

def get_flow_history(db, limit: int = 10) -> list:
    """Get recent flow history with flow details."""
    return list(db.execute("""
        SELECT fh.id, fh.flow_id, fh.created_at, f.name, f.description
        FROM flow_history fh
        JOIN flows f ON fh.flow_id = f.id
        WHERE f.archived = FALSE
        ORDER BY fh.created_at DESC
        LIMIT ?
    """, [limit]))
