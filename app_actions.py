from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import asdict
from db import (
    Flow, Match, FlowMatch, MatchNote, FlowHistory, FlowHistoryResult,
    insert_row, get_row, update_row, archive_row, prepare_row
)

def new_flow(db, flow: Flow) -> int:
    """Create a new flow and return its id."""
    return insert_row(db, "flows", flow)

def get_latest_flow(db) -> Optional[Flow]:
    """Get the most recent flow that is not archived."""
    result = list(db.query("""
        SELECT * FROM flows
        WHERE archived = FALSE
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """))
    return Flow(**result[0]) if result else None

def rename_flow(db, flow: Flow, new_name: str):
    """Rename a flow."""
    flow.name = new_name
    update_row(db, "flows", flow.id, flow)

def save_match(db, match: Match, flow_id: int =None) -> int:
    """Save a new match and return its id."""
    if flow_id:
        match_id = insert_row(db, "matches", match)
        insert_row(db, "flow_matches", FlowMatch(flows_id=flow_id, matches_id=match_id, order_index=0))
        return match_id
    
    matches_table = db['matches']
    new_flow = Flow(name=f"New Flow {datetime.now()}", description=f"Auto-created flow for line: {match.line} - in: {match.file_name}")
    matches_table.insert(prepare_row(match)).m2m('flows', prepare_row(new_flow), m2m_table='flow_matches', pk="id")
    return matches_table.last_pk

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

def get_active_flow_id(db, session_start: datetime = None) -> Optional[int]:
    """Get the currently active flow id (most recent in flow_history).
    Returns None if the most recent flow is archived or if there's no history."""

    result = list(db.query(f"""
        SELECT fh.flow_id, f.archived
        FROM flow_history fh
        LEFT JOIN flows f ON fh.flow_id = f.id
        WHERE fh.created_at >= :session_start
        ORDER BY fh.created_at DESC, fh.id DESC
        LIMIT 1
    """, {"session_start": session_start}))  
    return result[0].get("flow_id") if result and not result[0].get("archived") else None

def get_active_flow(db, session_start: datetime = None) -> Optional[Flow]:
    """Get the currently active flow object."""
    flow_id = get_active_flow_id(db, session_start=session_start)
    if flow_id:
        return get_row(db, "flows", flow_id, Flow)
    return None

def get_flow_history(db, limit: int = 10) -> list:
    """Get recent flow history with flow details."""
    return [FlowHistoryResult(*fh) for fh in db.execute("""
        SELECT fh.id, fh.flow_id, fh.created_at, f.name, f.description
        FROM flow_history fh
        JOIN flows f ON fh.flow_id = f.id
        WHERE f.archived = FALSE
        ORDER BY fh.created_at DESC
        LIMIT ?
    """, [limit]).fetchall()]

def get_flow_match_counts(db, flow_ids):
    return db.query(
        f"""
        SELECT flows_id, COUNT(*) as match_count
        FROM flow_matches
        WHERE flows_id IN ({','.join([str(i) for i in flow_ids])}) AND archived = 0
        GROUP BY flows_id
        """
    )

def get_flow_matches(db, flow_id: int) -> List[Tuple[Match, FlowMatch]]:
    """Get all matches for a specific flow with their FlowMatch relationship data, ordered by order_index"""
    if not flow_id:
        return []
    
    results = db.execute("""
        SELECT m.*, fm.order_index, fm.id as flow_match_id
        FROM matches m
        JOIN flow_matches fm ON m.id = fm.matches_id
        WHERE fm.flows_id = ? AND m.archived = 0 AND fm.archived = 0
        ORDER BY fm.order_index ASC, fm.created_at ASC
    """, [flow_id]).fetchall()
    
    matches_with_flow_data = []
    for row in results:
        # Create Match object from row data
        match_data = {k: row[k] for k in row.keys() if k not in ['order_index', 'flow_match_id']}
        match = Match(**match_data)
        
        # Create FlowMatch object
        flow_match = FlowMatch(
            id=row['flow_match_id'],
            flows_id=flow_id,
            matches_id=match.id,
            order_index=row['order_index']
        )
        
        matches_with_flow_data.append((match, flow_match))
    
    return matches_with_flow_data
