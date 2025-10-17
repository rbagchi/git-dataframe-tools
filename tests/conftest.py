import logging

logging.basicConfig(level=logging.DEBUG)

# Import fixtures from new modules
from .fixtures.golden_files import golden_file_manager
from .fixtures.sample_data import sample_commits
from .fixtures.markdown_utils import extract_code_blocks
from .fixtures.git_cli_fixtures import git_repo
from .fixtures.pygit2_fixtures import pygit2_repo
from .fixtures.remote_repo_fixtures import remote_git_repo