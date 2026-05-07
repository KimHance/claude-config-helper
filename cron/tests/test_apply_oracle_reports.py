import textwrap
from scripts.apply_oracle_reports import split_by_h2, merge_by_h2


def test_split_by_h2_basic():
    md = textwrap.dedent("""
        # title

        intro text

        ## Fundamentals
        - a
        - b

        ## Advanced
        - c

        ## Recommended
        - d

        ## Anti-patterns
        - e
    """).strip() + "\n"

    head, sections = split_by_h2(md)
    assert "# title" in head
    assert "intro text" in head
    assert sections["Fundamentals"].strip() == "- a\n- b"
    assert sections["Advanced"].strip() == "- c"
    assert sections["Recommended"].strip() == "- d"
    assert sections["Anti-patterns"].strip() == "- e"


def test_merge_by_h2_roundtrip():
    md = textwrap.dedent("""
        # x

        ## Fundamentals
        - a

        ## Advanced
        - b
    """).strip() + "\n"
    head, sections = split_by_h2(md)
    merged = merge_by_h2(head, sections, ["Fundamentals", "Advanced"])
    assert merged.strip() == md.strip()


def test_merge_replaces_only_changed():
    md_before = textwrap.dedent("""
        # x

        ## Fundamentals
        - old fundamentals

        ## Advanced
        - keep me
    """).strip() + "\n"
    head, sections = split_by_h2(md_before)
    sections["Fundamentals"] = "- new fundamentals\n"
    merged = merge_by_h2(head, sections, ["Fundamentals", "Advanced"])
    assert "new fundamentals" in merged
    assert "keep me" in merged
    assert "old fundamentals" not in merged
