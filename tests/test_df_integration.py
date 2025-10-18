import os
import pytest
from typer.testing import CliRunner

from git_dataframe_tools.cli.git_df import app as git_df_app
from git_dataframe_tools.cli.scoreboard import app as scoreboard_app
from tests.fixtures.sample_data import sample_commits

runner = CliRunner()

@pytest.mark.parametrize("git_repo", [sample_commits], indirect=True)
def test_git_df_scoreboard_integration(git_repo, tmp_path):
    """Test the integration between git-df and git-scoreboard."""
    output_file = tmp_path / "commits.parquet"
    original_cwd = os.getcwd()
    os.chdir(git_repo)

    try:
        # 1. Run git-df to create a parquet file
        result_df = runner.invoke(
            git_df_app,
            [
                "--output",
                str(output_file),
                "--repo-path",
                ".",
                "--since",
                "10 years ago",
            ],
        )
        assert result_df.exit_code == 0
        assert output_file.exists()

        # 2. Run git-scoreboard with the created parquet file
        result_scoreboard = runner.invoke(
            scoreboard_app,
            [
                "--df-path",
                str(output_file),
                "--author",
                "Test User",
            ],
        )
        assert result_scoreboard.exit_code == 0
        
        # 3. Check the output
        output = result_scoreboard.stdout
        assert "Analysis period: " in output
        assert "Author: Test User <test@example.com>" in output
        assert "Rank:          #1 of 1 authors" in output

    finally:
        os.chdir(original_cwd)