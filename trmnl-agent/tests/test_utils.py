import pytest
import datetime
from unittest.mock import patch, Mock

from app import utils


class TestDayOfWeek:
    
    def test_day_of_week_all_days(self):
        """Test all days of the week"""
        # Test data: (year, month, day, expected_result)
        test_cases = [
            (2026, 1, 20, "Mon"),  # Monday
            (2026, 1, 21, "Tue"),  # Tuesday  
            (2026, 1, 22, "Wed"),  # Wednesday
            (2026, 1, 23, "Thr"),  # Thursday
            (2026, 1, 24, "Fri"),  # Friday
            (2026, 1, 25, "Sat"),  # Saturday
            (2026, 1, 26, "Sun"),  # Sunday
        ]
        
        for year, month, day, expected in test_cases:
            test_date = datetime.datetime(year, month, day)
            result = utils.day_of_week(test_date)
            assert result == expected, f"Failed for {test_date}: expected {expected}, got {result}"


class TestGetHeaders:
    """Test the get_headers function"""
    
    def test_get_headers_returns_dict(self):
        """Test that get_headers returns a dictionary"""
        result = utils.get_headers()
        assert isinstance(result, dict)
        assert 'User-Agent' in result
        assert result['User-Agent'] in utils.USER_AGENTS


class TestHexToGrayscale:
    """Test the hex_to_grayscale function"""
    
    def test_hex_to_grayscale_with_hash(self):
        result = utils.hex_to_grayscale("#f05514")
        assert result == "#7C7C7C"
    
    def test_hex_to_grayscale_without_hash(self):
        """Test hex conversion without # prefix"""
        result = utils.hex_to_grayscale("dc250e") 
        assert result == "#595959"
    
    def test_hex_to_grayscale_blue(self):
        """Test hex conversion for blue color"""
        result = utils.hex_to_grayscale("#ffd701") 
        assert result == "#CBCBCB"
    
    def test_hex_to_grayscale_invalid_length_short(self):
        """Test hex conversion with invalid short length"""
        result = utils.hex_to_grayscale("#FF")
        assert "Error" in result
    
    def test_hex_to_grayscale_invalid_length_long(self):
        """Test hex conversion with invalid long length"""
        result = utils.hex_to_grayscale("#FF00FF00")
        assert "Error" in result
    
    def test_hex_to_grayscale_invalid_characters(self):
        """Test hex conversion with invalid characters"""
        result = utils.hex_to_grayscale("#GGHHII")
        assert "Error" in result
    
    def test_hex_to_grayscale_empty_string(self):
        """Test hex conversion with empty string"""
        result = utils.hex_to_grayscale("")
        assert "Error" in result
