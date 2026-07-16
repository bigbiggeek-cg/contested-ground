#!/usr/bin/env python3
"""Generate a PDF book from Contested Ground course content."""

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Print palette: dark text on white page (the site's light-on-navy colors
# are illegible on a white PDF background, so this is a distinct print scheme
# using the same brand hues, darkened/adjusted for contrast on paper).
COLORS = {
    'navy': HexColor('#0B1F33'),        # headings, primary text
    'accent': HexColor('#B84A18'),      # darkened burnt orange - passes contrast on white
    'accent_bright': HexColor('#9C3D14'),  # darker still, for body-sized accent text
    'text': HexColor('#1A1A1A'),        # body copy - near-black
    'text_mute': HexColor('#4A4A4A'),   # secondary text
    'text_dim': HexColor('#6B6B6B'),    # tertiary/meta text
    'rule': HexColor('#D8D2C4'),        # divider lines
}

DOMAIN_TITLES = {
    '01': 'Foundations',
    '02': 'Detection & Response',
    '03': 'Cloud & Modern Surface',
    '04': 'Practical Defense & Career',
    '05': 'The Human Element',
    '06': 'Compliance & Governance',
}

DOMAIN_ORDER = ['01', '02', '03', '04', '05', '06']


def find_matching_brace(text, open_pos):
    """Given the index of an opening '{', return the index of its matching '}'."""
    depth = 0
    pos = open_pos
    in_string = False
    string_char = None
    escape_next = False
    while pos < len(text):
        char = text[pos]
        if escape_next:
            escape_next = False
        elif char == '\\':
            escape_next = True
        elif in_string:
            if char == string_char:
                in_string = False
        elif char in ("'", '"'):
            in_string = True
            string_char = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    return -1


def extract_lessons_from_html(html_path):
    """Extract lesson data from Lesson Page.dc.html."""
    with open(html_path, 'r') as f:
        content = f.read()

    lessons = {}

    # Find the LESSONS_DATA object block
    start = content.find('const LESSONS_DATA = {')
    if start == -1:
        return lessons

    obj_open = start + len('const LESSONS_DATA = ')
    obj_close = find_matching_brace(content, obj_open)
    data_block = content[obj_open:obj_close + 1]

    # Find each top-level lesson key ('01', '02', ...) and use brace-depth
    # counting (not regex) to find its block boundaries. Lessons contain a
    # `quiz` array with nested option objects — two levels of nested braces —
    # which a single-level regex silently truncates through, dropping every
    # field that follows (body/whyHeading/closing/takeaways).
    key_pattern = re.compile(r"'(\d{2})':\s*\{")

    for key_match in key_pattern.finditer(data_block):
        lesson_id = key_match.group(1)
        block_open = key_match.end() - 1  # index of the lesson's opening '{'
        block_close = find_matching_brace(data_block, block_open)
        if block_close == -1:
            continue
        lesson_block = data_block[block_open + 1:block_close]

        lesson = {'id': lesson_id}

        # Extract simple string fields
        simple_fields = {
            'domain': r"domain:\s*'(\d{2})'",
            'title': r"title:\s*'([^']*(?:\\'[^']*)*)'",
            'marker': r"marker:\s*'([^']*)'",
            'time': r"time:\s*'([^']*)'",
            'subtitle': r"subtitle:\s*'([^']*(?:\\'[^']*)*)'",
            'coreHeading': r"coreHeading:\s*'([^']*(?:\\'[^']*)*)'",
            'whyHeading': r"whyHeading:\s*'([^']*(?:\\'[^']*)*)'",
        }

        for field_name, field_pattern in simple_fields.items():
            match_field = re.search(field_pattern, lesson_block)
            if match_field:
                val = match_field.group(1).replace("\\'", "'")
                lesson[field_name] = val

        # Extract array fields - be more careful with string extraction
        for array_field in ['intro', 'body', 'closing', 'takeaways']:
            array_pattern = rf"{array_field}:\s*\[(.*?)\](?=\s*[,}}])"
            match_array = re.search(array_pattern, lesson_block, re.DOTALL)
            if match_array:
                items_str = match_array.group(1)
                # Extract quoted strings, handling escaped quotes
                items = []
                current = None
                in_string = False
                escape_next = False
                for char in items_str:
                    if escape_next:
                        if current is not None:
                            current += char
                        escape_next = False
                    elif char == '\\':
                        escape_next = True
                    elif char == "'" and not in_string:
                        in_string = True
                        current = ''
                    elif char == "'" and in_string:
                        in_string = False
                        items.append(current)
                        current = None
                    elif in_string:
                        current += char
                lesson[array_field] = items

        # Extract the optional 'table' field: an array of { a: '...', b: '...' } rows
        table_match = re.search(r"table:\s*\[(.*?)\](?=\s*,\s*(?:body|whyHeading|closing|takeaways|quiz)\s*:)", lesson_block, re.DOTALL)
        if table_match:
            rows_str = table_match.group(1)
            rows = []
            for row_match in re.finditer(r"\{\s*a:\s*'([^']*(?:\\'[^']*)*)',\s*b:\s*'([^']*(?:\\'[^']*)*)'\s*\}", rows_str):
                rows.append((
                    row_match.group(1).replace("\\'", "'"),
                    row_match.group(2).replace("\\'", "'"),
                ))
            if rows:
                lesson['table'] = rows

        lessons[lesson_id] = lesson

    return lessons


def extract_deepdives_from_html(html_path):
    """Extract deep dive data from Deep Dive Page.dc.html."""
    with open(html_path, 'r') as f:
        content = f.read()

    deepdives = {}

    # Find all deepdive entries
    pattern = r"'([^']+)':\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}(?=\s*,\s*'|\s*\}\s*;)"

    for match in re.finditer(pattern, content, re.DOTALL):
        key = match.group(1)
        dd_block = match.group(2)

        dd = {'id': key}

        # Extract simple string fields
        for field in ['index', 'title', 'subtitle']:
            pattern_field = rf"{field}:\s*'([^']*(?:\\'[^']*)*)',"
            match_field = re.search(pattern_field, dd_block)
            if match_field:
                dd[field] = match_field.group(1).replace("\\'", "'")

        # Extract readTime
        match_time = re.search(r"readTime:\s*(\d+)", dd_block)
        if match_time:
            dd['readTime'] = match_time.group(1)

        # Extract takeaways array
        takeaways_pattern = r"takeaways:\s*\[(.*?)\]"
        match_takeaways = re.search(takeaways_pattern, dd_block, re.DOTALL)
        if match_takeaways:
            items_str = match_takeaways.group(1)
            items = re.findall(r"'([^']*(?:\\'[^']*)*)'", items_str)
            dd['takeaways'] = [item.replace("\\'", "'") for item in items]

        deepdives[key] = dd

    return deepdives


def create_pdf(lessons, deepdives, output_path='contested-ground-course.pdf'):
    """Create PDF book from lesson and deepdive data."""
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)

    story = []
    styles = getSampleStyleSheet()

    # Define custom styles. Every style sets `leading` (line height) explicitly —
    # the base 'Normal' style's leading is a fixed 12pt, which is shorter than
    # most of these font sizes and causes text to visually overlap the flowable
    # that follows it if left unset.
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=40,
        leading=46,
        textColor=COLORS['navy'],
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=18,
        leading=24,
        textColor=COLORS['text_mute'],
        alignment=TA_CENTER,
        spaceAfter=24,
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=26,
        leading=32,
        textColor=COLORS['accent'],
        spaceAfter=16,
        spaceBefore=0,
        fontName='Helvetica-Bold',
    )

    lesson_style = ParagraphStyle(
        'LessonTitle',
        parent=styles['Normal'],
        fontSize=17,
        leading=21,
        textColor=COLORS['accent'],
        spaceAfter=4,
        spaceBefore=20,
        fontName='Helvetica-Bold',
    )

    lesson_meta_style = ParagraphStyle(
        'LessonMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=COLORS['text_dim'],
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLORS['text'],
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16,
    )

    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("CONTESTED GROUND", title_style))
    story.append(Paragraph("A Cybersecurity Course for IT Professionals", subtitle_style))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Six Domains • 30 Lessons • Practical, Vendor-Neutral Security Knowledge", body_style))
    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("TABLE OF CONTENTS", section_style))
    story.append(Spacer(1, 0.2*inch))

    toc_style = ParagraphStyle(
        'TOC',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        textColor=COLORS['text'],
        spaceAfter=6,
    )

    # Build TOC by domain
    for domain_num in DOMAIN_ORDER:
        domain_title = DOMAIN_TITLES.get(domain_num, '')
        story.append(Paragraph(f"<b>Domain {domain_num}: {domain_title}</b>", toc_style))

        # List lessons in this domain
        domain_lessons = [l for l in lessons.values() if l.get('domain') == domain_num]
        for lesson in sorted(domain_lessons, key=lambda x: x['id']):
            lesson_title = lesson.get('title', 'Unknown')
            story.append(Paragraph(f"  Lesson {lesson['id']}: {lesson_title}", toc_style))

        story.append(Spacer(1, 0.1*inch))

    story.append(PageBreak())

    # Content: Domains and Lessons
    for i, domain_num in enumerate(DOMAIN_ORDER):
        if i > 0:
            story.append(PageBreak())
        domain_title = DOMAIN_TITLES.get(domain_num, '')
        story.append(Paragraph(f"Domain {domain_num}: {domain_title}", section_style))

        # Get all lessons in this domain
        domain_lessons = [l for l in lessons.values() if l.get('domain') == domain_num]

        for lesson in sorted(domain_lessons, key=lambda x: x['id']):
            # Lesson header
            story.append(Paragraph(f"Lesson {lesson['id']}: {lesson.get('title', '')}", lesson_style))

            # Metadata
            meta_text = f"<b>Difficulty:</b> {lesson.get('marker', '')} • <b>Read time:</b> {lesson.get('time', '')}"
            story.append(Paragraph(meta_text, lesson_meta_style))

            # Subtitle
            if 'subtitle' in lesson:
                story.append(Paragraph(f"<i>{lesson['subtitle']}</i>", body_style))

            # Key Takeaways box
            if 'takeaways' in lesson:
                story.append(Paragraph("<b>Key Takeaways</b>", body_style))
                for takeaway in lesson['takeaways']:
                    story.append(Paragraph(f"• {takeaway}", body_style))
                story.append(Spacer(1, 0.15*inch))

            # Intro
            if 'intro' in lesson:
                for para in lesson['intro']:
                    story.append(Paragraph(para, body_style))

            # Core section
            if 'coreHeading' in lesson:
                story.append(Paragraph(lesson['coreHeading'], ParagraphStyle(
                    'H3', parent=styles['Normal'], fontSize=13, leading=17, fontName='Helvetica-Bold',
                    textColor=COLORS['navy'], spaceAfter=8, spaceBefore=14,
                )))

            # Reference table (e.g. asset/actor pairs, framework comparisons)
            if 'table' in lesson:
                table_label_style = ParagraphStyle(
                    'TableLabel', parent=styles['Normal'], fontSize=10, leading=13,
                    fontName='Helvetica-Bold', textColor=COLORS['accent'],
                )
                table_value_style = ParagraphStyle(
                    'TableValue', parent=styles['Normal'], fontSize=10, leading=13,
                    textColor=COLORS['text'],
                )
                table_rows = [
                    [Paragraph(a, table_label_style), Paragraph(b, table_value_style)]
                    for a, b in lesson['table']
                ]
                tbl = Table(table_rows, colWidths=[1.4*inch, 4.6*inch])
                tbl.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLORS['rule']),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 0.15*inch))

            if 'body' in lesson:
                for para in lesson['body']:
                    story.append(Paragraph(para, body_style))

            # Why section
            if 'whyHeading' in lesson:
                story.append(Paragraph(lesson['whyHeading'], ParagraphStyle(
                    'H3b', parent=styles['Normal'], fontSize=13, leading=17, fontName='Helvetica-Bold',
                    textColor=COLORS['navy'], spaceAfter=8, spaceBefore=14,
                )))

            if 'closing' in lesson:
                for para in lesson['closing']:
                    story.append(Paragraph(para, body_style))

            story.append(Spacer(1, 0.3*inch))

    # Appendix: Deep Dives
    if deepdives:
        story.append(PageBreak())
        story.append(Paragraph("APPENDIX: DEEP DIVES", section_style))

        for key in sorted(deepdives.keys()):
            dd = deepdives[key]
            story.append(Paragraph(f"Deep Dive {dd.get('index', '')}: {dd.get('title', '')}", lesson_style))
            if 'subtitle' in dd:
                story.append(Paragraph(dd['subtitle'], body_style))
            if 'takeaways' in dd:
                story.append(Paragraph("<b>Key Takeaways</b>", body_style))
                for takeaway in dd['takeaways'][:3]:  # Show first 3 takeaways
                    story.append(Paragraph(f"• {takeaway}", body_style))
                story.append(Spacer(1, 0.2*inch))

    # Build PDF
    doc.build(story)
    print(f"PDF created: {output_path}")


def main():
    # Extract data
    print("Extracting lesson data...")
    lessons = extract_lessons_from_html('Lesson Page.dc.html')
    print(f"  Found {len(lessons)} lessons")

    print("Extracting deep dive data...")
    deepdives = extract_deepdives_from_html('Deep Dive Page.dc.html')
    print(f"  Found {len(deepdives)} deep dives")

    if not lessons:
        print("No lessons found. Check HTML file format.", file=sys.stderr)
        return 1

    # Generate PDF
    print("Generating PDF...")
    create_pdf(lessons, deepdives)

    return 0


if __name__ == '__main__':
    sys.exit(main())
