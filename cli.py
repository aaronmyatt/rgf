from textual.app import App

# Import shared logic from waystation.py
from waystation import UserGrep

# Import screens from the screens package
from screens import SearchScreen, BlankScreen2, BlankScreen3

class RGApp(App):
    CSS_PATH = 'styles.tcss'

    def __init__(self, user_grep: UserGrep = None):
        super().__init__()
        self.user_grep = user_grep

    def on_mount(self):
        self.install_screen(screen=SearchScreen, name='search')
        self.install_screen(screen=BlankScreen2, name='blank2')
        self.install_screen(screen=BlankScreen3, name='blank3')
        self.push_screen('search')  # Start on the search screen


if __name__ == "__main__": # pragma: no cover
    from waystation import init_waystation
    import argparse

    # Initialize the database and $HOME/.waystation directory
    init_waystation()

    parser = argparse.ArgumentParser(description="Textual ripgrep-ast browser")
    parser.add_argument('pattern', nargs='?', help="Pattern to search")
    parser.add_argument('paths', nargs='*', help="Search in these files/dirs")
    args = parser.parse_args()

    if args.pattern is None:
        RGApp().run()
    else:
        RGApp(UserGrep(args.pattern, args.paths)).run()
