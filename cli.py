from textual.app import App
import sqlite_utils
from datetime import datetime, timezone, timedelta

# Import shared logic from waystation.py
from waystation import UserGrep

# Import screens from the screens package
from screens import SearchScreen, FlowScreen, StepScreen

class RGApp(App):
    CSS_PATH = 'styles.tcss'

    def __init__(self, db: sqlite_utils.Database, user_grep: UserGrep = None):
        super().__init__()
        self.db = db
        self.user_grep = user_grep
        self.session_start = datetime.now(timezone.utc) - timedelta(seconds=1)

    def on_mount(self):
        self.install_screen(screen=SearchScreen, name='search')
        self.install_screen(screen=FlowScreen, name='flows')
        self.install_screen(screen=StepScreen, name='steps')
        self.push_screen('search')  # Start on the search screen


if __name__ == "__main__": # pragma: no cover
    from waystation import init_waystation
    import argparse

    # Initialize the database and $HOME/.waystation directory
    db = init_waystation()

    parser = argparse.ArgumentParser(description="Textual ripgrep-ast browser")
    parser.add_argument('pattern', nargs='?', help="Pattern to search")
    parser.add_argument('paths', nargs='*', help="Search in these files/dirs")
    args = parser.parse_args()

    if args.pattern is None:
        RGApp(db).run()
    else:
        RGApp(db, UserGrep(args.pattern, args.paths)).run()
