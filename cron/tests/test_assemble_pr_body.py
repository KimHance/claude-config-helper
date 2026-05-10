from scripts.assemble_pr_body import render


def test_render_replaces_simple():
    tmpl = "version {{NEW_VERSION}} ({{BUMP_LEVEL}})"
    out = render(tmpl, {"NEW_VERSION": "0.5.0", "BUMP_LEVEL": "minor"})
    assert out == "version 0.5.0 (minor)"


def test_render_strips_empty_block():
    tmpl = "before\n{{IF WARNINGS}}\n** WARN **\n{{END}}\nafter"
    out = render(tmpl, {"WARNINGS": ""})
    assert "WARN" not in out


def test_render_keeps_filled_block():
    tmpl = "{{IF WARNINGS}}\n{{WARNINGS}}\n{{END}}"
    out = render(tmpl, {"WARNINGS": "danger"})
    assert "danger" in out
