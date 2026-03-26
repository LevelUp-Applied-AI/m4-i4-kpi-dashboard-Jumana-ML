from pathlib import Path


def test_analysis_script_exists():
    assert Path("analysis.py").exists(), "analysis.py not found"


def test_analysis_script_has_functions():
    """Verify analysis.py defines the required function signatures."""
    content = Path("analysis.py").read_text()
    for func in ["def connect_db", "def extract_data", "def compute_kpis",
                  "def run_statistical_tests", "def create_visualizations", "def main"]:
        assert func in content, f"analysis.py missing function: {func}"


def test_kpi_framework_exists():
    path = Path("kpi_framework.md")
    assert path.exists(), "kpi_framework.md not found"
    content = path.read_text()
    assert len(content) > 300, "kpi_framework.md appears too short — fill in all 5 KPIs"


def test_executive_summary_exists():
    path = Path("EXECUTIVE_SUMMARY.md")
    assert path.exists(), "EXECUTIVE_SUMMARY.md not found"
    content = path.read_text()
    assert len(content) > 200, "EXECUTIVE_SUMMARY.md appears too short — write substantive findings"


def test_learner_tests_exist():
    path = Path("tests/test_analysis.py")
    assert path.exists(), "tests/test_analysis.py not found"
    content = path.read_text()
    assert content.count("def test_") >= 3, (
        "tests/test_analysis.py should contain at least 3 test functions"
    )


def test_schema_and_seed_present():
    assert Path("schema.sql").exists(), "schema.sql not found"
    assert Path("seed_data.sql").exists(), "seed_data.sql not found"
