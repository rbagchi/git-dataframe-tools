# F401 (unused-imports) is ignored in conftest.py because pytest automatically discovers and uses fixtures,
# so explicit usage within conftest.py is not required and would be misleading to linters.
# ruff: noqa: F401
import logging

# This conftest.py is used to make fixtures defined in tests/fixtures/ available to all tests.
# For fixture implementations, please refer to the files in the tests/fixtures/ directory.

# Import fixtures from new modules
from .fixtures.golden_files import golden_file_manager
from .fixtures.sample_data import sample_commits
from .fixtures.markdown_utils import extract_code_blocks
from .fixtures.git_cli_fixtures import git_repo
from .fixtures.pygit2_fixtures import pygit2_repo
from .fixtures.remote_repo_fixtures import remote_git_repo

logging.basicConfig(level=logging.DEBUG)