# Used Copilot to convert from Java to Python from https://github.com/onozaty/junit-xml2csv Copyright (c) 2024 onozaty
import sys
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_testcase(testcase_elem):
    class_name = testcase_elem.attrib.get('classname', '')
    name = testcase_elem.attrib.get('name', '')
    time = testcase_elem.attrib.get('time', '')
    result = 'PASSED'
    for child in testcase_elem:
        if child.tag == 'skipped':
            result = 'SKIPPED'
        elif child.tag == 'failure':
            result = 'FAILURE'
        elif child.tag == 'error':
            result = 'ERROR'
    return class_name, name, time, result

def parse_testsuite(suite_elem):
    suite_name = suite_elem.attrib.get('name', '')
    timestamp = suite_elem.attrib.get('timestamp', '')
    testcases = []
    for testcase in suite_elem.findall('testcase'):
        class_name, name, time, result = parse_testcase(testcase)
        testcases.append({
            'suite_name': suite_name,
            'timestamp': timestamp,
            'class_name': class_name,
            'name': name,
            'time': time,
            'result': result
        })
    return testcases

def parse_testsuites(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Warning: Skipping file '{xml_path}' - not valid JUnit XML: {e}")
        return []
    testcases = []
    if root.tag == 'testsuites':
        for suite in root.findall('testsuite'):
            testcases.extend(parse_testsuite(suite))
    elif root.tag == 'testsuite':
        testcases.extend(parse_testsuite(root))
    else:
        print(f"Warning: Unexpected root tag '{root.tag}' in file '{xml_path}'")
    return testcases

def main(xml_dir, csv_path):
    rows = []
    xml_files = list(Path(xml_dir).rglob('*.xml'))
    print(f"Found {len(xml_files)} XML file(s).")
    for xml_file in xml_files:
        rows.extend(parse_testsuites(xml_file))

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'TestSuite: Name',
                'TestSuite: Timestamp',
                'TestCase: ClassName',
                'TestCase: Name',
                'TestCase: Time',
                'TestCase: Result'
            ])
            for row in rows:
                writer.writerow([
                    row['suite_name'],
                    row['timestamp'],
                    row['class_name'],
                    row['name'],
                    row['time'],
                    row['result']
                ])
    except OSError as e:
        print(f"Error: Could not open or write to CSV file '{csv_path}': {e}")
        sys.exit(2)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python junit_xml_to_csv.py <xml_dir> <output_csv>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
