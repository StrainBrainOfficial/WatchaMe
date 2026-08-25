#!/usr/bin/env python3
"""Minimal markdown -> PDF renderer (reportlab Platypus) for technical guides.

Supports: h1-h3, paragraphs, bullet/numbered lists, fenced code (splits across
pages), tables, callouts (>), rules, \\pagebreak, \\book dividers, \\toc.
"""
import re, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                               Table, TableStyle, PageBreak, HRFlowable)

ACCENT  = colors.HexColor('#1f4e79')
ACCENT2 = colors.HexColor('#2e6da4')
CODEBG  = colors.HexColor('#f4f5f7')
NOTEBG  = colors.HexColor('#fdf6e3')
NOTEBRD = colors.HexColor('#e0c98a')
GREY    = colors.HexColor('#5a5a5a')

ss = getSampleStyleSheet()
S = {
 'title':   ParagraphStyle('title', parent=ss['Title'], fontName='Helvetica-Bold',
                           fontSize=26, leading=31, textColor=ACCENT, spaceAfter=6),
 'subtitle':ParagraphStyle('subtitle', parent=ss['Normal'], fontName='Helvetica',
                           fontSize=12.5, leading=17, textColor=GREY, alignment=TA_LEFT, spaceAfter=18),
 'h1':      ParagraphStyle('h1', parent=ss['Heading1'], fontName='Helvetica-Bold', fontSize=17,
                           leading=21, textColor=ACCENT, spaceBefore=18, spaceAfter=8),
 'h2':      ParagraphStyle('h2', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=13,
                           leading=17, textColor=ACCENT2, spaceBefore=13, spaceAfter=6),
 'h3':      ParagraphStyle('h3', parent=ss['Heading3'], fontName='Helvetica-Bold', fontSize=11,
                           leading=14, textColor=colors.HexColor('#333333'), spaceBefore=10, spaceAfter=4),
 'body':    ParagraphStyle('body', parent=ss['Normal'], fontName='Helvetica', fontSize=9.8,
                           leading=14.2, spaceAfter=7),
 'bullet':  ParagraphStyle('bullet', parent=ss['Normal'], fontName='Helvetica', fontSize=9.8,
                           leading=13.6, spaceAfter=3),
 'code':    ParagraphStyle('code', parent=ss['Code'], fontName='Courier', fontSize=8.1,
                           leading=10.6, textColor=colors.HexColor('#1b1b1b')),
 'note':    ParagraphStyle('note', parent=ss['Normal'], fontName='Helvetica', fontSize=9.3,
                           leading=13, textColor=colors.HexColor('#4a3c10')),
 'book':    ParagraphStyle('book', parent=ss['Title'], fontName='Helvetica-Bold', fontSize=30,
                           leading=36, textColor=ACCENT, spaceBefore=150, spaceAfter=10),
 'booksub': ParagraphStyle('booksub', parent=ss['Normal'], fontName='Helvetica', fontSize=12,
                           leading=17, textColor=GREY, alignment=1, spaceAfter=8),
 'th':      ParagraphStyle('th', parent=ss['Normal'], fontName='Helvetica-Bold', fontSize=8.8,
                           leading=11.5, textColor=colors.white),
 'td':      ParagraphStyle('td', parent=ss['Normal'], fontName='Helvetica', fontSize=8.8, leading=11.5),
}

CAPTURED = []   # (level, text, page) recorded during a render pass
TOC_DATA = []   # (text, page) supplied on the final pass


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline(t):
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8.9" backColor="#eef0f3">\1</font>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<link href="\2" color="#1f4e79"><u>\1</u></link>', t)
    return t


def code_block(lines):
    """One table row per source line so long blocks split across pages."""
    data = [[Paragraph(esc(l).replace(' ', '&nbsp;') or '&nbsp;', S['code'])]
            for l in lines] or [[Paragraph('&nbsp;', S['code'])]]
    t = Table(data, colWidths=[6.55*inch], splitByRow=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CODEBG),
        ('LINEBEFORE',(0,0),(0,-1),2.2,colors.HexColor('#b9c0ca')),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),0.6),('BOTTOMPADDING',(0,0),(-1,-1),0.6),
        ('TOPPADDING',(0,0),(-1,0),6),('BOTTOMPADDING',(0,-1),(-1,-1),6),
    ]))
    return t


def note_block(lines):
    p = Paragraph('<br/>'.join(inline(l) for l in lines), S['note'])
    t = Table([[p]], colWidths=[6.55*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),NOTEBG),
        ('BOX',(0,0),(-1,-1),0.6,NOTEBRD),
        ('LINEBEFORE',(0,0),(0,-1),2.5,colors.HexColor('#d4a72c')),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    return t


def make_table(rows):
    head, body = rows[0], rows[1:]
    ncol = len(head)
    data = [[Paragraph(inline(c), S['th']) for c in head]]
    for r in body:
        r = (r + ['']*ncol)[:ncol]
        data.append([Paragraph(inline(c), S['td']) for c in r])
    total = 6.55*inch
    # A narrow leading column ("#" with short numeric cells) should not take an
    # equal share -- it starves the columns carrying real content.
    narrow_first = (head[0].strip() in ('#', 'No', 'Step') or
                    all(len(r[0].strip()) <= 3 for r in body if r))
    widths = [total/ncol]*ncol
    if ncol == 2:   widths = [total*0.34, total*0.66]
    elif ncol == 3: widths = [total*0.26, total*0.30, total*0.44]
    elif ncol == 4: widths = [total*0.20, total*0.22, total*0.22, total*0.36]
    if narrow_first and ncol >= 3:
        lead = 0.05
        rest = [w/total for w in widths[1:]]
        scale = (1.0 - lead)/sum(rest)
        widths = [total*lead] + [total*r*scale for r in rest]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),ACCENT),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f2f5f8')]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#c8ced6')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    return t


def toc_flowables():
    out = [PageBreak(),
           Paragraph('Contents', S['h1']),
           HRFlowable(width='100%', thickness=0.8, color=ACCENT2, spaceAfter=9)]
    rows = [[Paragraph(esc(t), ParagraphStyle('tocrow', fontName='Helvetica-Bold',
                                              fontSize=9.6, leading=13.4,
                                              textColor=colors.HexColor('#22303f'))),
             Paragraph('%d' % p, ParagraphStyle('tocpg', fontName='Helvetica',
                                                fontSize=9.6, leading=13.4,
                                                alignment=2, textColor=GREY))]
            for t, p in TOC_DATA]
    tt = Table(rows, colWidths=[6.05*inch, 0.5*inch], splitByRow=1)
    tt.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),1.6),('BOTTOMPADDING',(0,0),(-1,-1),1.6),
        ('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#e2e6ea')),
    ]))
    out.append(tt)
    return out


def render(md, out, title, subtitle, footer_text):
    story = []
    story.append(Paragraph(esc(title), S['title']))
    story.append(HRFlowable(width='100%', thickness=2, color=ACCENT, spaceAfter=10))
    story.append(Paragraph(inline(subtitle), S['subtitle']))
    md = md.replace('\\toc', '\\TOCMARK')
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if st == '\\TOCMARK':
            if TOC_DATA:
                story.extend(toc_flowables())
            i += 1; continue
        m_book = re.match(r'^\\book\s+(.*?)\s*\|\|\s*(.*)$', st)
        if m_book:
            story.append(PageBreak())
            p = Paragraph(esc(m_book.group(1)), S['book'])
            p._toc = (0, m_book.group(1))
            story.append(p)
            story.append(HRFlowable(width='60%', thickness=2.5, color=ACCENT,
                                    spaceAfter=12, hAlign='CENTER'))
            story.append(Paragraph(esc(m_book.group(2)), S['booksub']))
            story.append(PageBreak())
            i += 1; continue
        if st == '\\pagebreak':
            story.append(PageBreak()); i += 1; continue
        if st.startswith('```'):
            i += 1; buf = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            story.append(Spacer(1,3)); story.append(code_block(buf)); story.append(Spacer(1,8))
            continue
        if st.startswith('> '):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('> '):
                buf.append(lines[i].strip()[2:]); i += 1
            story.append(Spacer(1,3)); story.append(note_block(buf)); story.append(Spacer(1,8))
            continue
        if st.startswith('|') and i+1 < len(lines) and re.match(r'^\|[\s:\-\|]+\|$', lines[i+1].strip()):
            def cells(l): return [c.strip() for c in l.strip().strip('|').split('|')]
            rows = [cells(lines[i])]; i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(cells(lines[i])); i += 1
            story.append(Spacer(1,3)); story.append(make_table(rows)); story.append(Spacer(1,9))
            continue
        if re.match(r'^---+$', st):
            story.append(HRFlowable(width='100%', thickness=0.7,
                                    color=colors.HexColor('#c8ced6'), spaceBefore=8, spaceAfter=8))
            i += 1; continue
        m = re.match(r'^(#{1,3})\s+(.*)$', st)
        if m:
            lvl = len(m.group(1))
            para = Paragraph(inline(m.group(2)), S['h%d' % lvl])
            if lvl <= 2:
                para._toc = (lvl - 1, re.sub(r'<[^>]+>', '', inline(m.group(2))))
            story.append(para)
            if lvl == 1:
                story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT2, spaceAfter=7))
            i += 1; continue
        if re.match(r'^(\d+)\.\s+', st) or st.startswith('- ') or st.startswith('* '):
            items, ordered = [], bool(re.match(r'^(\d+)\.\s+', st))
            while i < len(lines):
                s2, raw = lines[i].strip(), lines[i]
                if not s2:
                    if i+1 < len(lines) and (lines[i+1].startswith('    ') or lines[i+1].startswith('\t')):
                        i += 1; continue
                    break
                m2 = re.match(r'^(\d+)\.\s+(.*)$', s2)
                m3 = re.match(r'^[-*]\s+(.*)$', s2)
                indented = raw.startswith('    ') or raw.startswith('\t')
                if m2 and not indented:   items.append(('i', m2.group(2)))
                elif m3 and not indented: items.append(('i', m3.group(1)))
                elif indented and m3:     items.append(('s', m3.group(1)))
                elif items:               items[-1] = (items[-1][0], items[-1][1] + ' ' + s2)
                else:                     break
                i += 1
            n = 0
            for kind, txt in items:
                if kind == 'i':
                    n += 1
                    bullet = ('%d.' % n) if ordered else '\u2022'
                    tb = Table([[Paragraph('<b>%s</b>' % bullet if ordered else bullet, S['bullet']),
                                 Paragraph(inline(txt), S['bullet'])]],
                               colWidths=[0.30*inch, 6.25*inch])
                else:
                    tb = Table([['', Paragraph('\u2013 ' + inline(txt), S['bullet'])]],
                               colWidths=[0.62*inch, 5.93*inch])
                tb.setStyle(TableStyle([
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                    ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),2.5),
                ]))
                story.append(tb)
            story.append(Spacer(1,6))
            continue
        if not st:
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r'^(#{1,3}\s|```|\||>\s|-\s|\*\s|\d+\.\s|---+$|\\pagebreak|\\book|\\TOCMARK)',
                lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        if buf:
            story.append(Paragraph(inline(' '.join(buf)), S['body']))

    def deco(canv, doc):
        canv.saveState()
        canv.setFont('Helvetica', 7.5)
        canv.setFillColor(GREY)
        canv.drawString(0.9*inch, 0.55*inch, footer_text)
        canv.drawRightString(7.6*inch, 0.55*inch, 'Page %d' % doc.page)
        canv.setStrokeColor(colors.HexColor('#c8ced6')); canv.setLineWidth(0.5)
        canv.line(0.9*inch, 0.72*inch, 7.6*inch, 0.72*inch)
        canv.restoreState()

    class Doc(BaseDocTemplate):
        def __init__(self, *a, **kw):
            BaseDocTemplate.__init__(self, *a, **kw)
            frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='normal')
            self.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=deco)])
            self._bm = 0

        def afterFlowable(self, flowable):
            toc = getattr(flowable, '_toc', None)
            if not toc:
                return
            level, text = toc
            key = 'bm%d' % self._bm
            self._bm += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
            CAPTURED.append((level, text, self.page))

    doc = Doc(out, pagesize=LETTER,
              leftMargin=0.9*inch, rightMargin=0.95*inch,
              topMargin=0.85*inch, bottomMargin=0.85*inch,
              title=title, author='Kodi Guides')
    doc.build(story)
    print('wrote', out)


if __name__ == '__main__':
    src, out, title, subtitle, footer = sys.argv[1:6]
    with open(src) as f:
        render(f.read(), out, title, subtitle, footer)
