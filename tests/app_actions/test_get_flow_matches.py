import pytest
import tempfile
import os
from datetime import datetime
from dataclasses import asdict
from app_actions import get_flow_matches
from db import Flow, Match, FlowMatch, get_db

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
def sample_flow(db):
    flow = Flow(name="Test Flow", description="Test Description")
    flow_id = db['flows'].insert(asdict(flow)).last_pk
    return flow_id

@pytest.fixture
def sample_match(db):
    match = Match(file_name="test.py", line_no=1, line="test line")
    match_id = db['matches'].insert(asdict(match)).last_pk
    return match_id

@pytest.fixture
def sample_flow_match(db, sample_flow, sample_match):
    flow_match = FlowMatch(flows_id=sample_flow, matches_id=sample_match, order_index=0)
    fm_id = db['flow_matches'].insert(asdict(flow_match)).last_pk
    return fm_id

class TestGetFlowMatches:
    def test_empty_flow_returns_empty_list(self, db):
        assert get_flow_matches(db, 999) == []  # Non-existent flow

    def test_returns_matches_for_flow(self, db, sample_flow, sample_match, sample_flow_match):
        results = get_flow_matches(db, sample_flow)
        assert len(results) == 1
        match, flow_match = results[0]
        assert isinstance(match, Match)
        assert isinstance(flow_match, FlowMatch)
        assert match.id == sample_match
        assert flow_match.id == sample_flow_match

    def test_ordering_by_order_index(self, db, sample_flow):
        # Add multiple matches with different order_index values
        match1 = Match(file_name="test1.py", line_no=1, line="line1")
        match2 = Match(file_name="test2.py", line_no=2, line="line2")

        m1_id = db['matches'].insert(asdict(match1)).last_pk
        m2_id = db['matches'].insert(asdict(match2)).last_pk

        # Insert out of order
        db['flow_matches'].insert(asdict(FlowMatch(
            flows_id=sample_flow, matches_id=m2_id, order_index=2
        )))
        db['flow_matches'].insert(asdict(FlowMatch(
            flows_id=sample_flow, matches_id=m1_id, order_index=1
        )))

        results = get_flow_matches(db, sample_flow)
        assert len(results) == 2
        assert results[0][0].file_name == "test1.py"  # Should come first (order_index=1)
        assert results[1][0].file_name == "test2.py"  # Should come second (order_index=2)

    def test_excludes_archived_matches(self, db, sample_flow, sample_match, sample_flow_match):
        # Archive the match
        db['matches'].update(sample_match, {'archived': 1})

        results = get_flow_matches(db, sample_flow)
        assert len(results) == 0

    def test_excludes_archived_flow_matches(self, db, sample_flow, sample_match, sample_flow_match):
        # Archive the flow_match relationship (but keep match)
        db['flow_matches'].update(sample_flow_match, {'archived': 1})

        results = get_flow_matches(db, sample_flow)
        assert len(results) == 0

    def test_returns_empty_for_invalid_flow_id(self, db):
        assert get_flow_matches(db, None) == []
        assert get_flow_matches(db, 0) == []
        assert get_flow_matches(db, -1) == []