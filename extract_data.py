#!/usr/bin/env python3
"""Extract lesson and deep dive data from HTML files."""

import re
import json
import sys

def extract_js_object(content, var_name):
    """Extract a JavaScript object by variable name."""
    pattern = rf'const {var_name}\s*=\s*(\{{.*?^\}};)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return None

    js_code = match.group(1).rstrip(';')

    # Convert JS object notation to valid JSON by replacing single quotes carefully
    json_str = js_code

    # Handle quoted strings - replace single quotes with double quotes
    # but be careful with apostrophes in text
    def quote_replacer(text):
        # Split by colons to identify keys vs values
        result = []
        in_string = False
        string_char = None
        i = 0
        while i < len(text):
            char = text[i]

            if char in ('"', "'") and (i == 0 or text[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                    if char == "'":
                        result.append('"')
                    else:
                        result.append(char)
                elif char == string_char:
                    in_string = False
                    if char == "'":
                        result.append('"')
                    else:
                        result.append(char)
                    string_char = None
                else:
                    result.append(char)
            else:
                result.append(char)
            i += 1
        return ''.join(result)

    json_str = quote_replacer(json_str)

    # Remove trailing commas before closing brackets/braces
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse {var_name}: {e}", file=sys.stderr)
        print(f"First 500 chars: {json_str[:500]}", file=sys.stderr)
        return None

def main():
    # Read HTML files
    with open('Lesson Page.dc.html', 'r') as f:
        lesson_html = f.read()

    with open('Deep Dive Page.dc.html', 'r') as f:
        deepdive_html = f.read()

    lessons = extract_js_object(lesson_html, 'LESSONS_DATA')
    deepdives = extract_js_object(deepdive_html, 'DEEP_DIVES_DATA')

    # Save as JSON for easier processing
    data = {
        'lessons': lessons,
        'deepdives': deepdives,
    }

    with open('course_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Extracted data saved to course_data.json")
    if lessons:
        print(f"  Lessons: {len(lessons)}")
    if deepdives:
        print(f"  Deep Dives: {len(deepdives)}")

if __name__ == '__main__':
    main()
