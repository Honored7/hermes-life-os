"""Skeleton tests: layers importable, facades delegate, layering enforced.

Conventions (match upstream): demo/* is imported with demo/ on sys.path
(`import storage`), and storage honors $HOME — so core tests reload the
module under a tmp HOME and never touch the real ~/.hermes.
"""
import ast
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DEMO_DIR = ROOT / "demo"
SUPERAPP_DIR = ROOT / "superapp"

sys.path.insert(0, str(ROOT))


def _parse_sources():
    files = sorted((SUPERAPP_DIR).rglob("*.py"))
    assert files, "superapp/ skeleton missing"
    return files


def _top_level_imports(tree: ast.Module) -> list[str]:
    names = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


class TestLayersImportable:
    def test_layers(self):
        import superapp

        assert superapp.LAYERS == (
            "core", "intelligence", "relief", "experience", "surfaces",
        )
        for layer in superapp.LAYERS:
            importlib.import_module(f"superapp.{layer}")

    def test_surfaces_contract(self):
        from superapp.surfaces import API_CONTRACT_VERSION

        assert API_CONTRACT_VERSION == "v1"


class TestCoreFacade:
    def test_store_roundtrip_in_tmp_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
            sys.modules.pop(mod, None)
        sys.path.insert(0, str(DEMO_DIR))
        import storage as s

        importlib.reload(s)
        monkeypatch.syspath_prepend(str(ROOT))
        from superapp.core import get_store

        store = get_store()
        store.save_profile({"name": "tester", "onboarded": True})
        assert store.load_profile()["name"] == "tester"
        store.write_memory({"type": "mood", "content": "steady", "score": 7})
        assert store.memory_count() >= 1
        hits = store.search_memory("steady", limit=5)
        assert hits and hits[-1]["content"] == "steady"


class TestIntelligenceFacades:
    def test_detect_patterns_shape(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
            sys.modules.pop(mod, None)
        sys.path.insert(0, str(DEMO_DIR))
        from superapp.intelligence import detect_patterns

        patterns = detect_patterns()
        assert isinstance(patterns, dict)
        assert "insights" in patterns
        assert "correlation_details" in patterns

    def test_correlations_empty_without_data(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
            sys.modules.pop(mod, None)
        sys.path.insert(0, str(DEMO_DIR))
        from superapp.intelligence import correlations

        assert correlations([]) == []


class TestReliefHonesty:
    def test_relief_available_after_library_migration(self):
        from superapp.relief import relief_available

        assert relief_available() is True

    def test_recommend_ranks_proven_methods(self):
        from superapp.relief import recommend
        from superapp.relief.ledger import InMemoryLedger

        result = recommend("angry", severity=8, ledger=InMemoryLedger())
        assert result.recommendations, "angry@8 must rank real methods"
        assert result.protocol is not None  # Anger Reset journey attaches
        names = [r.name for r in result.recommendations]
        assert any("Cold Water" in n for n in names)

    def test_experience_migrated(self):
        # With no data the rooms degrade to invitations, never crash.
        from superapp import experience

        briefing = experience.briefing()
        assert "greeting" in briefing and "true_line" in briefing
        climate = experience.climate()
        assert climate["span"] == 0 and "signals" in climate
        keep = experience.keepsake()
        assert "letter" in keep and "recognitions" in keep

    def test_ledger_contract(self):
        from superapp.relief import complete_outcome

        class MemLedger:
            def __init__(self):
                self.rows = []

            def log_outcome(self, **kw):
                self.rows.append(kw)

            def effectiveness_for(self, name):
                vals = [r["effectiveness"] for r in self.rows
                        if r["name"] == name and r["effectiveness"]]
                return sum(vals) / len(vals) if vals else None

        ledger = MemLedger()
        complete_outcome(ledger, name="Cold Water", state="angry",
                         severity_before=8, severity_after=5, effectiveness=4)
        assert ledger.effectiveness_for("Cold Water") == 4


class TestLayering:
    """Modularity guardrail: no top-level demo/wellness imports (those must
    stay lazy inside functions), no sys.path hacks at import time, and
    dependencies only flow core <- intelligence <- relief <- experience."""

    BANNED_TOP_LEVEL = {
        "storage", "analytics", "patterns", "demo", "wellness",
        "demo.storage", "demo.patterns", "demo.analytics",
    }

    ALLOWED_FLOW = {
        "superapp": set(),
        "superapp.core": set(),
        "superapp.intelligence": {"superapp.core"},
        "superapp.relief": {"superapp.core", "superapp.intelligence"},
        "superapp.experience": {
            "superapp.core", "superapp.intelligence", "superapp.relief",
        },
        "superapp.surfaces": {
            "superapp.core", "superapp.intelligence", "superapp.relief",
            "superapp.experience",
        },
    }

    def _module_name(self, path: Path) -> str:
        rel = path.relative_to(ROOT).with_suffix("")
        return ".".join(rel.parts)

    def test_no_banned_top_level_imports(self):
        violations = []
        for path in self._parse_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for name in _top_level_imports(tree):
                top = name.split(".")[0]
                if top in self.BANNED_TOP_LEVEL or name in self.BANNED_TOP_LEVEL:
                    violations.append(f"{path.relative_to(ROOT)}: {name}")
        assert not violations, f"move demo imports inside functions: {violations}"

    def test_no_sys_path_hacks_at_import_time(self):
        violations = []
        for path in self._parse_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    src = ast.dump(node.value)
                    if "sys.path" in src:
                        violations.append(str(path.relative_to(ROOT)))
        assert not violations, f"sys.path edits must be inside functions: {violations}"

    def test_dependency_direction(self):
        violations = []
        for path in self._parse_files():
            mod = self._module_name(path)
            layer = self._layer_of(mod)
            allowed = self.ALLOWED_FLOW[layer]
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        mods = [a.name for a in node.names]
                    else:
                        mods = [node.module or ""]
                    for m in mods:
                        if m.startswith("superapp.") and m != mod:
                            dep = self._layer_of(m)
                            if dep not in allowed and dep != layer:
                                violations.append(f"{mod} -> {m}")
        assert not violations, f"layering violated: {sorted(set(violations))}"

    def _parse_files(self):
        return _parse_sources()

    def _layer_of(self, dotted: str) -> str:
        parts = dotted.split(".")
        if len(parts) == 1:
            return "superapp"
        if parts[1] == "__init__":
            return "superapp"
        if len(parts) >= 2:
            return ".".join(parts[:2])
        return "superapp"

    # Only these seam modules may touch demo/* (anywhere, even lazily).
    # Everything else talks to seams, never to upstream directly — this
    # is what lets upstream change shape without Motif breaking.
    SEAM_ALLOWLIST = {
        Path("superapp/core/store.py"),
        Path("superapp/experience/store.py"),
        Path("superapp/intelligence/patterns.py"),
        Path("superapp/intelligence/narrate.py"),
        Path("superapp/surfaces/writes.py"),
        Path("superapp/surfaces/rhythm.py"),
    }
    DEMO_MODULES = {
        "storage", "tools", "patterns", "analytics", "plugins",
        "notifications", "scheduler", "backup", "nudges", "demo",
        "integrations", "wellness",
    }

    def test_demo_access_only_through_seams(self):
        violations = []
        for path in self._parse_files():
            imported: set[str] = set()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0]
                                    for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            touched = imported & self.DEMO_MODULES
            if touched and path.relative_to(ROOT) not in self.SEAM_ALLOWLIST:
                violations.append(
                    f"{path.relative_to(ROOT)} touches {sorted(touched)}")
        assert not violations, (
            "demo/* may only be touched inside seam modules "
            f"(see SEAM_ALLOWLIST): {violations}")
