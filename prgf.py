import subprocess
import sys
import shlex

def sanitize_input(arg):
    """Replicates bash printf %q."""
    return shlex.quote(arg)

def rgf(pattern, *paths):
    # Build the rg command
    rg_cmd = ['rg', '--color=always', '-n', pattern] + list(paths)
    try:
        # Start rg process
        rg_proc = subprocess.Popen(
            rg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Build fzf command and options
        fzf_cmd = [
            'fzf',
            '--ansi',
            '--nth', '1',
            '--delimiter', ':',
            '--preview-window', 'up,60%,border-bottom,+{2}/2',
            # --preview: grep-ast $(printf "%q" "{3..}") "{1}"
            '--preview',
            'grep-ast $(printf "%q" "{3..}") "{1}"',
            '--bind',
            'enter:execute(micro {1} +{2})'
        ]

        # Start fzf, piping in rg's output
        subprocess.run(
            fzf_cmd,
            stdin=rg_proc.stdout
        )

        # Optionally: handle rg_proc.returncode, errors, etc.

    except FileNotFoundError as e:
        print(f"Command not found: {e.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive ripgrep + fzf + previewed opener")
    parser.add_argument('pattern', help="Pattern to search")
    parser.add_argument('paths', nargs='*', help="Files/directories to search in (optional)")
    args = parser.parse_args()

    rgf(args.pattern, *args.paths)
