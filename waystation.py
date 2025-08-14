import re
import os
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from db import get_db, Match
import grep_ast

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
    db_path = waystation_dir / "way.db"
    schema_path = Path(__file__).parent / "schema.sql"
    db = get_db(str(db_path), str(schema_path))
    return db

def get_rg_matches(args: UserGrep):
    """
    Run ripgrep and returns list of Match objects.
    """
    cmd = ['rg', '--ignore-case', '--color=never', '--json', '--glob', '!*lock', args.pattern] + args.paths
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
    if not match.line:
        return "<no preview>"
    try:
        path = Path(match.file_path).absolute()
        lines = process_filename(path, {
            "pattern": match.line.strip(),
            "verbose": False,
            "encoding": "utf8",
            "ignore_case": True,
            "color": True,
            "line_numbers": False
        })
        if lines:
            return lines
        try:
            return get_plain_lines_from_file(match)
        except Exception as e:
            print(f"Error reading file {match.file_path}: {e}")
            return f"<no preview>"
    except FileNotFoundError as e:
        print(e)
        return "<no preview>"

def enumerate_files(fnames, spec, use_spec=False):
    for fname in fnames:
        fname = Path(fname)

        # oddly, Path('.').name == "" so we will recurse it
        if fname.name.startswith(".") or use_spec and spec.match_file(fname):
            continue

        if fname.is_file():
            yield str(fname)
            continue

        if fname.is_dir():
            for sub_fnames in enumerate_files(fname.iterdir(), spec, True):
                yield sub_fnames


def process_filename(filename, args):
    try:
        with open(filename, "r", encoding=args.get("encoding")) as file:
            code = file.read()
    except UnicodeDecodeError:
        return

    try:
        tc = grep_ast.TreeContext(filename, code, verbose=args.get("verbose"), line_number=args.get("line_number"), color=args.get("color"))
    except ValueError:
        return

    loi = tc.grep(re.escape(args.get("pattern")), ignore_case=args.get("ignore_case"))
    if not loi:
        return

    tc.add_lines_of_interest(loi)
    tc.add_context()
    return tc.format()

def get_plain_lines_from_file(match, context_lines=1):
    """Get matching line with surrounding context from file.

    Args:
        match: Match object containing file info
        context_lines: Number of lines to show before/after match (default: 1)
    """
    path = Path(match.file_path).absolute()
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            idx = match.line_no - 1
            context = []

            # Get lines before the match
            for i in range(max(0, idx - context_lines), idx):
                context.append(f"{lines[i].rstrip()}")

            # Add the matching line itself
            context.append(f"{lines[idx].rstrip()}")

            # Get lines after the match
            for i in range(idx + 1, min(len(lines), idx + context_lines + 1)):
                context.append(f"{lines[i].rstrip()}")

            return "\n".join(context)
    except FileNotFoundError:
        # Fall back to the line stored in the match
        return match.line

def get_language_from_filename(filename: str) -> str:
    """Determine syntax highlighting language from file extension"""
    ext = Path(filename).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
    }
    return language_map.get(ext, 'text')

def flow_matches_to_markdown(flow_matches: list) -> str:
    """
    Convert flow matches to markdown format.
    
    Args:
        flow_matches: List of tuples (Match, FlowMatch, Optional[MatchNote])
    
    Returns:
        Markdown string representation of the flow
    """
    markdown_lines = []
    
    for idx, (match, flow_match, note) in enumerate(flow_matches):
        # Step header (##)
        step_num = flow_match.order_index + 1
        header = f"## Step {step_num}: {match.file_name}:{match.line_no}"
        markdown_lines.append(header)
        
        # Note section (### + paragraph)
        if note:
            if note.name:
                markdown_lines.append(f"### {note.name}")
            markdown_lines.append(f"{note.note}\n")
        
        # Code block (```)
        preview_text = get_plain_lines_from_file(match, 3)
        language = get_language_from_filename(match.file_name) or ""
        markdown_lines.append(f"```{language}")
        markdown_lines.append(preview_text)
        markdown_lines.append("```\n")  # Extra newline between steps
        
    return "\n".join(markdown_lines)

def get_git_info(path="."):
    """Return git_repo_root, git_commit_sha, git_branch for the given path."""
    def run_git_cmd(args):
        return subprocess.check_output(
            ["git"] + args, cwd=path
        ).decode("utf-8").strip()
    
    try:
        git_repo_root = run_git_cmd(["rev-parse", "--show-toplevel"])
        git_commit_sha = run_git_cmd(["rev-parse", "HEAD"])
        git_branch = run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
        return git_repo_root, git_commit_sha, git_branch
    except Exception:
        return None, None, None