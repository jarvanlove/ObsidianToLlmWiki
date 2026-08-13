from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_FILES = (
    "PRODUCT_SPEC.md",
    "ARCHITECTURE.md",
    "TASKS.md",
    "TESTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
)


class EngineeringGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = "\n".join(
            (REPO_ROOT / name).read_text(encoding="utf-8")
            for name in CONTROL_FILES
        ).lower()

    def test_human_controlled_ai_engineering_contract_is_declared(self):
        required_terms = {
            "four-layer fact precedence": ("l0", "l1", "l2", "l3"),
            "trusted context gate": ("context integrity", "context receipt"),
            "bounded context and projections": ("bounded context", "bounded current projections"),
            "memory compiler": ("memory compiler", "evidence-backed"),
            "passive operation": ("passive", "ordinary coding intent"),
            "risk levels": ("p3", "p2", "p1", "p0"),
            "root-cause gate": ("root-cause",),
            "scope-drift gate": ("scope-drift",),
            "human understanding gate": ("human understanding",),
            "structured evidence": ("structured-evidence",),
            "capability recovery": ("capability recovery", "capability observations"),
            "human cockpit": ("human-first", "local cockpit"),
            "privacy boundary": ("private-policy", "secrets"),
            "compatibility strategy": ("compatibility", "idempotency"),
        }

        for contract_name, terms in required_terms.items():
            with self.subTest(contract=contract_name):
                for term in terms:
                    self.assertIn(term, self.contract)


if __name__ == "__main__":
    unittest.main()
