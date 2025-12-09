#!/usr/bin/env python
"""
Comprehensive Test Suite for Record Matcher
Tests core functionality and identifies runtime issues
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import core
    from core import (
        validate_path, validate_date, validate_chqno, validate_amount,
        format_chqNo, TableSnapshot, JsonDataLoader
    )
except ImportError as e:
    print(f"ERROR: Cannot import core module: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)


class TestValidationFunctions(unittest.TestCase):
    """Test validation utility functions"""
    
    def test_validate_path_valid_xls(self):
        """Test path validation with valid .xls file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self.assertTrue(validate_path(tmp_path))
        finally:
            os.unlink(tmp_path)
    
    def test_validate_path_valid_xlsx(self):
        """Test path validation with valid .xlsx file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self.assertTrue(validate_path(tmp_path))
        finally:
            os.unlink(tmp_path)
    
    def test_validate_path_invalid_extension(self):
        """Test path validation with invalid extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self.assertFalse(validate_path(tmp_path))
        finally:
            os.unlink(tmp_path)
    
    def test_validate_path_nonexistent(self):
        """Test path validation with non-existent file"""
        self.assertFalse(validate_path('/nonexistent/file.xls'))
    
    def test_validate_path_empty(self):
        """Test path validation with empty path"""
        self.assertFalse(validate_path(''))
        self.assertFalse(validate_path(None))
    
    def test_validate_date_valid(self):
        """Test date validation with valid dates"""
        self.assertTrue(validate_date('01/01/21'))
        self.assertTrue(validate_date('31/12/99'))
        self.assertTrue(validate_date('15/06/20'))
    
    def test_validate_date_invalid(self):
        """Test date validation with invalid dates"""
        self.assertFalse(validate_date('32/01/21'))  # Invalid day
        self.assertFalse(validate_date('01/13/21'))  # Invalid month
        self.assertFalse(validate_date('2021-01-01'))  # Wrong format
        self.assertFalse(validate_date('not a date'))
    
    def test_validate_chqno_valid(self):
        """Test cheque number validation with valid numbers"""
        self.assertTrue(validate_chqno('123456'))
        self.assertTrue(validate_chqno('000001'))
        self.assertTrue(validate_chqno('999999999999999'))  # 15 digits
    
    def test_validate_chqno_invalid(self):
        """Test cheque number validation with invalid numbers"""
        self.assertFalse(validate_chqno('abc123'))  # Contains letters
        self.assertFalse(validate_chqno('1234567890123456'))  # Too long (16 digits)
        self.assertFalse(validate_chqno(''))  # Empty
    
    def test_validate_amount_valid(self):
        """Test amount validation with valid amounts"""
        self.assertTrue(validate_amount('100'))
        self.assertTrue(validate_amount('100.50'))
        self.assertTrue(validate_amount('0'))
        self.assertTrue(validate_amount('0.01'))
    
    def test_validate_amount_invalid(self):
        """Test amount validation with invalid amounts"""
        self.assertFalse(validate_amount('-100'))  # Negative
        self.assertFalse(validate_amount('abc'))  # Not a number
        self.assertFalse(validate_amount(''))  # Empty
    
    def test_format_chqno(self):
        """Test cheque number formatting"""
        self.assertEqual(format_chqNo('123'), '0000000000000123')
        self.assertEqual(format_chqNo('1234567890'), '0000001234567890')
        self.assertEqual(len(format_chqNo('1')), 16)


class TestJsonDataLoader(unittest.TestCase):
    """Test JSON data loading"""
    
    def setUp(self):
        """Create temporary data.json for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.temp_dir, 'test_data.json')
        
        test_data = {
            "Years": [
                {"name": "2020", "value": "2020"},
                {"name": "2021", "value": "2021"}
            ],
            "Banks": [
                {"name": "HDFC", "value": "hdfc"},
                {"name": "ICICI", "value": "icici"}
            ],
            "Companies": [
                {"name": "Gokul", "value": "gokul"}
            ],
            "Months": [
                {"name": "January", "value": "january"},
                {"name": "February", "value": "february"}
            ]
        }
        
        import json
        with open(self.json_path, 'w') as f:
            json.dump(test_data, f)
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_json_data(self):
        """Test loading JSON data"""
        loader = JsonDataLoader(self.json_path)
        
        self.assertEqual(loader.get_years(), ['2020', '2021'])
        self.assertEqual(loader.get_banks(), ['hdfc', 'icici'])
        self.assertEqual(loader.get_companies(), ['gokul'])
        self.assertEqual(loader.get_months(), ['january', 'february'])
    
    def test_load_nonexistent_json(self):
        """Test loading non-existent JSON file"""
        loader = JsonDataLoader('/nonexistent/data.json')
        
        # Should not crash, but return empty lists
        self.assertEqual(loader.get_years(), [])
        self.assertEqual(loader.get_banks(), [])


class TestTableSnapshot(unittest.TestCase):
    """Test TableSnapshot class"""
    
    def test_create_snapshot_mode2(self):
        """Test creating snapshot with all parameters"""
        master_table = [
            {
                'Bank Date': '01/01/2021',
                'Bank Narration': 'Test',
                'Chq No': '123456',
                'Party Name': 'Test Party',
                'Infi Date': '02/01/2021',
                'Credit': '1000',
                'Debit': '',
                'Closing Balance': '5000',
                'meta': ''
            }
        ]
        
        snapshot = TableSnapshot(
            'gokul', 'january', '2021', 'hdfc',
            master_table, [0], '/path/to/export.xls'
        )
        
        self.assertEqual(snapshot.get_company(), 'gokul')
        self.assertEqual(snapshot.get_month(), 'january')
        self.assertEqual(snapshot.get_year(), '2021')
        self.assertEqual(snapshot.get_bank(), 'hdfc')
        self.assertEqual(len(snapshot.get_master_table()), 1)
        self.assertEqual(snapshot.get_master_selected_rows(), [0])
    
    def test_snapshot_update_selected_rows(self):
        """Test updating selected rows"""
        snapshot = TableSnapshot(
            'gokul', 'january', '2021', 'hdfc',
            [], [], None
        )
        
        snapshot.set_master_selected_rows([1, 2, 3])
        self.assertEqual(snapshot.get_master_selected_rows(), [1, 2, 3])
        
        # Should update last edited time
        self.assertIsNotNone(snapshot.get_last_edited_time())


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common scenarios"""
    
    def test_cheque_number_formatting_consistency(self):
        """Test that cheque numbers are formatted consistently"""
        test_numbers = ['1', '123', '123456789', '000123']
        
        for num in test_numbers:
            formatted = format_chqNo(num)
            # All should be 16 characters
            self.assertEqual(len(formatted), 16)
            # All should be numeric
            self.assertTrue(formatted.isdigit())
            # Should preserve the original number at the end
            self.assertTrue(formatted.endswith(num))
    
    def test_validation_pipeline(self):
        """Test complete validation pipeline"""
        # Create valid test file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Validate path
            self.assertTrue(validate_path(tmp_path))
            
            # Validate associated data
            self.assertTrue(validate_date('01/01/21'))
            self.assertTrue(validate_chqno('123456'))
            self.assertTrue(validate_amount('1000.50'))
            
        finally:
            os.unlink(tmp_path)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_empty_inputs(self):
        """Test handling of empty inputs"""
        self.assertFalse(validate_path(''))
        self.assertFalse(validate_chqno(''))
        self.assertFalse(validate_amount(''))
    
    def test_none_inputs(self):
        """Test handling of None inputs"""
        self.assertFalse(validate_path(None))
    
    def test_very_large_amounts(self):
        """Test validation of very large amounts"""
        self.assertTrue(validate_amount('999999999.99'))
        self.assertTrue(validate_amount('1000000000'))
    
    def test_boundary_cheque_numbers(self):
        """Test cheque number at boundaries"""
        # Maximum valid length (15 digits)
        self.assertTrue(validate_chqno('1' * 15))
        # One more than maximum (16 digits) - should fail
        self.assertFalse(validate_chqno('1' * 16))


def run_tests(verbosity=2):
    """Run all tests"""
    print("=" * 80)
    print("RECORD MATCHER - AUTOMATED TEST SUITE")
    print("=" * 80)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValidationFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestJsonDataLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestTableSnapshot))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
