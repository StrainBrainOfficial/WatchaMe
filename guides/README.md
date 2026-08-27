# Guides

Source for the WatchaMe Operations Guide.

    guide1.md           Book One - running the repository
    guide2.md           Book Two - provisioning a Fire TV Stick 4K
    combined.md         GENERATED - the two books plus front matter
    md2pdf.py           Markdown -> PDF renderer
    build_combined.py   Two-pass build; verifies every TOC page number

Rebuild after editing either book:

    python3 build_combined.py

It renders once to learn where headings land, then re-renders with a real
table of contents and asserts that every listed page number matches reality.
Output: `WatchaMe_Operations_Guide.pdf`.
