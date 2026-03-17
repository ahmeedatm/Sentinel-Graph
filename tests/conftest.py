import sys
from pathlib import Path

# Allow both `from ingestion import ...` and direct module imports.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ingestion"))
sys.path.insert(0, str(ROOT / "src" / "analysis"))
