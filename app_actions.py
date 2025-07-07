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
