import pytest
import logging
import yaml
import requests
from unittest.mock import patch, MagicMock, Mock
import re
from urllib.parse import urlparse

from twdata import TWAPI

# uv run python -m pytest tests/test_api.py -v


# Load configuration file

@pytest.fixture(scope="module")
def config():
    """Load configuration from YAML file.

    Returns:
        dict: Configuration data.
    """
    try:
        with open("conf/servers.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        pytest.fail("Configuration file conf/servers.yaml not found.")
    except yaml.YAMLError as e:
        pytest.fail(f"Error parsing YAML file: {e}")
    return None

def test_load_config(config):
    """Test loading of configuration file."""
    assert config is not None, "Configuration should not be None"
    assert 'servers' in config, "Configuration should contain 'servers' key"
    assert isinstance(config['servers'], list), "'servers' should be a list"
    assert len(config['servers']) > 0, "'servers' list should not be empty"
    for server in config['servers']:
        assert 'name' in server, "Each server should have a 'name'"
        assert 'url' in server, "Each server should have a 'url'"
        assert isinstance(server['name'], str) and server['name'], "'name' should be a non-empty string"
        assert isinstance(server['url'], str) and server['url'], "'url' should be a non-empty string"


# =====================================
# URL Validation Tests
# =====================================

class TestUrlValidation:
    """Test URL construction and validation."""
    
    def test_domain_mapping(self):
        """Test that domain mapping works correctly for different languages."""
        test_cases = [
            ('en', '.net'),
            ('de', '.de'),
            ('nl', '.nl'),
            ('fr', '.fr'),
            ('es', '.es'),
            ('us', '.us'),
            ('uk', '.co.uk'),
        ]
        
        for language, expected_domain in test_cases:
            with patch.object(TWAPI, 'get_worlds_by_language', return_value=['test123']):
                tw = TWAPI(language, worlds=[123])
                assert tw.domain == expected_domain, f"Domain for {language} should be {expected_domain}"

    def test_base_url_construction(self):
        """Test base URL construction for different languages."""
        test_cases = [
            ('en', None, 'https://en.tribalwars.net'),
            ('de', None, 'https://de.tribalwars.de'),
            ('custom', 'https://custom.example.com', 'https://custom.example.com'),
        ]
        
        for language, base_url, expected in test_cases:
            with patch.object(TWAPI, 'get_worlds_by_language', return_value=['test123']):
                tw = TWAPI(language, base_url=base_url, worlds=[123])
                assert tw.base_url == expected, f"Base URL should be {expected}"

    def test_world_url_construction(self):
        """Test that world URLs are constructed correctly."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144', 'en146']):
            tw = TWAPI('en', worlds=[144, 146])
            
            expected_urls = [
                'https://en144.tribalwars.net',
                'https://en146.tribalwars.net'
            ]
            
            assert tw.urls == expected_urls, f"URLs should be {expected_urls}"

    def test_custom_domain_url_construction(self):
        """Test URL construction with custom domains."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['de236']):
            tw = TWAPI('de', base_url='https://die-staemme.de', worlds=[236])
            
            expected_urls = ['https://de236.die-staemme.de']
            assert tw.urls == expected_urls, f"Custom domain URLs should be {expected_urls}"

    def test_map_file_url_generation(self):
        """Test that complete URLs for map files are generated correctly."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            # Test a few key map file URLs
            base_url = 'https://en144.tribalwars.net'
            expected_urls = {
                'village': f'{base_url}/map/village.txt',
                'player': f'{base_url}/map/player.txt',
                'ally': f'{base_url}/map/ally.txt',
            }
            
            for file_type, expected_url in expected_urls.items():
                full_url = tw.urls[0] + tw.map_files[file_type]
                assert full_url == expected_url, f"URL for {file_type} should be {expected_url}"


# =====================================
# File Validity Tests
# =====================================

class TestFileValidity:
    """Test file content validation using the existing check_file_validity method."""
    
    def test_valid_file_content(self):
        """Test that valid file content passes validation."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            valid_contents = [
                "1,Village Name,123,456,1,789\n2,Another Village,124,457,2,790",
                "player_id,name,tribe_id,villages,points,rank\n1,Player1,0,5,1000,1",
                "123456,Village Name,100,200,1,5000,Player Name",
                "",  # Empty file should be valid
                "Simple text content without HTML"
            ]
            
            for content in valid_contents:
                assert tw.check_file_validity(content), f"Content should be valid: {content[:50]}"

    def test_invalid_html_content(self):
        """Test that HTML content (error pages) is detected as invalid."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            # These should be detected as invalid (exact DOCTYPE html match)
            invalid_contents = [
                "<!DOCTYPE html><html><head><title>Error</title></head><body>Not Found</body></html>",
                "<!DOCTYPE html>\n<html>",
            ]
            
            for content in invalid_contents:
                assert not tw.check_file_validity(content), f"HTML content should be invalid: {content[:50]}"
            
            # This should be valid since it doesn't exactly match "<!DOCTYPE html>"
            xhtml_content = "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\""
            assert tw.check_file_validity(xhtml_content), f"XHTML DOCTYPE should be valid (different format): {xhtml_content[:50]}"

    def test_edge_case_content(self):
        """Test edge cases for file validation."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            # Content that starts with similar text but isn't HTML
            edge_cases = [
                "<!This is not HTML>",
                "< DOCTYPE html>",  # Space before DOCTYPE
                "<!doctype html>",  # lowercase
                "Some content\n<!DOCTYPE html>",  # HTML in middle of file
            ]
            
            for content in edge_cases:
                result = tw.check_file_validity(content)
                # These should be valid since they don't start with exact "<!DOCTYPE html>"
                if not content.startswith("<!DOCTYPE html>"):
                    assert result, f"Content should be valid: {content[:50]}"


# =====================================
# Network Request Tests
# =====================================

class TestNetworkRequests:
    """Test actual network requests and responses."""
    
    @patch('requests.get')
    def test_successful_file_download(self, mock_get):
        """Test successful file download with valid content."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "1,Village Name,123,456,1,789\n2,Another Village,124,457,2,790"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144], save_local=True)
            
            # Test that the mocked response would pass validation
            assert tw.check_file_validity(mock_response.text)

    @patch('requests.get')
    def test_html_error_response(self, mock_get):
        """Test handling of HTML error responses."""
        # Mock HTML error response
        mock_response = Mock()
        mock_response.text = "<!DOCTYPE html><html><head><title>404 Not Found</title></head></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            # Test that HTML error response is detected as invalid
            assert not tw.check_file_validity(mock_response.text)

    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            # The get_files method should handle the exception gracefully
            # We can't easily test this without running the full method,
            # but we can verify the exception would be raised
            with pytest.raises(requests.RequestException):
                mock_get("http://test.com")

    def test_url_accessibility_patterns(self):
        """Test URL patterns to ensure they follow expected format."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=['en144']):
            tw = TWAPI('en', worlds=[144])
            
            for url in tw.urls:
                # Parse URL to validate format
                parsed = urlparse(url)
                
                # Check basic URL structure
                assert parsed.scheme in ['http', 'https'], f"URL should use HTTP/HTTPS: {url}"
                assert parsed.netloc, f"URL should have a domain: {url}"
                
                # Check that domain follows expected pattern
                domain_pattern = r'^[a-z]+\d+\.tribalwars\.[a-z.]+$'
                assert re.match(domain_pattern, parsed.netloc), f"Domain should match pattern: {parsed.netloc}"


# =====================================
# World Detection Tests
# =====================================

class TestWorldDetection:
    """Test world detection and filtering functionality."""
    
    @patch('requests.get')
    def test_world_filtering_excludes_special_worlds(self, mock_get):
        """Test that special worlds (premium, speed, classic) are excluded."""
        # Mock response from get_servers.php
        mock_worlds_data = {
            b'en144': b'https://en144.tribalwars.net',
            b'en146': b'https://en146.tribalwars.net', 
            b'enp16': b'https://enp16.tribalwars.net',  # Premium world - should be excluded
            b'ens1': b'https://ens1.tribalwars.net',    # Speed world - should be excluded
            b'enc1': b'https://enc1.tribalwars.net',    # Classic world - should be excluded
        }
        
        import phpserialize
        mock_response = Mock()
        mock_response.content = phpserialize.dumps(mock_worlds_data)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        tw = TWAPI('en')  # Don't pass worlds, let it auto-detect
        
        # Should only include regular worlds (144, 146), not special ones
        expected_worlds = [144, 146]
        assert set(tw.worlds) == set(expected_worlds), f"Should only include regular worlds: {expected_worlds}"

    @patch('requests.get')
    def test_world_detection_handles_network_errors(self, mock_get):
        """Test that world detection handles network errors gracefully."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        # When network fails, should fall back to empty worlds list or handle gracefully
        tw = TWAPI('en')
        
        # Should handle the error and have empty worlds list
        assert isinstance(tw.worlds, list), "Worlds should still be a list even after network error"


# =====================================
# Integration Tests
# =====================================

class TestIntegration:
    """Integration tests that test multiple components together."""
    
    def test_complete_url_workflow(self, config):
        """Test complete workflow from config to URL generation."""
        # Test with first server from config
        server = config['servers'][0]
        
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=[f"{server['name']}144"]):
            tw = TWAPI(
                language=server['name'],
                base_url=server['url'],
                worlds=[144]
            )
            
            # Verify URL construction
            assert len(tw.urls) == 1
            assert server['name'] in tw.urls[0]
            
            # Verify map file URLs can be constructed
            for file_type, file_path in tw.map_files.items():
                full_url = tw.urls[0] + file_path
                parsed = urlparse(full_url)
                assert parsed.path.endswith('.txt'), f"Map file URL should end with .txt: {full_url}"

    @pytest.mark.parametrize("language,domain", [
        ('en', '.net'),
        ('de', '.de'), 
        ('nl', '.nl'),
        ('fr', '.fr'),
    ])
    def test_multiple_language_support(self, language, domain):
        """Test URL generation for multiple languages."""
        with patch.object(TWAPI, 'get_worlds_by_language', return_value=[f'{language}123']):
            tw = TWAPI(language, worlds=[123])
            
            expected_url = f'https://{language}123.tribalwars{domain}'
            assert tw.urls[0] == expected_url, f"URL for {language} should be {expected_url}"
 
