import pytest
import tempfile
import os

from db import (
    get_db,
    Flow, Match, FlowMatch, MatchNote,
    insert_row, get_row, update_row, archive_row, list_rows
)

@pytest.fixture
def db():
    # Use a temporary file for the database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    schema_path = os.path.join(os.path.dirname(__file__), "../schema.sql")
    db = get_db(db_path, schema_path)
    yield db
    os.remove(db_path)

def test_flow_crud(db):
    flow = Flow(name="Test Flow", description="desc")
    flow_id = insert_row(db, "flows", flow)
    fetched = get_row(db, "flows", flow_id, Flow)
    assert fetched.name == "Test Flow"
    assert fetched.description == "desc"

    # Update
    fetched.description = "updated"
    update_row(db, "flows", flow_id, fetched)
    updated = get_row(db, "flows", flow_id, Flow)
    assert updated.description == "updated"

    # Archive
    archive_row(db, "flows", flow_id)
    archived = get_row(db, "flows", flow_id, Flow)
    assert archived.archived is 1

def test_match_crud(db):
    match = Match(line="foo", file_path="/tmp/foo.py", file_name="foo.py")
    match_id = insert_row(db, "matches", match)
    fetched = get_row(db, "matches", match_id, Match)
    assert fetched.line == "foo"
    assert fetched.file_name == "foo.py"

    # Archive
    archive_row(db, "matches", match_id)
    archived = get_row(db, "matches", match_id, Match)
    assert archived.archived is 1

def test_flowmatch_crud(db):
    # Need a flow and a match first
    flow_id = insert_row(db, "flows", Flow(name="F"))
    match_id = insert_row(db, "matches", Match(line="bar", file_path="/tmp/bar.py", file_name="bar.py"))

    flow_match = FlowMatch(flows_id=flow_id, matches_id=match_id, order_index=1)
    fm_id = insert_row(db, "flow_matches", flow_match)
    fetched = get_row(db, "flow_matches", fm_id, FlowMatch)
    assert fetched.flows_id == flow_id
    assert fetched.matches_id == match_id

    # Archive
    archive_row(db, "flow_matches", fm_id)
    archived = get_row(db, "flow_matches", fm_id, FlowMatch)
    assert archived.archived is 1

def test_matchnote_crud(db):
    match_id = insert_row(db, "matches", Match(line="baz", file_path="/tmp/baz.py", file_name="baz.py"))
    note = MatchNote(match_id=match_id, name="Note1", note="This is a note")
    note_id = insert_row(db, "match_notes", note)
    fetched = get_row(db, "match_notes", note_id, MatchNote)
    assert fetched.name == "Note1"
    assert fetched.note == "This is a note"

    # Archive
    archive_row(db, "match_notes", note_id)
    archived = get_row(db, "match_notes", note_id, MatchNote)
    assert archived.archived is 1

def test_list_rows(db):
    # Insert some test data
    for i in range(5):
        insert_row(db, "matches", Match(line=f"line {i}", file_path=f"/tmp/file{i}.py", file_name=f"file{i}.py"))

    # List all matches
    matches = list_rows(db, "matches", Match)
    assert len(matches) == 5

    # List archived matches (should be none)
    archived_matches = list_rows(db, "matches", Match, "archived=1")
    assert len(archived_matches) == 0

    # Archive one match and check listing
    match_id = matches[0].id
    archive_row(db, "matches", match_id)
    archived_matches = list_rows(db, "matches", Match, "archived=1")
    assert len(archived_matches) == 1
    assert archived_matches[0].id == match_id

def test_get_row_not_found(db):
    # Test getting a row that doesn't exist
    assert get_row(db, "matches", 9999, Match) is None
        