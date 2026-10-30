"""KIN NEXT smoke tests. Uses fictional data and no network requests."""
from pathlib import Path
import ast

from kin_core import assess_alerts, detect_internal_conflicts, sample_commitments, simulated_alert

ROOT = Path(__file__).resolve().parents[1]


def test_prototype_is_independent_from_sqlite():
    source = (ROOT / "kin_next.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [alias.name for n in ast.walk(tree) if isinstance(n, ast.Import)
                for alias in n.names]
    assert "kin_store" not in imports
    assert "app" not in imports
    assert "st.set_page_config" in source
    assert "get_weather(lat, lon, city)" in source
    assert "answer_question(q, context)" in source
    assert "on_click=approve" in source


def test_simulated_weather_matches_fictional_exam():
    impacts = assess_alerts(sample_commitments(), [simulated_alert()], 30)
    assert impacts
    assert all(item["is_simulation"] for item in impacts)
    assert any("exam" in item["commitment"].lower() for item in impacts)


def test_fictional_events_are_conflict_free_initially():
    assert detect_internal_conflicts(sample_commitments()) == []


def test_app_can_render_offline():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "kin_next.py"), default_timeout=20).run()
    assert not app.exception, [str(e.message) for e in app.exception]
    assert app.title or app.markdown
