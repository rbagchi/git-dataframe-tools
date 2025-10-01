import pytest
import pandas as pd
from git_scoreboard.git_stats_pandas import parse_git_log_to_dataframe, get_author_stats_dataframe, find_author_stats_pandas, print_ranking_pandas

def test_parse_git_log_to_dataframe_empty_input():
    git_data = ""
    df = parse_git_log_to_dataframe(git_data)
    assert df.empty
    assert list(df.columns) == ['commit_hash', 'author_name', 'author_email', 'commit_message', 'added', 'deleted', 'filepath']

def test_parse_git_log_to_dataframe_single_commit_single_file():
    git_data = """
commit_hash1|Author Name|author@example.com|Commit message 1
10	5	file1.txt
"""
    df = parse_git_log_to_dataframe(git_data)
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]['commit_hash'] == 'commit_hash1'
    assert df.iloc[0]['author_name'] == 'Author Name'
    assert df.iloc[0]['author_email'] == 'author@example.com'
    assert df.iloc[0]['commit_message'] == 'Commit message 1'
    assert df.iloc[0]['added'] == 10
    assert df.iloc[0]['deleted'] == 5
    assert df.iloc[0]['filepath'] == 'file1.txt'

def test_parse_git_log_to_dataframe_multiple_commits_multiple_files():
    git_data = """
commit_hash1|Author One|one@example.com|Commit message A
10	5	fileA.txt
2	1	fileB.txt

commit_hash2|Author Two|two@example.com|Commit message B
1	1	fileC.txt
"""
    df = parse_git_log_to_dataframe(git_data)
    assert not df.empty
    assert len(df) == 3
    
    # Commit 1, File A
    assert df.iloc[0]['commit_hash'] == 'commit_hash1'
    assert df.iloc[0]['author_name'] == 'Author One'
    assert df.iloc[0]['author_email'] == 'one@example.com'
    assert df.iloc[0]['commit_message'] == 'Commit message A'
    assert df.iloc[0]['added'] == 10
    assert df.iloc[0]['deleted'] == 5
    assert df.iloc[0]['filepath'] == 'fileA.txt'

    # Commit 1, File B
    assert df.iloc[1]['commit_hash'] == 'commit_hash1'
    assert df.iloc[1]['author_name'] == 'Author One'
    assert df.iloc[1]['author_email'] == 'one@example.com'
    assert df.iloc[1]['commit_message'] == 'Commit message A'
    assert df.iloc[1]['added'] == 2
    assert df.iloc[1]['deleted'] == 1
    assert df.iloc[1]['filepath'] == 'fileB.txt'

    # Commit 2, File C
    assert df.iloc[2]['commit_hash'] == 'commit_hash2'
    assert df.iloc[2]['author_name'] == 'Author Two'
    assert df.iloc[2]['author_email'] == 'two@example.com'
    assert df.iloc[2]['commit_message'] == 'Commit message B'
    assert df.iloc[2]['added'] == 1
    assert df.iloc[2]['deleted'] == 1
    assert df.iloc[2]['filepath'] == 'fileC.txt'

def test_parse_git_log_to_dataframe_binary_files():
    git_data = """
commit_hash1|Author Name|author@example.com|Commit message 1
-	-	image.png
10	5	file1.txt
"""
    df = parse_git_log_to_dataframe(git_data)
    assert not df.empty
    assert len(df) == 2
    assert df.iloc[0]['added'] == 0
    assert df.iloc[0]['deleted'] == 0
    assert df.iloc[0]['filepath'] == 'image.png'
    assert df.iloc[1]['added'] == 10
    assert df.iloc[1]['deleted'] == 5

def test_get_author_stats_dataframe_empty_input():
    df = pd.DataFrame(columns=['commit_hash', 'author_name', 'author_email', 'commit_message', 'added', 'deleted', 'filepath'])
    author_stats = get_author_stats_dataframe(df)
    assert author_stats.empty
    assert list(author_stats.columns) == ['author_name', 'author_email', 'added', 'deleted', 'total', 'commits', 'rank', 'diff_decile', 'commit_decile']

def test_get_author_stats_dataframe_basic():
    git_data = """
commit1|Author A|a@example.com|msg1
10	5	file1.txt

commit2|Author B|b@example.com|msg2
20	10	file2.txt

commit3|Author A|a@example.com|msg3
5	2	file3.txt
"""
    df = parse_git_log_to_dataframe(git_data)
    author_stats = get_author_stats_dataframe(df)

    assert len(author_stats) == 2
    
    author_a = author_stats[author_stats['author_email'] == 'a@example.com'].iloc[0]
    assert author_a['author_name'] == 'Author A'
    assert author_a['added'] == 15
    assert author_a['deleted'] == 7
    assert author_a['total'] == 22
    assert author_a['commits'] == 2

    author_b = author_stats[author_stats['author_email'] == 'b@example.com'].iloc[0]
    assert author_b['author_name'] == 'Author B'
    assert author_b['added'] == 20
    assert author_b['deleted'] == 10
    assert author_b['total'] == 30
    assert author_b['commits'] == 1

def test_get_author_stats_dataframe_ranks_deciles():
    git_data = """
commit1|A|a@example.com|msg
100	0	f1.txt

commit2|B|b@example.com|msg
50	0	f2.txt

commit3|C|c@example.com|msg
200	0	f3.txt

commit4|D|d@example.com|msg
10	0	f4.txt
"""
    df = parse_git_log_to_dataframe(git_data)
    author_stats = get_author_stats_dataframe(df)

    # Sort by total for easier assertion
    author_stats = author_stats.sort_values(by='total', ascending=False).reset_index(drop=True)

    # C: total 200, commits 1
    assert author_stats.iloc[0]['author_email'] == 'c@example.com'
    assert author_stats.iloc[0]['rank'] == 1
    assert author_stats.iloc[0]['diff_decile'] == 1
    assert author_stats.iloc[0]['commit_decile'] == 1 # All have 1 commit, so all are in decile 1

    # A: total 100, commits 1
    assert author_stats.iloc[1]['author_email'] == 'a@example.com'
    assert author_stats.iloc[1]['rank'] == 2
    assert author_stats.iloc[1]['diff_decile'] == 7
    assert author_stats.iloc[1]['commit_decile'] == 7

    # B: total 50, commits 1
    assert author_stats.iloc[2]['author_email'] == 'b@example.com'
    assert author_stats.iloc[2]['rank'] == 3
    assert author_stats.iloc[2]['diff_decile'] == 10
    assert author_stats.iloc[2]['commit_decile'] == 10

    # D: total 10, commits 1
    assert author_stats.iloc[3]['author_email'] == 'd@example.com'
    assert author_stats.iloc[3]['rank'] == 4
    assert author_stats.iloc[3]['diff_decile'] == 10
    assert author_stats.iloc[3]['commit_decile'] == 10

def test_find_author_stats_pandas_found():
    author_stats_df = pd.DataFrame({
        'author_name': ['John Doe', 'Jane Smith'],
        'author_email': ['john@example.com', 'jane@example.com'],
        'added': [100, 200],
        'deleted': [10, 20],
        'total': [110, 220],
        'commits': [5, 10],
        'rank': [2, 1],
        'diff_decile': [2, 1],
        'commit_decile': [2, 1]
    })
    
    matches = find_author_stats_pandas(author_stats_df, "john")
    assert not matches.empty
    assert len(matches) == 1
    assert matches.iloc[0]['author_name'] == 'John Doe'

def test_find_author_stats_pandas_not_found():
    author_stats_df = pd.DataFrame({
        'author_name': ['John Doe', 'Jane Smith'],
        'author_email': ['john@example.com', 'jane@example.com'],
        'added': [100, 200],
        'deleted': [10, 20],
        'total': [110, 220],
        'commits': [5, 10],
        'rank': [2, 1],
        'diff_decile': [2, 1],
        'commit_decile': [2, 1]
    })
    
    matches = find_author_stats_pandas(author_stats_df, "peter")
    assert matches.empty

def test_print_ranking_pandas_basic():
    author_stats_df = pd.DataFrame({
        'author_name': ['John Doe', 'Jane Smith'],
        'author_email': ['john@example.com', 'jane@example.com'],
        'added': [100, 200],
        'deleted': [10, 20],
        'total': [110, 220],
        'commits': [5, 10],
        'rank': [2, 1],
        'diff_decile': [2, 1],
        'commit_decile': [2, 1]
    })
    
    ranked_df = print_ranking_pandas(author_stats_df)
    assert not ranked_df.empty
    assert ranked_df.iloc[0]['author_name'] == 'Jane Smith' # Sorted by total descending
    assert ranked_df.iloc[1]['author_name'] == 'John Doe'

def test_print_ranking_pandas_empty_input():
    author_stats_df = pd.DataFrame(columns=['author_name', 'author_email', 'added', 'deleted', 'total', 'commits', 'rank', 'diff_decile', 'commit_decile'])
    ranked_df = print_ranking_pandas(author_stats_df)
    assert ranked_df.empty
