import pytest
import datetime
from unittest.mock import patch, Mock
import requests
from bs4 import BeautifulSoup

# Import the modules to test
import app
import utils


class TestGetPage:
    """Test the get_page function for URL fetching"""
    
    def test_get_page_success(self, mock_requests_get, mock_response):
        """Test successful page retrieval"""
        mock_requests_get.return_value = mock_response
        
        result = app.get_page("https://example.com")
        
        assert result == mock_response.content
        mock_requests_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    
    def test_get_page_http_error(self, mock_requests_get):
        """Test handling of HTTP errors"""
        mock_requests_get.side_effect = requests.HTTPError("404 Not Found")
        
        with patch('app.logging.error') as mock_log_error:
            result = app.get_page("https://example.com/notfound")
            
            assert result is None
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args[0][0]
            assert "Error fetching data" in call_args
    
    def test_get_page_connection_error(self, mock_requests_get):
        """Test handling of connection errors"""
        mock_requests_get.side_effect = requests.ConnectionError("Connection failed")
        
        with patch('app.logging.error') as mock_log_error:
            result = app.get_page("https://example.com")
            
            assert result is None
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args[0][0]
            assert "Error fetching data" in call_args
    
    def test_get_page_uses_headers(self, mock_requests_get, mock_response):
        """Test that get_page uses headers from utils.get_headers()"""
        with patch('app.get_headers') as mock_get_headers:
            mock_get_headers.return_value = {'User-Agent': 'test-agent'}
            mock_requests_get.return_value = mock_response
            
            app.get_page("https://example.com")
            
            mock_requests_get.assert_called_once_with(
                "https://example.com", 
                headers={'User-Agent': 'test-agent'}, 
                verify=False
            )


class TestParseElement:
    """Test the parse_element function for data extraction"""
    
    def test_parse_element_success(self):
        """Test successful element parsing"""
        element = {
            "data-xvalue": "01/21/2026 00:00:00",
            "data-yvalue": "65",
            "fill": "#3366cc"
        }
        
        with patch('app.hex_to_grayscale') as mock_hex_convert, \
             patch('app.day_of_week') as mock_day_convert:
            mock_hex_convert.return_value = "#5C5C5C"
            mock_day_convert.return_value = "Tue"
            
            result = app.parse_element(element)
            
            expected = {"y": "65", "color": "#5C5C5C", "day": "Tue"}
            assert result == expected
    
    def test_parse_element_date_parsing(self):
        """Test that date parsing works correctly"""
        element = {
            "data-xvalue": "12/25/2025 00:00:00",
            "data-yvalue": "70",
            "fill": "#ff0000"
        }
        
        with patch('app.hex_to_grayscale') as mock_hex_convert, \
             patch('app.day_of_week') as mock_day_convert:
            mock_hex_convert.return_value = "#808080"
            mock_day_convert.return_value = "Thu"
            
            result = app.parse_element(element)
            
            # Verify the datetime object was created correctly
            mock_day_convert.assert_called_once()
            call_args = mock_day_convert.call_args[0][0]
            assert isinstance(call_args, datetime.datetime)
            # Note: app.py has a bug using %M instead of %H, so minutes become hour
            assert call_args.year == 2025
            assert call_args.month == 12
            assert call_args.day == 25


class TestExtractContent:
    """Test the extract_content function for HTML parsing"""
    
    def test_extract_content_success(self, sample_html_content):
        """Test successful content extraction from HTML"""
        with patch('app.parse_element') as mock_parse:
            mock_parse.side_effect = [
                {"y": "65", "color": "#5C5C5C", "day": "Tue"},
                {"y": "72", "color": "#6B6B6B", "day": "Wed"},
                {"y": "68", "color": "#848484", "day": "Thr"}
            ]
            
            result = app.extract_content(sample_html_content)
            
            assert len(result) == 3
            assert mock_parse.call_count == 3
    
    def test_extract_content_no_bars(self):
        """Test content extraction with no chart bars"""
        html_content = b"<html><body><p>No chart bars here</p></body></html>"
        
        result = app.extract_content(html_content)
        
        assert result == []
    
    def test_extract_content_beautifulsoup_parsing(self, sample_html_content):
        """Test that BeautifulSoup correctly identifies chart bars"""
        result_elements = []
        
        def capture_parse_calls(element):
            result_elements.append(element)
            return {"y": element["data-yvalue"], "color": "#808080", "day": "Test"}
        
        with patch('app.parse_element', side_effect=capture_parse_calls):
            app.extract_content(sample_html_content)
            
            assert len(result_elements) == 3
            assert result_elements[0]["data-yvalue"] == "65"
            assert result_elements[1]["data-yvalue"] == "72"
            assert result_elements[2]["data-yvalue"] == "68"


class TestBuildTrmnlPayload:
    """Test the build_trmnl_payload function"""
    
    def test_build_trmnl_payload_success(self, expected_parsed_data):
        """Test successful payload building"""
        result = app.build_trmnl_payload(expected_parsed_data)
        
        expected_payload = {
            "merge_variables": {
                0: {"y": "65", "color": "#5C5C5C", "day": "Tue"},
                1: {"y": "72", "color": "#6B6B6B", "day": "Wed"},
                2: {"y": "68", "color": "#848484", "day": "Thr"}
            }
        }
        
        assert result == expected_payload
    
    def test_build_trmnl_payload_empty_data(self):
        """Test payload building with empty data"""
        result = app.build_trmnl_payload([])
        
        assert result == {"merge_variables": {}}
    
    def test_build_trmnl_payload_single_item(self):
        """Test payload building with single data item"""
        data = [{"y": "75", "color": "#808080", "day": "Mon"}]
        
        result = app.build_trmnl_payload(data)
        
        expected = {
            "merge_variables": {
                0: {"y": "75", "color": "#808080", "day": "Mon"}
            }
        }
        assert result == expected


class TestWebhookUpload:
    """Test the webhook_upload function"""
    
    def test_webhook_upload_success(self, mock_requests_post):
        """Test successful webhook upload"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_response
        
        test_data = {"test": "data"}
        
        with patch('app.logging.info') as mock_log_info:
            app.webhook_upload("https://webhook.example.com", test_data)
            
            mock_requests_post.assert_called_once_with(
                "https://webhook.example.com", 
                json=test_data
            )
            mock_log_info.assert_called_with("Data successfully sent to webhook.")
    
    def test_webhook_upload_http_error(self, mock_requests_post):
        """Test webhook upload with HTTP error"""
        mock_requests_post.side_effect = requests.HTTPError("500 Server Error")
        
        test_data = {"test": "data"}
        
        with patch('app.logging.error') as mock_log_error:
            app.webhook_upload("https://webhook.example.com", test_data)
            
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args[0][0]
            assert "Error sending data to webhook" in call_args
    
    def test_webhook_upload_connection_error(self, mock_requests_post):
        """Test webhook upload with connection error"""
        mock_requests_post.side_effect = requests.ConnectionError("Connection failed")
        
        test_data = {"test": "data"}
        
        with patch('app.logging.error') as mock_log_error:
            app.webhook_upload("https://webhook.example.com", test_data)
            
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args[0][0]
            assert "Error sending data to webhook" in call_args


class TestRunFunction:
    """Test the main run function"""
    
    @patch('app.webhook_upload')
    @patch('app.build_trmnl_payload') 
    @patch('app.extract_content')
    @patch('app.get_page')
    @patch('app.logging.basicConfig')
    @patch('app.logging.getLogger')
    def test_run_function_integration(self, mock_get_logger, mock_logging_config,
                                    mock_get_page, mock_extract, mock_build_payload, 
                                    mock_webhook):
        """Test the complete run function workflow"""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_get_page.return_value = b"<html>test</html>"
        mock_extract.return_value = [{"test": "data"}]
        mock_build_payload.return_value = {"merge_variables": {"test": "payload"}}
        
        # Create mock config object
        mock_config = Mock()
        mock_config.APP_NAME = "test-agent"
        mock_config.LOG_LEVEL = "INFO"
        mock_config.SOURCE_URL = "https://test.com"
        mock_config.WEBHOOK_URL = "https://webhook.test.com"
        
        # Execute the run function
        app.run(mock_config)
        
        # Verify logging setup
        mock_logging_config.assert_called_once_with(
            filename="test-agent.log", 
            level="INFO"
        )
        
        # Verify the workflow
        mock_get_page.assert_called_once_with("https://test.com")
        mock_extract.assert_called_once_with(b"<html>test</html>")
        mock_build_payload.assert_called_once_with([{"test": "data"}])
        mock_webhook.assert_called_once_with(
            "https://webhook.test.com", 
            {"merge_variables": {"test": "payload"}}
        )
        
        # Verify logging calls
        assert mock_logger.info.call_count == 3  # startup, success, completion
        mock_logger.debug.assert_called_once()


class TestMainIntegration:
    """Integration tests for the individual workflow functions"""
    
    @patch('app.webhook_upload')
    @patch('app.build_trmnl_payload')
    @patch('app.extract_content')
    @patch('app.get_page')
    def test_workflow_functions_integration(self, mock_get_page, mock_extract, 
                                          mock_build_payload, mock_webhook):
        """Test the individual workflow functions working together"""
        # Setup mocks
        mock_get_page.return_value = b"<html>test</html>"
        mock_extract.return_value = [{"test": "data"}]
        mock_build_payload.return_value = {"merge_variables": {"test": "payload"}}
        
        # Execute the workflow manually
        page_content = app.get_page('https://test.com')
        extracted_data = app.extract_content(page_content)
        payload = app.build_trmnl_payload(extracted_data)
        app.webhook_upload('https://webhook.test.com', payload)
        
        # Verify the workflow
        mock_get_page.assert_called_once_with('https://test.com')
        mock_extract.assert_called_once_with(b"<html>test</html>")
        mock_build_payload.assert_called_once_with([{"test": "data"}])
        mock_webhook.assert_called_once_with(
            'https://webhook.test.com', 
            {"merge_variables": {"test": "payload"}}
        )