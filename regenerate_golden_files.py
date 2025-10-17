import json
from pathlib import Path
from datetime import datetime
import logging
import dataclasses

from git2df.git_parser._chunk_processor import _process_commit_chunk
from git2df.git_parser._commit_metadata_parser import GitLogEntry

# Configure logging to output debug messages to console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def regenerate_golden_files():
    data_dir = Path(__file__).parent / "tests" / "data"
    for log_file in data_dir.glob("*.log"):
        json_file = log_file.with_suffix(".json")
        logger.info(f"Processing {log_file}...")
        with open(log_file, "r") as f:
            git_log_output = f.read()

        if not git_log_output.strip():
            parsed_data = []
        else:
            commit_chunks = git_log_output.split("@@@COMMIT@@@")
            commit_chunks = [chunk for chunk in commit_chunks if chunk.strip()]
            parsed_data: list[GitLogEntry] = []
            for chunk in commit_chunks:
                entry = _process_commit_chunk(chunk)
                if entry:
                    parsed_data.append(entry)

        # Convert dataclass objects to dictionaries for JSON serialization
        parsed_data_as_dicts = []
        for entry in parsed_data:
            entry_dict = dataclasses.asdict(entry)
            # Convert datetime objects to ISO format strings for JSON serialization
            if "commit_date" in entry_dict and isinstance(entry_dict["commit_date"], datetime):
                entry_dict["commit_date"] = entry_dict["commit_date"].isoformat()
            if "file_changes" in entry_dict:
                for change in entry_dict["file_changes"]:
                    pass # No longer removing old_file_path if None
            parsed_data_as_dicts.append(entry_dict)

        with open(json_file, "w") as f:
            json.dump(parsed_data_as_dicts, f, indent=4)
        logger.info(f"Generated {json_file}")

if __name__ == "__main__":
    regenerate_golden_files()