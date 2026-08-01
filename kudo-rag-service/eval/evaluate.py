import json
import sys
import io
import logging
from pathlib import Path

# Force UTF-8 output encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.rag_chain import generate_rag_answer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_evaluation() -> None:
    """
    Load golden_set_v2.json (or golden_set.json), execute RAG pipeline, and evaluate accuracy pass rate.
    """
    golden_set_path = PROJECT_ROOT / "eval" / "golden_set_v2.json"
    if not golden_set_path.exists():
        golden_set_path = PROJECT_ROOT / "eval" / "golden_set.json"
        
    if not golden_set_path.exists():
        print(f"❌ Error: Golden set file not found at {golden_set_path}")
        return

    with open(golden_set_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)
    passed = 0

    print("==================================================")
    print("🚀 RUNNING RAG EVALUATION SUITE FOR KUDO-RAG-SERVICE")
    print(f"Total Test Cases: {total}")
    print("==================================================\n")

    for tc in test_cases:
        tc_id = tc.get("id")
        question = tc.get("question", "")
        expected = tc.get("expected_answer_contains", "")

        print(f"🔹 [{tc_id}] Question: '{question}'")
        print(f"   Expected Keyphrase: '{expected}'")

        try:
            answer, sources = generate_rag_answer(question)
            print(f"   Generated Answer: {answer}")
            print(f"   Sources Count: {len(sources)}")

            if isinstance(expected, list):
                is_pass = any(exp.lower() in answer.lower() for exp in expected)
            else:
                is_pass = expected.lower() in answer.lower()

            if is_pass:
                passed += 1
                print("   Status: ✅ PASS\n")
            else:
                print("   Status: ❌ FAIL\n")
        except Exception as e:
            logger.error(f"Error evaluating test case {tc_id}: {e}")
            print("   Status: ❌ ERROR\n")

    pass_rate = (passed / total) * 100 if total > 0 else 0.0
    print("==================================================")
    print("📊 EVALUATION SUMMARY")
    print(f"Passed: {passed}/{total}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("==================================================")


if __name__ == "__main__":
    run_evaluation()
