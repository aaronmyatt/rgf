import os
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from db import get_db, Match

@dataclass
class UserGrep:
    pattern: str
    paths: list[str]

    def __post_init__(self):
        if not self.paths:
            self.paths = ['.']

def init_waystation():
    waystation_dir = Path.home() / ".waystation"
    waystation_dir.mkdir(exist_ok=True)
    db_path = waystation_dir / "rgf.db"
    schema_path = Path(__file__).parent / "schema.sql"
    db = get_db(str(db_path), str(schema_path))
    return db

def get_rg_matches(args: UserGrep):
    """
    Run ripgrep and returns list of Match objects.
    """
    cmd = ['rg', '--color=never', '--json', '--glob', '!*lock', args.pattern] + args.paths
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    matches = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        match = json.loads(line)
        if match.get('type') == 'match':
            data = match.get('data')
            file_path = data['path']['text']
            file_name = os.path.basename(file_path)
            matches.append(Match(line=data['lines']['text'], file_path=file_path, file_name=file_name, line_no=data['line_number'], grep_meta=data))
    return matches

def get_grep_ast_preview(match: Match):
    """
    Run grep-ast on match.filename and return output as a string.
    If grep-ast fails, show the matching line and its context.
    """
    try:
        result = subprocess.run(
            ['grep-ast', Path(match.file_path).absolute()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        # If grep-ast fails, show context lines
        try:
            with open(match.file_path, 'r') as f:
                lines = f.readlines()
                idx = match.line_no - 1
                context = []
                if idx > 0:
                    context.append(f"{lines[idx-1].rstrip()}")
                context.append(f"{lines[idx].rstrip()}")
                if idx + 1 < len(lines):
                    context.append(f"{lines[idx+1].rstrip()}")
                return "\n".join(context)
        except Exception as e:
            print(f"Error reading file {match.file_path}: {e}")
            return f"<no preview>"
    except FileNotFoundError:
        return "<no preview>"
