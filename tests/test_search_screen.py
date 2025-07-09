import pytest
from cli import RGApp
from waystation import UserGrep


# async def test_app_initialization():
#     """Test that the app initializes correctly without arguments."""
#     app = RGApp()
#     async with app.run_test() as pilot:
#         raise
#         await app.push_screen(app.SCREENS['search']())  # Ensure we start on the search screen
#         assert app.user_grep is None
#         assert app.screen.id == "search"


async def test_input_submission_returns_matches():
    app = RGApp()
    async with app.run_test() as pilot:
        pilot.press("escape")  # to clear initial input focus
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "async def test_input_submission_returns_matches"
        paths_input.value = "test_data/"

        await pilot.press("enter")
        assert len(app.screen.matches) == 1
        assert "test_data/sample_code.py" in app.screen.matches[0].filename
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 1
    