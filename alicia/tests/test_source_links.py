"""Links to the provision a source quotes (register/source_links.py) and their use on the Industry lens."""

from __future__ import annotations

from urllib.parse import unquote

from alicia.menu import lens
from alicia.register.requirements import load_requirements
from alicia.register.source_links import deep_link, fragment, load_pages, quote_key, section

QLD = "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-2023-028"
TAS = "https://www.legislation.tas.gov.au/view/whole/html/inforce/current/act-2011-023"


def test_section_from_locator():
    assert section("s 52(1) (current)") == "52"
    assert section("ss 62(1), 71C") == "62"
    assert section("s 26K(a)") == "26K"
    assert section("reg 9(1) (current version)") == "9"
    assert section("cl 3") == "3"
    assert section("Sch 7, cl 2(1)") is None
    assert section(None) is None


def test_fragment_takes_a_plain_run_of_words():
    # Clause numbers and list markers are left out: pages often set them apart from the text.
    q = "4.1 This award covers: (a) employers throughout Australia in the banking industry and their employees"
    assert unquote(fragment(q)) == "text=employers throughout Australia in the banking industry and their employees"
    short = "A person must not deal in motor vehicles."
    assert unquote(fragment(short)) == "text=" + short
    # The dash and comma are the fragment's own syntax, so they are always encoded.
    assert "-" not in fragment("a non-residential building work contractor")


def test_links_by_register():
    q = deep_link(QLD, "s 52(1) (current)", "A person must not conduct a tow truck business unless")
    assert q == {"href": QLD + "#sec.52", "how": "section", "text": "Open the law at s 52(1)"}
    assert deep_link(TAS, "s 6(1) (current)", "A person must not deal")["href"] == TAS + "#GS6@EN"
    # No section in the locator: open the law, not a phrase that may match the table of contents first.
    assert deep_link(QLD, "Sch 2, s 57(1)", "Regulated waste transport")["how"] == "law"
    frl = deep_link("https://www.legislation.gov.au/C2004A00818/latest/text", "s 12", "Some words quoted here")
    assert frl["how"] == "law" and "#" not in frl["href"]
    award = deep_link("https://awards.fairwork.gov.au/MA000001.html", "cl 4.1", "4.1 This award covers: (a) employers")
    assert award["how"] == "words" and unquote(award["href"]).endswith("#:~:text=This award covers:")
    wa = deep_link("https://www.legislation.wa.gov.au/legislation/statutes.nsf/RedirectURL?OpenAgent&query=mrdoc_1.docx",
                   "s 5", "words", ("law_a212",))
    assert wa["href"] == "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a212.html"
    sa = deep_link("https://www.legislation.sa.gov.au/__legislation/lz/c/a/x/current/1994.86.un.rtf", "s 5", "words")
    assert sa["how"] == "file"


def test_pdf_pages_match_their_sources():
    """Every page number belongs to a PDF quote that is still in the register."""
    pages = load_pages()
    quoted = {(str(s.url), quote_key(s.quote)) for q in load_requirements().requirements for s in q.sources if s.quote}
    quoted |= {(str(s.url), quote_key(s.quote)) for q in load_requirements().requirements for r in q.reach
               for s in r.sources if s.quote}
    assert pages and set(pages) <= quoted
    assert all(p >= 1 for p in pages.values())


def test_lens_rows_carry_every_quote_with_a_link():
    reqs = load_requirements().requirements
    for q in reqs:
        row = lens.requirement_row(q, {})
        assert len(row["cites"]) == len(q.sources)
        for c, s in zip(row["cites"], q.sources, strict=True):
            # The link opens the source's own document, or the law's page on the same register.
            assert c["href"].split("#")[0] == str(s.url).split("#")[0] or c["how"] == "law"
            assert c["linkText"]
            assert len(c["quote"]) <= lens.QUOTE_CHARS + 2
