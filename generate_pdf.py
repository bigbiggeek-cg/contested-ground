#!/usr/bin/env python3
"""Generate a PDF book from Contested Ground course content."""

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Color scheme from brand
COLORS = {
    'navy': HexColor('#0B1F33'),
    'navy_mid': HexColor('#142C46'),
    'navy_line': HexColor('#2A4361'),
    'accent': HexColor('#D2571E'),
    'accent_bright': HexColor('#F2894E'),
    'text': HexColor('#F5EFE6'),
    'text_mute': HexColor('#8CA2BC'),
    'text_dim': HexColor('#5E7591'),
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


def extract_lessons_from_html(html_path):
    """Extract lesson data from Lesson Page.dc.html."""
    with open(html_path, 'r') as f:
        content = f.read()

    lessons = {}

    # Find the LESSONS_DATA object block
    start = content.find('const LESSONS_DATA = {')
    if start == -1:
        return lessons

    # Find matching closing brace
    depth = 0
    pos = start + len('const LESSONS_DATA = ')
    while pos < len(content):
        if content[pos] == '{':
            depth += 1
        elif content[pos] == '}':
            depth -= 1
            if depth == 0:
                break
        pos += 1

    data_block = content[start + len('const LESSONS_DATA = '):pos + 1]

    # Extract each lesson by its numeric key
    lesson_pattern = r"'(\d{2})':\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"

    for match in re.finditer(lesson_pattern, data_block, re.DOTALL):
        lesson_id = match.group(1)
        lesson_block = match.group(2)

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

    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=44,
        bold=True,
        textColor=COLORS['accent'],
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        letterSpacing=2,
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=COLORS['text_mute'],
        alignment=TA_CENTER,
        spaceAfter=24,
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=28,
        bold=True,
        textColor=COLORS['accent'],
        spaceAfter=12,
        spaceBefore=24,
        fontName='Helvetica-Bold',
        pageBreakBefore=True,
    )

    lesson_style = ParagraphStyle(
        'LessonTitle',
        parent=styles['Normal'],
        fontSize=18,
        bold=True,
        textColor=COLORS['accent_bright'],
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    )

    lesson_meta_style = ParagraphStyle(
        'LessonMeta',
        parent=styles['Normal'],
        fontSize=9,
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
    for domain_num in DOMAIN_ORDER:
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
                    'H3', parent=styles['Normal'], fontSize=13, bold=True,
                    textColor=COLORS['accent_bright'], spaceAfter=10, spaceBefore=10,
                )))

            if 'body' in lesson:
                for para in lesson['body']:
                    story.append(Paragraph(para, body_style))

            # Why section
            if 'whyHeading' in lesson:
                story.append(Paragraph(lesson['whyHeading'], ParagraphStyle(
                    'H3', parent=styles['Normal'], fontSize=13, bold=True,
                    textColor=COLORS['accent_bright'], spaceAfter=10, spaceBefore=10,
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
