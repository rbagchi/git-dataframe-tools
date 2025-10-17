import json
from pathlib import Path
import pytest

GOLDEN_FILES_DIR = Path(__file__).parent.parent / "data" / "golden_files"
GOLDEN_FILES_DIR.mkdir(parents=True, exist_ok=True)

class GoldenFileManager:
    def __init__(self, request):
        self.request = request

    def _get_golden_file_path(self, test_name, params):
        # Create a unique filename based on test name and parameters
        param_str = "-".join(f"{k}_{v}" for k, v in sorted(params.items()))
        if param_str:
            file_name = f"{test_name}-{param_str}.json"
        else:
            file_name = f"{test_name}.json"
        return GOLDEN_FILES_DIR / file_name

    def load_golden_file(self, test_name, params):
        file_path = self._get_golden_file_path(test_name, params)
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return None

    def save_golden_file(self, test_name, params, content):
        file_path = self._get_golden_file_path(test_name, params)
        with open(file_path, "w") as f:
            json.dump(content, f, indent=4)

@pytest.fixture
def golden_file_manager(request):
    return GoldenFileManager(request)
