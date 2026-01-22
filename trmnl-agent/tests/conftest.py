import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add app directory to path for imports
app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))


@pytest.fixture
def mock_requests_get():
    """Mock requests.get() calls"""
    with patch('requests.get') as mock:
        yield mock


@pytest.fixture
def mock_requests_post():
    """Mock requests.post() calls"""
    with patch('requests.post') as mock:
        yield mock


@pytest.fixture
def mock_response():
    """Mock HTTP response object"""
    response = Mock()
    response.status_code = 200
    response.content = b'<html><body></body></html>'
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def sample_html_content():
    """Sample HTML content with chart bars for testing"""
    return b"""
    <html>
        <body>
            <rect class="index-chart-bar" data-xvalue="01/21/2026 00:00:00" data-yvalue="65" fill="#3366cc"></rect>
            <rect class="index-chart-bar" data-xvalue="01/22/2026 00:00:00" data-yvalue="72" fill="#dc3912"></rect>
            <rect class="index-chart-bar" data-xvalue="01/23/2026 00:00:00" data-yvalue="68" fill="#ff9900"></rect>
        </body>
    </html>
    """


@pytest.fixture
def expected_parsed_data():
    """Expected data structure after parsing HTML"""
    return [
        {"y": "65", "color": "#5C5C5C", "day": "Tue"},  # Grayscale conversion of #3366cc
        {"y": "72", "color": "#6B6B6B", "day": "Wed"},  # Grayscale conversion of #dc3912
        {"y": "68", "color": "#848484", "day": "Thr"}   # Grayscale conversion of #ff9900
    ]


@pytest.fixture
def sample_config():
    """Mock configuration values"""
    return {
        'SOURCE_URL': 'https://example.com/test',
        'WEBHOOK_URL': 'https://webhook.example.com/test',
        'LOG_LEVEL': 'INFO',
        'APP_NAME': 'trmnl-agent-test'
    }


@pytest.fixture
def mock_logging():
    """Mock logging calls"""
    with patch('logging.basicConfig'), \
         patch('logging.getLogger') as mock_get_logger, \
         patch('logging.info'), \
         patch('logging.error'), \
         patch('logging.debug'):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger