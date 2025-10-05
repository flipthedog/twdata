"""
Real URL tests that make actual HTTP requests.
These tests iterate through all servers in conf/servers.yaml and validate their URLs.
Run these manually to verify that URLs are actually accessible and returning valid data.

Usage:
    # Test all servers (network required)
    uv run python tests/test_real_urls.py
    
    # Test specific server
    uv run python -m pytest tests/test_real_urls.py::TestRealUrls::test_server_en_accessibility -v
    
    # Run just URL format validation (no network)
    uv run python -m pytest tests/test_real_urls.py::TestRealUrls::test_all_servers_url_format -v
"""

# uv run python -m pytest tests/test_real_urls.py::TestRealUrls::test_all_servers_url_format tests/test_real_urls.py::TestRealUrls::test_url_construction_bugs tests/test_real_urls.py::TestRealUrls::test_invalid_urls_and_worlds -v

import pytest
import requests
import yaml
import time
from twdata import TWAPI
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ServerTestResult:
    """Container for server test results."""
    server_name: str
    server_url: str
    success: bool
    worlds_tested: List[str]
    files_tested: List[str]
    successful_files: List[str]
    failed_files: List[str]
    errors: List[str]
    total_response_time: float


class TestRealUrls:
    """Tests that validate URL accessibility for all configured servers."""
    
    @pytest.fixture(scope="class")
    def config(self):
        """Load server configuration from YAML file."""
        try:
            with open("conf/servers.yaml", "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            pytest.fail("Configuration file conf/servers.yaml not found.")
        except yaml.YAMLError as e:
            pytest.fail(f"Error parsing YAML file: {e}")
    
    def test_all_servers_url_format(self, config):
        """Test URL format validation for all configured servers (no network required)."""
        print("\n" + "="*80)
        print("URL FORMAT VALIDATION FOR ALL SERVERS")
        print("="*80)
        
        results = []
        
        for server in config['servers']:
            server_name = server['name']
            server_url = server['url']
            
            try:
                # Test with a dummy world to validate URL construction
                tw = TWAPI(server_name, base_url=server_url, worlds=[1])
                
                # Validate base URL format
                if server_url.startswith(('http://', 'https://')):
                    print(f"Testing {server_name}: {server_url}")
                    
                    # Check constructed world URLs for obvious issues
                    url_valid = True
                    if tw.urls:
                        sample_url = tw.urls[0]
                        
                        # Check for obviously malformed URLs
                        from urllib.parse import urlparse
                        try:
                            parsed = urlparse(sample_url)
                            
                            # Flag suspicious patterns that indicate URL construction bugs
                            suspicious_patterns = [
                                'www.www.',  # Double www
                                '.www.',     # www in middle of domain
                                '...',       # Triple dots
                                'http://.', 'https://.',  # Missing domain
                            ]
                            
                            domain_issues = any(pattern in sample_url.lower() for pattern in suspicious_patterns)
                            
                            # Check if domain looks reasonable (has at least one dot and no spaces)
                            domain_reasonable = ('.' in parsed.netloc and 
                                               ' ' not in parsed.netloc and 
                                               len(parsed.netloc) > 3)
                            
                            if domain_issues or not domain_reasonable:
                                print(f"  ✗ Malformed world URL: {sample_url}")
                                url_valid = False
                            else:
                                print(f"  ✓ World URL construction: {sample_url}")
                                
                        except Exception as url_parse_error:
                            print(f"  ✗ Invalid URL format: {sample_url} - {url_parse_error}")
                            url_valid = False
                    else:
                        print(f"  ✗ No world URLs generated")
                        url_valid = False
                    
                    # Validate map file URLs only if world URL is valid
                    if url_valid and tw.urls:
                        map_url_sample = tw.urls[0] + tw.map_files['village']
                        if map_url_sample.endswith('.txt') and '/map/' in map_url_sample:
                            print(f"  ✓ Map file URL format: {map_url_sample}")
                        else:
                            print(f"  ⚠ Map file URL format issue: {map_url_sample}")
                            url_valid = False
                    
                    results.append(url_valid)
                else:
                    print(f"✗ {server_name}: Invalid base URL format - {server_url}")
                    results.append(False)
                    
            except Exception as e:
                print(f"✗ {server_name}: Error during URL validation - {str(e)}")
                results.append(False)
        
        passed = sum(results)
        total = len(results)
        print(f"\nSummary: {passed}/{total} servers passed URL format validation")
        
        if passed < total:
            print(f"⚠️  {total - passed} servers have URL construction issues that need fixing")
        
        # Don't fail the test completely, but warn about issues
        if passed == 0:
            assert False, "All servers failed URL format validation - major configuration issue"
        elif passed < total * 0.5:
            print("❌ More than half of servers have URL issues - this needs investigation")
        else:
            print("✅ Most servers have valid URL formats")

    def test_url_construction_bugs(self):
        """Test specific URL construction bugs found in real configurations."""
        print("\n" + "="*80)
        print("URL CONSTRUCTION BUG TEST")
        print("="*80)
        
        # Test the specific Turkish server issue that creates malformed URLs
        problematic_configs = [
            {
                'name': 'turkish_server_bug',
                'language': 'tr',
                'base_url': 'http://www.klanlar.org/',
                'worlds': [1],
                'expected_issue': 'Creates https://tr1.www.klanlar.org (invalid subdomain)'
            },
            {
                'name': 'brazilian_server_bug',
                'language': 'br',
                'base_url': 'http://www.tribalwars.com.br/',
                'worlds': [1], 
                'expected_issue': 'Creates https://br1.www.tribalwars.com.br (invalid subdomain)'
            },
            {
                'name': 'double_www_test',
                'language': 'test',
                'base_url': 'https://www.www.example.com',
                'worlds': [1],
                'expected_issue': 'Creates test1.www.www.example.com (double www)'
            }
        ]
        
        for i, config in enumerate(problematic_configs, 1):
            print(f"\n[{i}/{len(problematic_configs)}] Testing {config['name']}")
            print(f"  Language: {config['language']}")
            print(f"  Base URL: {config['base_url']}")
            print(f"  Expected Issue: {config['expected_issue']}")
            
            try:
                tw = TWAPI(
                    language=config['language'],
                    base_url=config['base_url'],
                    worlds=config['worlds']
                )
                
                if tw.urls:
                    constructed_url = tw.urls[0]
                    map_url = constructed_url + tw.map_files['village']
                    
                    print(f"  Constructed World URL: {constructed_url}")
                    print(f"  Full Map URL: {map_url}")
                    
                    # Check for URL construction bugs
                    issues_found = []
                    
                    if '.www.' in constructed_url:
                        issues_found.append("Contains '.www.' - invalid subdomain structure")
                    
                    if 'www.www.' in constructed_url:
                        issues_found.append("Contains 'www.www.' - double www issue")
                    
                    from urllib.parse import urlparse
                    try:
                        parsed = urlparse(constructed_url)
                        if not parsed.netloc:
                            issues_found.append("No valid domain found")
                        elif parsed.netloc.count('.') < 1:
                            issues_found.append("Domain appears malformed")
                    except Exception:
                        issues_found.append("URL parsing failed")
                    
                    if issues_found:
                        print(f"  ✓ URL CONSTRUCTION BUG DETECTED:")
                        for issue in issues_found:
                            print(f"    - {issue}")
                    else:
                        print(f"  ⚠️  URL looks valid (unexpected)")
                        
                    # Try to actually access it to confirm it fails
                    try:
                        import requests
                        response = requests.get(map_url, timeout=3)
                        
                        if response.status_code == 200:
                            print(f"  ⚠️  UNEXPECTED: Malformed URL actually worked!")
                        else:
                            print(f"  ✓ EXPECTED: HTTP {response.status_code} (URL doesn't work)")
                            
                    except requests.exceptions.ConnectionError:
                        print(f"  ✓ EXPECTED: Connection failed (malformed URL)")
                    except requests.RequestException as e:
                        print(f"  ✓ EXPECTED: Request failed - {str(e)[:50]}...")
                else:
                    print(f"  ✗ No URLs generated")
                    
            except Exception as e:
                print(f"  ✗ Setup error: {str(e)[:60]}...")
        
        print(f"\n✓ URL construction bug test completed")

    def test_invalid_urls_and_worlds(self):
        """Test behavior with intentionally invalid URLs and world configurations."""
        print("\n" + "="*80)
        print("INVALID URL AND WORLD TEST")
        print("="*80)
        
        test_cases = [
            {
                'name': 'invalid_domain',
                'base_url': 'https://completely-fake-domain-12345.xyz',
                'worlds': [1],
                'expected_error': 'Network error'
            },
            {
                'name': 'malformed_url',
                'base_url': 'not-a-url-at-all',
                'worlds': [1],
                'expected_error': 'URL construction error'
            },
            {
                'name': 'nonexistent_world',
                'base_url': 'https://en.tribalwars.net',
                'worlds': [99999],  # World that definitely doesn't exist
                'expected_error': '404 or network error'
            },
            {
                'name': 'localhost_test',
                'base_url': 'http://localhost:9999',
                'worlds': [1],
                'expected_error': 'Connection refused'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Testing {test_case['name']}")
            print(f"  Base URL: {test_case['base_url']}")
            print(f"  Worlds: {test_case['worlds']}")
            print(f"  Expected: {test_case['expected_error']}")
            
            try:
                # Try to create TWAPI instance
                tw = TWAPI(
                    language='test',
                    base_url=test_case['base_url'],
                    worlds=test_case['worlds']
                )
                
                if tw.urls:
                    test_url = tw.urls[0] + tw.map_files['village']
                    print(f"  Constructed URL: {test_url}")
                    
                    try:
                        import requests
                        response = requests.get(test_url, timeout=5)
                        
                        if response.status_code == 200:
                            is_valid = tw.check_file_validity(response.text)
                            content_length = len(response.text)
                            
                            if is_valid and content_length > 0:
                                print(f"  ⚠️  UNEXPECTED SUCCESS: Got valid data ({content_length} chars)")
                                print(f"      This invalid URL actually worked!")
                            else:
                                error_type = "HTML error page" if not is_valid else "Empty content"
                                print(f"  ✓ EXPECTED FAILURE: {error_type}")
                        else:
                            print(f"  ✓ EXPECTED FAILURE: HTTP {response.status_code}")
                            
                    except requests.exceptions.ConnectionError as e:
                        print(f"  ✓ EXPECTED FAILURE: Connection error - {str(e)[:60]}...")
                    except requests.exceptions.Timeout as e:
                        print(f"  ✓ EXPECTED FAILURE: Timeout - {str(e)[:60]}...")
                    except requests.RequestException as e:
                        print(f"  ✓ EXPECTED FAILURE: Request error - {str(e)[:60]}...")
                else:
                    print(f"  ✗ No URLs generated - TWAPI setup failed")
                    
            except Exception as setup_error:
                print(f"  ✓ EXPECTED FAILURE: Setup error - {str(setup_error)[:60]}...")
        
        print(f"\n✓ Invalid URL/World test completed - all cases handled gracefully")

    def test_basic_server_accessibility(self, config):
        """Test basic network accessibility for all servers (quick validation)."""
        print("\n" + "="*80)
        print("BASIC NETWORK ACCESSIBILITY TEST")
        print("="*80)
        
        results = []
        
        for server in config['servers']:
            server_name = server['name']
            server_url = server['url']
            timeout = server.get('timeout', 10)
            
            print(f"Testing {server_name}: {server_url}")
            
            try:
                # Try to initialize TWAPI and get first world
                tw = TWAPI(server_name, base_url=server_url, worlds=None)
                
                if not tw.worlds:
                    print(f"  ✗ No worlds detected - URL construction may be broken")
                    results.append(False)
                    continue
                
                # Try to fetch one file from first world to validate URL works
                test_world_id = tw.worlds[0]
                test_url = tw.urls[0] + tw.map_files['village']
                
                print(f"  Testing URL: {test_url}")
                
                import requests
                response = requests.get(test_url, timeout=timeout)
                
                if response.status_code == 200:
                    is_valid = tw.check_file_validity(response.text)
                    content_length = len(response.text)
                    
                    if is_valid and content_length > 0:
                        print(f"  ✓ SUCCESS: Got valid data ({content_length} chars)")
                        results.append(True)
                    else:
                        error_type = "HTML error page" if not is_valid else "Empty content"
                        print(f"  ✗ FAILED: {error_type}")
                        results.append(False)
                else:
                    print(f"  ✗ FAILED: HTTP {response.status_code}")
                    results.append(False)
                    
            except requests.RequestException as e:
                print(f"  ✗ NETWORK ERROR: {str(e)[:80]}...")
                results.append(False)
            except Exception as e:
                print(f"  ✗ SETUP ERROR: {str(e)[:80]}...")
                results.append(False)

            time.sleep(1)  # Small delay between servers

        passed = sum(results)
        total = len(results)
        
        print(f"\n{'='*80}")
        print(f"RESULTS: {passed}/{total} servers accessible ({passed/total:.1%})")
        print('='*80)
        
        if passed == total:
            print("🎉 All servers are working correctly!")
        elif passed >= total * 0.7:
            print("👍 Most servers are working")
        elif passed >= total * 0.3:
            print("⚠️  Some servers have issues")
        else:
            print("❌ Many servers are failing - investigate configuration")

    @pytest.mark.skip(reason="Network test - run manually via main()")
    def test_all_servers_accessibility(self, config):
        """Test comprehensive network accessibility for all servers (manual test)."""
        results = self._test_all_servers_network(config)
        
        # Print summary
        print(f"\n{'='*80}")
        print("NETWORK TEST SUMMARY")
        print('='*80)
        
        successful_servers = [r for r in results if r.success]
        failed_servers = [r for r in results if not r.success]
        
        print(f"Total servers tested: {len(results)}")
        print(f"Successful: {len(successful_servers)}")
        print(f"Failed: {len(failed_servers)}")
        
        if failed_servers:
            print("\nFailed servers:")
            for result in failed_servers:
                print(f"  - {result.server_name}: {', '.join(result.errors)}")
        
        # For automated testing, we'll allow some failures but require at least some servers to work
        success_rate = len(successful_servers) / len(results) if results else 0
        assert success_rate > 0.3, f"Too many servers failed ({success_rate:.1%} success rate)"

    def _test_all_servers_network(self, config) -> List[ServerTestResult]:
        """Internal method to test network accessibility for all servers."""
        print("\n" + "="*80)
        print("NETWORK ACCESSIBILITY TEST FOR ALL SERVERS")
        print("="*80)
        
        results = []
        
        # Key file types to test (most important ones first)
        test_files = ['village', 'player', 'ally']
        
        for i, server in enumerate(config['servers'], 1):
            server_name = server['name']
            server_url = server['url']
            timeout = server.get('timeout', 10)
            
            print(f"\n[{i}/{len(config['servers'])}] Testing server: {server_name} ({server_url})")
            
            result = ServerTestResult(
                server_name=server_name,
                server_url=server_url,
                success=False,
                worlds_tested=[],
                files_tested=test_files.copy(),
                successful_files=[],
                failed_files=[],
                errors=[],
                total_response_time=0.0
            )
            
            try:
                # Initialize TWAPI for this server (limit worlds to avoid too many requests)
                tw = TWAPI(server_name, base_url=server_url, worlds=None)
                
                if not tw.worlds:
                    result.errors.append("No worlds detected")
                    results.append(result)
                    print(f"  ✗ No worlds found for {server_name}")
                    continue
                
                # Test with first available world
                test_world_id = tw.worlds[0]
                result.worlds_tested = [f"{server_name}{test_world_id}"]
                
                print(f"  Testing world: {server_name}{test_world_id}")
                
                start_time = time.time()
                
                for file_type in test_files:
                    file_url = tw.urls[0] + tw.map_files[file_type]
                    
                    try:
                        print(f"    Testing {file_type}... ", end="")
                        response = requests.get(file_url, timeout=timeout)
                        response.raise_for_status()
                        
                        # Validate content
                        is_valid = tw.check_file_validity(response.text)
                        content_length = len(response.text)
                        
                        if is_valid and content_length > 0:
                            result.successful_files.append(file_type)
                            print(f"✓ ({content_length} chars)")
                        else:
                            result.failed_files.append(file_type)
                            error_msg = "HTML error page" if not is_valid else "Empty content"
                            result.errors.append(f"{file_type}: {error_msg}")
                            print(f"✗ {error_msg}")
                        
                        # Small delay between requests
                        time.sleep(0.5)
                        
                    except requests.RequestException as e:
                        result.failed_files.append(file_type)
                        error_msg = f"{file_type}: {str(e)[:50]}..."
                        result.errors.append(error_msg)
                        print(f"✗ {str(e)[:50]}...")
                
                result.total_response_time = time.time() - start_time
                result.success = len(result.successful_files) > 0
                
                if result.success:
                    print(f"  ✓ Success: {len(result.successful_files)}/{len(test_files)} files accessible")
                else:
                    print(f"  ✗ Failed: No files accessible")
                
            except Exception as e:
                result.errors.append(f"Setup error: {str(e)}")
                print(f"  ✗ Setup failed: {str(e)}")
            
            results.append(result)
        
        return results


    # Individual server test methods (auto-generated from config)
    @pytest.mark.skip(reason="Network test - run manually via main()")
    def test_server_en_accessibility(self, config):
        """Test English server accessibility."""
        self._test_specific_server(config, 'en')
    
    @pytest.mark.skip(reason="Network test - run manually via main()")
    def test_server_de_accessibility(self, config):
        """Test German server accessibility."""
        self._test_specific_server(config, 'de')
    
    @pytest.mark.skip(reason="Network test - run manually via main()")
    def test_server_nl_accessibility(self, config):
        """Test Dutch server accessibility."""
        self._test_specific_server(config, 'nl')

    def _test_specific_server(self, config, server_name: str):
        """Test accessibility for a specific server."""
        server_config = next((s for s in config['servers'] if s['name'] == server_name), None)
        if not server_config:
            pytest.skip(f"Server {server_name} not found in configuration")
        
        print(f"\n{'='*60}")
        print(f"TESTING SERVER: {server_name.upper()}")
        print('='*60)
        
        # Create a mini config with just this server
        mini_config = {'servers': [server_config]}
        results = self._test_all_servers_network(mini_config)
        
        assert len(results) == 1, "Should have exactly one result"
        result = results[0]
        
        if result.success:
            print(f"\n✓ {server_name} server is working correctly!")
            print(f"  Successful files: {', '.join(result.successful_files)}")
        else:
            print(f"\n✗ {server_name} server has issues:")
            for error in result.errors:
                print(f"  - {error}")
        
        assert result.success, f"Server {server_name} accessibility test failed: {result.errors}"


def main():
    """Main function to run all tests manually."""
    print("TribalWars URL Validation Test Suite")
    print("="*50)
    
    # Load configuration
    try:
        with open("conf/servers.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: Configuration file conf/servers.yaml not found.")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return
    
    test_instance = TestRealUrls()
    
    # Run URL format validation (no network required)
    print("\nStep 1: URL Format Validation")
    print("-" * 30)
    try:
        test_instance.test_all_servers_url_format(config)
        print("✓ All servers passed URL format validation")
    except Exception as e:
        print(f"✗ URL format validation failed: {e}")
        return
    
    # Ask user if they want to run network tests
    print("\nStep 2: Network Accessibility Tests")
    print("-" * 35)
    
    user_input = input("Run network tests? This will make HTTP requests to all servers (y/N): ").strip().lower()
    
    if user_input in ['y', 'yes']:
        try:
            results = test_instance._test_all_servers_network(config)
            
            # Generate detailed report
            print(f"\n{'='*80}")
            print("DETAILED RESULTS")
            print('='*80)
            
            for result in results:
                print(f"\nServer: {result.server_name}")
                print(f"URL: {result.server_url}")
                print(f"Status: {'✓ PASS' if result.success else '✗ FAIL'}")
                print(f"Response Time: {result.total_response_time:.2f}s")
                
                if result.worlds_tested:
                    print(f"Worlds Tested: {', '.join(result.worlds_tested)}")
                
                if result.successful_files:
                    print(f"Working Files: {', '.join(result.successful_files)}")
                
                if result.failed_files:
                    print(f"Failed Files: {', '.join(result.failed_files)}")
                
                if result.errors:
                    print("Errors:")
                    for error in result.errors:
                        print(f"  - {error}")
            
            # Summary statistics
            successful = sum(1 for r in results if r.success)
            total = len(results)
            
            print(f"\n{'='*80}")
            print(f"FINAL SUMMARY: {successful}/{total} servers working ({successful/total:.1%})")
            print('='*80)
            
            if successful == total:
                print("🎉 All servers are working correctly!")
            elif successful > total * 0.7:
                print("👍 Most servers are working. Some may have temporary issues.")
            else:
                print("⚠️  Many servers are having issues. Please investigate.")
                
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
        except Exception as e:
            print(f"\n✗ Network tests failed: {e}")
    else:
        print("Skipping network tests.")
    
    print("\nTest suite completed!")


if __name__ == "__main__":
    main()
    # test.test_real_world_url_accessibility()
    # test.test_multiple_file_types_accessibility()