import os
import tempfile
import subprocess
import pytest
from waystation import get_git_info

def test_get_git_info_returns_expected_fields(tmp_path):
    # Create a temporary git repo
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    (repo_dir / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)

    # Should return non-None values
    root, sha, branch = get_git_info(str(repo_dir))
    assert root is not None and os.path.samefile(root, str(repo_dir))
    assert sha is not None and len(sha) == 40
    assert branch in ("master", "main")

    # Should return (None, None, None) for non-git dir
    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()
    root2, sha2, branch2 = get_git_info(str(non_git_dir))
    assert root2 is None and sha2 is None and branch2 is None

def test_get_git_info_in_subdirectory(tmp_path):
    repo_dir = tmp_path / "repo2"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    (repo_dir / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)
    subdir = repo_dir / "subdir"
    subdir.mkdir()
    # Should still find repo root from subdir
    root, sha, branch = get_git_info(str(subdir))
    assert root is not None and os.path.samefile(root, str(repo_dir))
    assert sha is not None and len(sha) == 40
    assert branch in ("master", "main")

def test_get_git_info_detached_head(tmp_path):
    repo_dir = tmp_path / "repo3"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    (repo_dir / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "file.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)
    # Create a detached HEAD state
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir).decode().strip()
    subprocess.run(["git", "checkout", sha], cwd=repo_dir, check=True)
    root, sha2, branch = get_git_info(str(repo_dir))
    assert root is not None and os.path.samefile(root, str(repo_dir))
    assert sha2 == sha
    # In detached HEAD, branch may be None or 'HEAD'
    assert branch in (None, "HEAD")
