#!/usr/bin/env python3
"""Iterative build: re-render until the TOC's page numbers match reality."""
import md2pdf as M

SRC, OUT = 'combined.md', 'WatchaMe_Operations_Guide.pdf'
TITLE = 'WatchaMe Operations Guide'
SUB   = ('Operating a self-updating Kodi add-on repository, and provisioning '
         'a Fire TV Stick 4K from it.')
FOOT  = 'WatchaMe Operations Guide'
md = open(SRC).read()

def render_pass(out):
    M.CAPTURED.clear()
    M.render(md, out, TITLE, SUB, FOOT)
    return [(t, p) for (lvl, t, p) in M.CAPTURED if lvl == 0]

M.TOC_DATA.clear()
seed = render_pass('/tmp/_pass0.pdf')
M.TOC_DATA.extend((t, 0) for t, _ in seed)

for attempt in range(1, 6):
    actual = render_pass(OUT)
    listed = dict(M.TOC_DATA)
    bad = [t for t, p in actual if listed.get(t) != p]
    if not bad:
        print('converged after %d pass(es): %d TOC entries, all page numbers correct'
              % (attempt, len(actual)))
        break
    M.TOC_DATA.clear(); M.TOC_DATA.extend(actual)
    print('pass %d: %d entr(ies) off, retrying' % (attempt, len(bad)))
else:
    raise SystemExit('TOC did not converge')
