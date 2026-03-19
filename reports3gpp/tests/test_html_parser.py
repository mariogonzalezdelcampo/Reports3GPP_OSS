"""
Tests for HTML parser functionality.
"""
import unittest
from unittest.mock import patch, Mock
from src.html_parser import find_zip_file_in_html

class TestHTMLParser(unittest.TestCase):
    
    @patch('src.html_parser.requests.get')
    def test_find_zip_file_in_html(self, mock_get):
        # Mock HTML response with a ZIP file link
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <body>
            <a href="/ftp/tsg_sa/WG5_TM/TSGS5_165/TDoc_List_Meeting165.zip">TDoc_List_Meeting165.zip</a>
            <a href="/ftp/tsg_sa/WG5_TM/TSGS5_165/other_file.txt">Other file</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test finding ZIP file
        result = find_zip_file_in_html("https://www.3gpp.org/ftp/tsg_sa/WG5_TM/TSGS5_165/Tdoclist", 165)
        self.assertEqual(result, "TDoc_List_Meeting165.zip")
    
    @patch('src.html_parser.requests.get')
    def test_find_zip_file_in_html_no_match(self, mock_get):
        # Mock HTML response with no ZIP file links
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <body>
            <a href="/ftp/tsg_sa/WG5_TM/TSGS5_165/other_file.txt">Other file</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test finding ZIP file when none exists
        result = find_zip_file_in_html("https://www.3gpp.org/ftp/tsg_sa/WG5_TM/TSGS5_165/Tdoclist", 165)
        self.assertIsNone(result)
    
    @patch('src.html_parser.requests.get')
    def test_find_zip_file_in_html_fallback(self, mock_get):
        # Mock HTML response with ZIP file that doesn't match exact pattern but contains meeting number
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <body>
            <a href="/ftp/tsg_sa/WG5_TM/TSGS5_165/Meeting165_document.zip">Meeting165_document.zip</a>
            <a href="/ftp/tsg_sa/WG5_TM/TSGS5_165/other_file.txt">Other file</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test fallback method
        result = find_zip_file_in_html("https://www.3gpp.org/ftp/tsg_sa/WG5_TM/TSGS5_165/Tdoclist", 165)
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith(".zip"))

if __name__ == '__main__':
    unittest.main()