#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class GigPulseAPITester:
    def __init__(self, base_url="https://gig-pulse-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.passed_tests.append(name)
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'data' in response_data:
                        print(f"   Data count: {len(response_data['data']) if isinstance(response_data['data'], list) else 'N/A'}")
                except:
                    pass
            else:
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'url': url,
                    'response': response.text[:200] if response.text else 'No response'
                })
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            self.failed_tests.append({
                'name': name,
                'expected': expected_status,
                'actual': 'TIMEOUT',
                'url': url,
                'response': 'Request timed out'
            })
            print(f"❌ Failed - Request timed out")
            return False, {}
        except Exception as e:
            self.failed_tests.append({
                'name': name,
                'expected': expected_status,
                'actual': 'ERROR',
                'url': url,
                'response': str(e)
            })
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoints(self):
        """Test basic health and info endpoints"""
        print("\n=== Testing Health & Info Endpoints ===")
        
        # Test root endpoint
        self.run_test("Root API", "GET", "api/", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "api/health", 200)

    def test_static_content_endpoints(self):
        """Test static content endpoints"""
        print("\n=== Testing Static Content Endpoints ===")
        
        # Test featured channels
        self.run_test("Featured Channels", "GET", "api/static-content/featured-channels", 200)
        
        # Test weekly shows
        self.run_test("Weekly Shows", "GET", "api/static-content/weekly-shows", 200)
        
        # Test featured gear
        self.run_test("Featured Gear", "GET", "api/static-content/featured-gear", 200)
        
        # Test community favorites
        self.run_test("Community Favorites", "GET", "api/static-content/community-favorites", 200)
        
        # Test gig apps
        self.run_test("Gig Apps", "GET", "api/static-content/gig-apps", 200)
        
        # Test helpful tools
        self.run_test("Helpful Tools", "GET", "api/static-content/helpful-tools", 200)

    def test_suggestion_endpoints(self):
        """Test suggestion submission endpoints"""
        print("\n=== Testing Suggestion Endpoints ===")
        
        # Test channel suggestion
        channel_data = {
            "name": "Test Channel",
            "url": "https://youtube.com/@testchannel"
        }
        success, response = self.run_test("Submit Channel Suggestion", "POST", "api/suggestions/channel", 200, channel_data)
        
        # Test gear suggestion
        gear_data = {
            "name": "Test Gear Item",
            "category": "rideshare",
            "description": "A test gear item for rideshare drivers",
            "link": "https://amazon.com/test-item"
        }
        self.run_test("Submit Gear Suggestion", "POST", "api/suggestions/gear", 200, gear_data)
        
        # Test app suggestion
        app_data = {
            "name": "Test App",
            "category": "delivery",
            "description": "A test app for delivery drivers",
            "link": "https://testapp.com"
        }
        self.run_test("Submit App Suggestion", "POST", "api/suggestions/app", 200, app_data)
        
        # Test news suggestion
        news_data = {
            "name": "Test News Site",
            "url": "https://testnews.com",
            "type": "website"
        }
        self.run_test("Submit News Suggestion", "POST", "api/suggestions/news", 200, news_data)

    def test_email_subscription(self):
        """Test email subscription endpoint"""
        print("\n=== Testing Email Subscription ===")
        
        # Test email subscription
        email_data = {
            "email": f"test{datetime.now().strftime('%H%M%S')}@example.com",
            "list_type": "merch"
        }
        self.run_test("Email Subscription", "POST", "api/subscribe", 200, email_data)

    def test_admin_endpoints(self):
        """Test admin endpoints (should work without auth for GET requests)"""
        print("\n=== Testing Admin Endpoints ===")
        
        # Test get suggestions
        self.run_test("Get Channel Suggestions", "GET", "api/suggestions/channel", 200)
        self.run_test("Get Gear Suggestions", "GET", "api/suggestions/gear", 200)
        self.run_test("Get App Suggestions", "GET", "api/suggestions/app", 200)
        self.run_test("Get News Suggestions", "GET", "api/suggestions/news", 200)
        
        # Test get subscribers
        self.run_test("Get Subscribers", "GET", "api/subscribers", 200)

    def test_youtube_endpoints(self):
        """Test YouTube API endpoints (may fail if no API key)"""
        print("\n=== Testing YouTube Endpoints ===")
        
        # Test featured channels
        self.run_test("YouTube Featured Channels", "GET", "api/youtube/featured-channels", 200)
        
        # Test feed (may fail without API key, but should return proper error)
        success, response = self.run_test("YouTube Feed", "GET", "api/youtube/feed?max_per_channel=2", 200)
        if not success:
            print("   Note: YouTube feed may fail without API key - this is expected")

    def test_news_endpoints(self):
        """Test news feed endpoints"""
        print("\n=== Testing News Endpoints ===")
        
        # Test news sources
        self.run_test("News Sources", "GET", "api/news/sources", 200)
        
        # Test news feed
        success, response = self.run_test("News Feed", "GET", "api/news/feed?limit=5", 200)
        if not success:
            print("   Note: News feed may fail due to RSS parsing - this is expected")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*50}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: Expected {test['expected']}, got {test['actual']}")
                if test['response'] and test['response'] != 'No response':
                    print(f"     Response: {test['response']}")
        
        if self.passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in self.passed_tests:
                print(f"   • {test}")
        
        return len(self.failed_tests) == 0

def main():
    print("🚀 Starting The Gig Pulse API Tests")
    print("=" * 50)
    
    tester = GigPulseAPITester()
    
    # Run all test suites
    tester.test_health_endpoints()
    tester.test_static_content_endpoints()
    tester.test_suggestion_endpoints()
    tester.test_email_subscription()
    tester.test_admin_endpoints()
    tester.test_youtube_endpoints()
    tester.test_news_endpoints()
    
    # Print summary and return appropriate exit code
    all_passed = tester.print_summary()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())