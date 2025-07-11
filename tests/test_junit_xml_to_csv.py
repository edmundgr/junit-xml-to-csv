"""Unit tests for junit_xml_to_csv"""
# pylint: disable=wrong-import-position
import sys
import os
import unittest
import tempfile
import xml.etree.ElementTree as ET
import csv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import junit_xml_to_csv

class TestJunitXmlToCsv(unittest.TestCase):
    """Unit Test class for junit_xml_to_csv"""
    def test_parse_testcase_passed(self):
        """Test a parse_testcase() for passed test"""
        elem = ET.Element('testcase', classname='MyClass', name='test1', time='0.01')
        result = junit_xml_to_csv.parse_testcase(elem)
        self.assertEqual(result, ('MyClass', 'test1', '0.01', 'PASSED'))

    def test_parse_testcase_skipped(self):
        """Test a parse_testcase() for skipped test"""
        elem = ET.Element('testcase', classname='MyClass', name='test2', time='0.02')
        ET.SubElement(elem, 'skipped')
        result = junit_xml_to_csv.parse_testcase(elem)
        self.assertEqual(result, ('MyClass', 'test2', '0.02', 'SKIPPED'))

    def test_parse_testcase_failure(self):
        """Test parse_testcase() for failed test"""
        elem = ET.Element('testcase', classname='MyClass', name='test3', time='0.03')
        ET.SubElement(elem, 'failure')
        result = junit_xml_to_csv.parse_testcase(elem)
        self.assertEqual(result, ('MyClass', 'test3', '0.03', 'FAILURE'))

    def test_parse_testcase_error(self):
        """Test parse_testcase() for error test"""
        elem = ET.Element('testcase', classname='MyClass', name='test4', time='0.04')
        ET.SubElement(elem, 'error')
        result = junit_xml_to_csv.parse_testcase(elem)
        self.assertEqual(result, ('MyClass', 'test4', '0.04', 'ERROR'))

    def test_parse_testsuite(self):
        """Test parse_testsuite() with testsuite root and 2 test cases"""
        suite = ET.Element('testsuite', name='Suite1', timestamp='2024-06-01T12:00:00')
        ET.SubElement(suite, 'testcase', classname='ClassA', name='testA', time='0.1')
        tc2 = ET.SubElement(suite, 'testcase', classname='ClassB', name='testB', time='0.2')
        ET.SubElement(tc2, 'failure')
        result = junit_xml_to_csv.parse_testsuite(suite)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['suite_name'], 'Suite1')
        self.assertEqual(result[0]['timestamp'], '2024-06-01T12:00:00')
        self.assertEqual(result[0]['class_name'], 'ClassA')
        self.assertEqual(result[0]['name'], 'testA')
        self.assertEqual(result[0]['time'], '0.1')
        self.assertEqual(result[0]['result'], 'PASSED')
        self.assertEqual(result[1]['result'], 'FAILURE')

    def test_parse_testsuites_testsuites_root(self):
        """Test parse_testsuite() with testsuites root and 2 testsuites"""
        root = ET.Element('testsuites')
        suite1 = ET.SubElement(root, 'testsuite', name='Suite1', timestamp='2024-06-01T12:00:00')
        ET.SubElement(suite1, 'testcase', classname='ClassA', name='testA', time='0.1')
        suite2 = ET.SubElement(root, 'testsuite', name='Suite2', timestamp='2024-06-01T13:00:00')
        ET.SubElement(suite2, 'testcase', classname='ClassB', name='testB', time='0.2')
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.xml') as tmp:
            ET.ElementTree(root).write(tmp.name)
            result = junit_xml_to_csv.parse_testsuites(tmp.name)
        os.unlink(tmp.name)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['suite_name'], 'Suite1')
        self.assertEqual(result[1]['suite_name'], 'Suite2')

    def test_parse_testsuites_testsuite_root(self):
        """Test parse_testsuite() with testsuite root and 1 testcase"""
        suite = ET.Element('testsuite', name='Suite1', timestamp='2024-06-01T12:00:00')
        ET.SubElement(suite, 'testcase', classname='ClassA', name='testA', time='0.1')
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.xml') as tmp:
            ET.ElementTree(suite).write(tmp.name)
            result = junit_xml_to_csv.parse_testsuites(tmp.name)
        os.unlink(tmp.name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['suite_name'], 'Suite1')

    def test_main_creates_csv(self):
        """Test main() with a testsuite root file"""
        # Create a temporary XML file
        suite = ET.Element('testsuite', name='Suite1', timestamp='2024-06-01T12:00:00')
        ET.SubElement(suite, 'testcase', classname='ClassA', name='testA', time='0.1')
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = os.path.join(tmpdir, 'test.xml')
            ET.ElementTree(suite).write(xml_path)
            csv_path = os.path.join(tmpdir, 'output.csv')
            junit_xml_to_csv.main(tmpdir, csv_path)
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                self.assertEqual(rows[0], [
                    'TestSuite: Name',
                    'TestSuite: Timestamp',
                    'TestCase: ClassName',
                    'TestCase: Name',
                    'TestCase: Time',
                    'TestCase: Result'
                ])
                self.assertEqual(rows[1][0], 'Suite1')
                self.assertEqual(rows[1][2], 'ClassA')
                self.assertEqual(rows[1][3], 'testA')
                self.assertEqual(rows[1][5], 'PASSED')

if __name__ == '__main__':
    unittest.main()
