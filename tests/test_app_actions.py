import pytest
import tempfile
import os
from datetime import datetime
from db import get_db, Flow, Match, FlowMatch, MatchNote, FlowHistory
from app_actions import (
    new_flow, rename_flow, save_match, add_match_note, add_match_to_flow,
    archive_flow, archive_match, archive_flow_match, archive_match_note,
    activate_flow, get_active_flow_id, get_active_flow, get_flow_history
)


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = get_db(db_path)
        yield db
    finally:
        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sample_flow():
    """Create a sample flow for testing."""
    return Flow(name="Test Flow", description="A test flow")



# @dataclass
# class Match:
#     id: Optional[int] = None
#     line: str = ""
#     file_path: str = ""
#     file_name: str = ""
#     grep_meta: Optional[str] = None
#     created_at: Optional[str] = None
#     updated_at: Optional[str] = None
#     archived: bool = False
@pytest.fixture
def sample_match():
    """Create a sample match for testing."""
    return Match(
        file_path="/path/to/file.py",
        file_name="file.py",
        line="test content",
        grep_meta= '{"line_number": 1, "file_path": "/path/to/file.py"}',
    )


@pytest.fixture
def sample_match_note():
    """Create a sample match note for testing."""
    return MatchNote(match_id=1, note="This is a test note")


@pytest.fixture
def sample_flow_match():
    """Create a sample flow match for testing."""
    return FlowMatch(flows_id=1, matches_id=1, order_index=0)


class TestFlowOperations:
    def test_new_flow(self, db, sample_flow):
        """Test creating a new flow."""
        flow_id = new_flow(db, sample_flow)
        
        assert isinstance(flow_id, int)
        assert flow_id > 0
        
        # Verify the flow was saved correctly
        saved_flow = db.execute("SELECT * FROM flows WHERE id = ?", [flow_id]).fetchone()
        flow = Flow(*saved_flow)
        assert saved_flow is not None
        assert flow.name == sample_flow.name
        assert flow.description == sample_flow.description

    def test_rename_flow(self, db, sample_flow):
        """Test renaming a flow."""
        flow_id = new_flow(db, sample_flow)
        sample_flow.id = flow_id
        
        new_name = "Renamed Flow"
        rename_flow(db, sample_flow, new_name)
        
        # Verify the flow was renamed
        updated_flow_row = db.execute("SELECT * FROM flows WHERE id = ?", [flow_id]).fetchone()
        updated_flow = Flow(*updated_flow_row)
        assert updated_flow.name == new_name
        assert sample_flow.name == new_name

    def test_archive_flow(self, db, sample_flow):
        """Test archiving a flow."""
        flow_id = new_flow(db, sample_flow)
        sample_flow.id = flow_id
        
        archive_flow(db, sample_flow)
        
        # Verify the flow was archived
        archived_flow_row = db.execute("SELECT * FROM flows WHERE id = ?", [flow_id]).fetchone()
        archived_flow = Flow(*archived_flow_row)
        assert archived_flow.archived == 1


class TestMatchOperations:
    def test_save_match(self, db, sample_match):
        """Test saving a new match."""
        match_id = save_match(db, sample_match)
        
        assert isinstance(match_id, int)
        assert match_id > 0
        
        # Verify the match was saved correctly
        saved_match_row = db.execute("SELECT * FROM matches WHERE id = ?", [match_id]).fetchone()
        saved_match = Match(*saved_match_row)
        assert saved_match is not None
        assert saved_match.file_path == sample_match.file_path
        assert saved_match.grep_meta == sample_match.grep_meta
        assert saved_match.line == sample_match.line

    def test_archive_match(self, db, sample_match):
        """Test archiving a match."""
        match_id = save_match(db, sample_match)
        sample_match.id = match_id
        
        archive_match(db, sample_match)
        
        # Verify the match was archived
        archived_match_row = db.execute("SELECT * FROM matches WHERE id = ?", [match_id]).fetchone()
        archived_match = Match(*archived_match_row)
        assert archived_match.archived == 1

def test_save_match_and_links_to_active_flow(db, sample_flow):
    from db import Match
    from app_actions import save_match, get_active_flow_id

    flow_id = new_flow(db, sample_flow)
    active_flow_id = activate_flow(db, flow_id)
    assert get_active_flow_id(db) is not None

    # Prepare a match (minimal required fields)
    match = Match(
        line="test line",
        file_path="/tmp/test.py",
        file_name="test.py",
        line_no=1,
        grep_meta='{"line_number": 1, "file_path": "/tmp/test.py"}'
    )

    # Save the match (should create a new flow and link the match)
    match_id = save_match(db, match)

    # The match should exist
    saved_match_row = db.execute("SELECT * FROM matches WHERE id = ?", [match_id]).fetchone()
    assert saved_match_row is not None, "Match should be saved"

    # The match should be linked to the new flow via flow_matches (m2m)
    linked_matches = db.query('SELECT * FROM flow_matches WHERE id = :flows_id;', {"flows_id": active_flow_id})
    match_ids = [m["id"] for m in linked_matches]
    assert match_id in match_ids, "Match should be linked to the new flow via m2m"

def test_save_match_creates_flow_and_links_match_if_no_active_flow(db):
    """
    Fails: When saving a match and no flow is active, a new Flow should be created,
    set as active, and the match should be linked to that flow via flow_matches (m2m).
    """
    from db import Match
    from app_actions import save_match, get_active_flow_id

    # Ensure there is no active flow
    assert get_active_flow_id(db) is None

    # Prepare a match (minimal required fields)
    match = Match(
        line="test line",
        file_path="/tmp/test.py",
        file_name="test.py",
        line_no=1,
        grep_meta='{"line_number": 1, "file_path": "/tmp/test.py"}'
    )

    # Save the match (should create a new flow and link the match)
    match_id = save_match(db, match)

    # A new flow should now exist and be active
    active_flow_id = get_active_flow_id(db)
    assert active_flow_id is not None, "A new flow should be created and set active"

    # The match should exist
    saved_match_row = db.execute("SELECT * FROM matches WHERE id = ?", [match_id]).fetchone()
    assert saved_match_row is not None, "Match should be saved"

    # The match should be linked to the new flow via flow_matches (m2m)
    linked_matches = db.query('SELECT * FROM flow_matches WHERE id = :flows_id;', {"flows_id": active_flow_id})
    match_ids = [m["id"] for m in linked_matches]
    assert match_id in match_ids, "Match should be linked to the new flow via m2m"

class TestMatchNoteOperations:
    def test_add_match_note(self, db, sample_match, sample_match_note):
        """Test adding a note to a match."""
        match_id = save_match(db, sample_match)
        sample_match_note.match_id = match_id
        
        note_id = add_match_note(db, sample_match_note)
        
        assert isinstance(note_id, int)
        assert note_id > 0
        
        # Verify the note was saved correctly
        saved_note_row = db.execute("SELECT * FROM match_notes WHERE id = ?", [note_id]).fetchone()
        saved_note = MatchNote(*saved_note_row)
        assert saved_note is not None
        assert saved_note.match_id == match_id
        assert saved_note.note == sample_match_note.note

    def test_archive_match_note(self, db, sample_match, sample_match_note):
        """Test archiving a match note."""
        match_id = save_match(db, sample_match)
        sample_match_note.match_id = match_id
        note_id = add_match_note(db, sample_match_note)
        sample_match_note.id = note_id
        
        archive_match_note(db, sample_match_note)
        
        # Verify the note was archived
        archived_note_row = db.execute("SELECT * FROM match_notes WHERE id = ?", [note_id]).fetchone()
        archived_note = MatchNote(*archived_note_row)
        assert archived_note.archived == 1


class TestFlowMatchOperations:
    def test_add_match_to_flow(self, db, sample_flow, sample_match, sample_flow_match):
        """Test adding a match to a flow."""
        flow_id = new_flow(db, sample_flow)
        match_id = save_match(db, sample_match)
        
        sample_flow_match.flows_id = flow_id
        sample_flow_match.matches_id = match_id
        
        flow_match_id = add_match_to_flow(db, sample_flow_match)
        
        assert isinstance(flow_match_id, int)
        assert flow_match_id > 0
        
        # Verify the flow_match was saved correctly
        saved_flow_match_row = db.execute("SELECT * FROM flow_matches WHERE id = ?", [flow_match_id]).fetchone()
        saved_flow_match = FlowMatch(*saved_flow_match_row)
        assert saved_flow_match is not None
        assert saved_flow_match.flows_id == flow_id
        assert saved_flow_match.matches_id == match_id
        assert saved_flow_match.order_index == sample_flow_match.order_index

    def test_archive_flow_match(self, db, sample_flow, sample_match, sample_flow_match):
        """Test archiving a flow match."""
        flow_id = new_flow(db, sample_flow)
        match_id = save_match(db, sample_match)
        
        sample_flow_match.flow_id = flow_id
        sample_flow_match.match_id = match_id
        flow_match_id = add_match_to_flow(db, sample_flow_match)
        sample_flow_match.id = flow_match_id
        
        archive_flow_match(db, sample_flow_match)
        
        # Verify the flow_match was archived
        archived_flow_match_row = db.execute("SELECT * FROM flow_matches WHERE id = ?", [flow_match_id]).fetchone()
        archived_flow_match = FlowMatch(*archived_flow_match_row)
        assert archived_flow_match.archived == 1


class TestFlowActivation:
    def test_activate_flow(self, db, sample_flow):
        """Test activating a flow."""
        flow_id = new_flow(db, sample_flow)
        
        history_id = activate_flow(db, flow_id)
        
        assert isinstance(history_id, int)
        assert history_id > 0
        
        # Verify the flow history was created
        history_entry_row = db.execute("SELECT * FROM flow_history WHERE id = ?", [history_id]).fetchone()
        history_entry = FlowHistory(*history_entry_row)
        assert history_entry is not None
        assert history_entry.flow_id == flow_id

    def test_get_active_flow_id_with_no_history(self, db):
        """Test getting active flow ID when no flows have been activated."""
        active_flow_id = get_active_flow_id(db)
        assert active_flow_id is None

    def test_get_active_flow_id_with_history(self, db, sample_flow):
        """Test getting the most recently activated flow ID."""
        flow_id = new_flow(db, sample_flow)
        activate_flow(db, flow_id)
        
        active_flow_id = get_active_flow_id(db)
        assert active_flow_id == flow_id

    def test_get_active_flow_id_multiple_activations(self, db):
        """Test that get_active_flow_id returns the most recent activation."""
        # Create two flows
        flow1 = Flow(name="Flow 1", description="First flow")
        flow2 = Flow(name="Flow 2", description="Second flow")
        
        flow1_id = new_flow(db, flow1)
        flow2_id = new_flow(db, flow2)
        
        # Activate flow1, then flow2
        activate_flow(db, flow1_id)
        activate_flow(db, flow2_id)
        
        # Should return flow2_id as it was activated most recently
        active_flow_id = get_active_flow_id(db)
        assert active_flow_id == flow2_id

    def test_get_active_flow_with_no_history(self, db):
        """Test getting active flow when no flows have been activated."""
        active_flow = get_active_flow(db)
        assert active_flow is None

    def test_get_active_flow_with_history(self, db, sample_flow):
        """Test getting the currently active flow object."""
        flow_id = new_flow(db, sample_flow)
        activate_flow(db, flow_id)
        
        active_flow = get_active_flow(db)
        assert active_flow is not None
        assert active_flow.id == flow_id
        assert active_flow.name == sample_flow.name

    def test_cannot_get_active_flow_with_archived_flow(self, db, sample_flow):
        """Test getting active flow when the active flow has been archived."""
        flow_id = new_flow(db, sample_flow)
        sample_flow.id = flow_id
        activate_flow(db, flow_id)
        archive_flow(db, sample_flow)
        
        # Should still return the flow even if it's archived
        active_flow = get_active_flow(db)
        assert active_flow is None

    def test_returns_none_when_last_active_flow_archived(self, db):
        """Test that get_active_flow_id returns the most recent activation."""
        # Create two flows
        flow1 = Flow(name="Flow 1", description="First flow")
        flow2 = Flow(name="Flow 2", description="Second flow")
        
        flow1_id = new_flow(db, flow1)
        flow2_id = new_flow(db, flow2)
        
        # Activate flow1, then flow2
        activate_flow(db, flow1_id)
        activate_flow(db, flow2_id)
        archive_flow(db, get_active_flow(db))
        
        # Should return flow2_id as it was activated most recently
        active_flow_id = get_active_flow_id(db)
        assert active_flow_id is None


class TestFlowHistory:
    def test_get_flow_history_empty(self, db):
        """Test getting flow history when no flows have been activated."""
        history = get_flow_history(db)
        assert history == []

    def test_get_flow_history_with_entries(self, db):
        """Test getting flow history with multiple entries."""
        # Create and activate multiple flows
        flow1 = Flow(name="Flow 1", description="First flow")
        flow2 = Flow(name="Flow 2", description="Second flow")
        
        flow1_id = new_flow(db, flow1)
        flow2_id = new_flow(db, flow2)
        
        activate_flow(db, flow1_id)
        activate_flow(db, flow2_id)
        activate_flow(db, flow1_id)  # Activate flow1 again
        
        history = get_flow_history(db)
        
        assert len(history) == 3
        # Should be ordered by most recent first
        assert history[0].flow_id == flow1_id
        assert history[1].flow_id == flow2_id
        assert history[2].flow_id == flow1_id
        
        # Check that flow details are included
        assert history[0].name == "Flow 1"
        assert history[1].name == "Flow 2"

    def test_get_flow_history_with_limit(self, db):
        """Test getting flow history with a custom limit."""
        # Create and activate multiple flows
        flow = Flow(name="Test Flow", description="Test")
        flow_id = new_flow(db, flow)
        
        # Activate the flow 5 times
        for _ in range(5):
            activate_flow(db, flow_id)
        
        # Get history with limit of 3
        history = get_flow_history(db, limit=3)
        assert len(history) == 3

    def test_get_flow_history_excludes_archived_flows(self, db):
        """Test that flow history excludes archived flows."""
        flow1 = Flow(name="Flow 1", description="First flow")
        flow2 = Flow(name="Flow 2", description="Second flow")
        
        flow1_id = new_flow(db, flow1)
        flow2_id = new_flow(db, flow2)
        
        activate_flow(db, flow1_id)
        activate_flow(db, flow2_id)
        
        # Archive flow1
        flow1.id = flow1_id
        archive_flow(db, flow1)
        
        history = get_flow_history(db)
        
        # Should only include flow2's activation
        assert len(history) == 1
        assert history[0].flow_id == flow2_id
        assert history[0].name == "Flow 2"
