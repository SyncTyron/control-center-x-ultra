#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Control Center X Ultra
Tests all API endpoints mentioned in requirements
"""

import requests
import sys
import json
from datetime import datetime
import time

class ControlCenterAPITester:
    def __init__(self, base_url="https://ticket.armesa.de"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    self.log(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    self.log(f"   Response: {response.text[:100]}...")
                    return True, response.text
            else:
                self.tests_passed += 1 if response.status_code == expected_status else 0
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                self.log(f"❌ FAILED - {error_msg}")
                try:
                    error_detail = response.json()
                    self.log(f"   Error: {error_detail}")
                except:
                    self.log(f"   Error text: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'endpoint': endpoint,
                    'error': error_msg,
                    'status': response.status_code,
                    'expected': expected_status
                })
                return False, {}

        except requests.RequestException as e:
            self.log(f"❌ FAILED - Network Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'endpoint': endpoint,
                'error': f"Network Error: {str(e)}",
                'status': 'CONNECTION_ERROR',
                'expected': expected_status
            })
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        self.log("\n=== AUTHENTICATION TESTS ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success and isinstance(response, dict) and 'token' in response:
            self.token = response['token']
            user_info = response.get('user', {})
            self.log(f"   ✅ Login successful for user: {user_info.get('username')} (role: {user_info.get('role')})")
            return True
        else:
            self.log(f"   ❌ Login failed - no token received")
            return False

    def test_dashboard_apis(self):
        """Test Dashboard KPI endpoint"""
        self.log("\n=== DASHBOARD TESTS ===")
        
        success, kpi_data = self.run_test("Dashboard KPIs", "GET", "/kpi")
        if success and isinstance(kpi_data, dict):
            # Check for undefined/Invalid Date issues
            required_fields = ['total_tickets', 'open_tickets', 'closed_today', 'escalated', 'sla_breached', 'avg_response_time_min']
            missing_fields = []
            invalid_values = []
            
            for field in required_fields:
                if field not in kpi_data:
                    missing_fields.append(field)
                elif kpi_data[field] is None or kpi_data[field] == "undefined" or kpi_data[field] == "Invalid Date":
                    invalid_values.append(f"{field}: {kpi_data[field]}")
            
            if missing_fields:
                self.log(f"   ⚠️  Missing KPI fields: {missing_fields}")
            if invalid_values:
                self.log(f"   ❌ Invalid KPI values: {invalid_values}")
            else:
                self.log(f"   ✅ All KPI values are valid")
            
            self.log(f"   KPI Summary: Total={kpi_data.get('total_tickets')}, Open={kpi_data.get('open_tickets')}, Closed Today={kpi_data.get('closed_today')}")
        
        return success

    def test_tickets_api(self):
        """Test Tickets endpoint - check for n.map errors"""
        self.log("\n=== TICKETS TESTS ===")
        
        success, tickets_data = self.run_test("Get All Tickets", "GET", "/tickets")
        if success and isinstance(tickets_data, dict):
            # Check structure - should have 'tickets' key with array
            if 'tickets' in tickets_data and isinstance(tickets_data['tickets'], list):
                ticket_count = len(tickets_data['tickets'])
                self.log(f"   ✅ Tickets API returns proper structure with {ticket_count} tickets")
                
                # Check individual ticket structure
                if ticket_count > 0:
                    sample_ticket = tickets_data['tickets'][0]
                    required_ticket_fields = ['id', 'subject', 'status', 'priority', 'created_at']
                    missing_fields = [field for field in required_ticket_fields if field not in sample_ticket]
                    if missing_fields:
                        self.log(f"   ⚠️  Sample ticket missing fields: {missing_fields}")
                    else:
                        self.log(f"   ✅ Ticket structure is correct")
            else:
                self.log(f"   ❌ Invalid tickets response structure - missing 'tickets' array")
                return False
        
        # Test search functionality 
        search_success, search_data = self.run_test("Search Tickets", "GET", "/search?q=test")
        if search_success and isinstance(search_data, dict):
            if 'results' in search_data and isinstance(search_data['results'], list):
                self.log(f"   ✅ Search API returns proper structure with {len(search_data['results'])} results")
            else:
                self.log(f"   ❌ Invalid search response structure")
        
        return success and search_success

    def test_analytics_api(self):
        """Test Analytics SLA endpoint"""
        self.log("\n=== ANALYTICS TESTS ===")
        
        success, sla_data = self.run_test("SLA Analytics", "GET", "/sla")
        if success and isinstance(sla_data, dict):
            required_fields = ['compliance', 'total', 'breached', 'by_priority', 'daily']
            missing_fields = [field for field in required_fields if field not in sla_data]
            
            if missing_fields:
                self.log(f"   ❌ Missing SLA fields: {missing_fields}")
                return False
            else:
                self.log(f"   ✅ SLA data structure is correct")
                self.log(f"   SLA Summary: Compliance={sla_data.get('compliance')}%, Total={sla_data.get('total')}, Breached={sla_data.get('breached')}")
                
                # Check by_priority structure
                if isinstance(sla_data.get('by_priority'), dict):
                    self.log(f"   ✅ Priority breakdown available for {len(sla_data['by_priority'])} priorities")
                
                # Check daily data
                if isinstance(sla_data.get('daily'), list):
                    self.log(f"   ✅ Daily data available for {len(sla_data['daily'])} days")
        
        return success

    def test_support_stats_api(self):
        """Test Support Stats endpoint - check for n.map errors"""
        self.log("\n=== SUPPORT STATS TESTS ===")
        
        success, stats_data = self.run_test("Support Team Stats", "GET", "/support_stats")
        if success and isinstance(stats_data, dict):
            if 'stats' in stats_data and isinstance(stats_data['stats'], list):
                stats_count = len(stats_data['stats'])
                self.log(f"   ✅ Support stats API returns proper structure with {stats_count} supporters")
                
                # Check individual supporter structure
                if stats_count > 0:
                    sample_supporter = stats_data['stats'][0]
                    required_fields = ['supporter', 'total_tickets', 'closed_tickets', 'escalations', 'sla_breaches', 'score']
                    missing_fields = [field for field in required_fields if field not in sample_supporter]
                    if missing_fields:
                        self.log(f"   ⚠️  Sample supporter missing fields: {missing_fields}")
                    else:
                        self.log(f"   ✅ Supporter structure is correct")
                        self.log(f"   Top Supporter: {sample_supporter.get('supporter')} (Score: {sample_supporter.get('score')}%)")
            else:
                self.log(f"   ❌ Invalid support stats response structure - missing 'stats' array")
                return False
        
        return success

    def test_settings_api(self):
        """Test Settings endpoint"""
        self.log("\n=== SETTINGS TESTS ===")
        
        # Test GET settings
        success, settings_data = self.run_test("Get Settings", "GET", "/settings")
        if success and isinstance(settings_data, dict):
            expected_settings = ['sla_first_response', 'sla_resolution', 'auto_close_hours', 'max_tickets_per_user']
            missing_settings = [setting for setting in expected_settings if setting not in settings_data]
            
            if missing_settings:
                self.log(f"   ⚠️  Missing settings: {missing_settings}")
            else:
                self.log(f"   ✅ All expected settings present")
                self.log(f"   Settings: SLA First Response={settings_data.get('sla_first_response')}min, Resolution={settings_data.get('sla_resolution')}min")
        
        return success

    def test_user_management_api(self):
        """Test User Management endpoint"""
        self.log("\n=== USER MANAGEMENT TESTS ===")
        
        success, users_data = self.run_test("Get Users", "GET", "/admin/users")
        if success and isinstance(users_data, dict):
            if 'users' in users_data and isinstance(users_data['users'], list):
                users_count = len(users_data['users'])
                self.log(f"   ✅ User management API returns proper structure with {users_count} users")
                
                # Check for admin user
                admin_found = any(user.get('username') == 'admin' for user in users_data['users'])
                if admin_found:
                    self.log(f"   ✅ Admin user found in user list")
                else:
                    self.log(f"   ⚠️  Admin user not found in user list")
                
                # Check user structure
                if users_count > 0:
                    sample_user = users_data['users'][0]
                    required_fields = ['id', 'username', 'role']
                    missing_fields = [field for field in required_fields if field not in sample_user]
                    if missing_fields:
                        self.log(f"   ⚠️  Sample user missing fields: {missing_fields}")
                    else:
                        self.log(f"   ✅ User structure is correct")
            else:
                self.log(f"   ❌ Invalid users response structure - missing 'users' array")
                return False
        
        return success

    def test_live_chat_apis(self):
        """Test Live Chat related endpoints"""
        self.log("\n=== LIVE CHAT TESTS ===")
        
        # Test recent events
        success1, events_data = self.run_test("Get Recent Events", "GET", "/recent_events")
        if success1 and isinstance(events_data, dict):
            if 'events' in events_data and isinstance(events_data['events'], list):
                events_count = len(events_data['events'])
                self.log(f"   ✅ Recent events API returns proper structure with {events_count} events")
                
                # Check event structure
                if events_count > 0:
                    sample_event = events_data['events'][0]
                    required_fields = ['id', 'event_type', 'data', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in sample_event]
                    if missing_fields:
                        self.log(f"   ⚠️  Sample event missing fields: {missing_fields}")
                    else:
                        self.log(f"   ✅ Event structure is correct")
                        self.log(f"   Latest Event: {sample_event.get('event_type')} at {sample_event.get('timestamp')}")
            else:
                self.log(f"   ❌ Invalid events response structure - missing 'events' array")
                return False
        
        # Test SSE endpoint (just check it's accessible)
        try:
            response = requests.get(f"{self.base_url}/api/events", 
                                  headers={'Authorization': f'Bearer {self.token}'}, 
                                  timeout=2, stream=True)
            if response.status_code == 200:
                self.log(f"   ✅ SSE Events endpoint accessible")
                # Close connection immediately  
                response.close()
            else:
                self.log(f"   ❌ SSE Events endpoint returned {response.status_code}")
        except requests.Timeout:
            self.log(f"   ⚠️  SSE Events endpoint timeout (expected for streaming)")
        except Exception as e:
            self.log(f"   ❌ SSE Events endpoint error: {e}")
        
        return success1

    def test_health_check(self):
        """Test health endpoint"""
        self.log("\n=== HEALTH CHECK ===")
        success, health_data = self.run_test("Health Check", "GET", "/health")
        if success and isinstance(health_data, dict):
            if health_data.get('status') == 'ok':
                self.log(f"   ✅ Service is healthy: {health_data.get('service', 'Unknown')}")
            else:
                self.log(f"   ⚠️  Service status: {health_data.get('status')}")
        return success

    def print_summary(self):
        """Print test summary"""
        self.log(f"\n{'='*60}")
        self.log(f"TEST SUMMARY")
        self.log(f"{'='*60}")
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {len(self.failed_tests)}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            self.log(f"\nFAILED TESTS:")
            for test in self.failed_tests:
                self.log(f"❌ {test['name']} ({test['endpoint']}): {test['error']}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    print("🚀 Starting Control Center X Ultra Backend API Tests")
    print(f"Target: https://ticket.armesa.de")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tester = ControlCenterAPITester()
    
    # Run all tests in sequence
    all_passed = True
    
    if not tester.test_login():
        print("❌ Authentication failed - cannot proceed with other tests")
        return 1
    
    # Test all endpoints mentioned in requirements
    test_results = [
        tester.test_health_check(),
        tester.test_dashboard_apis(),
        tester.test_tickets_api(), 
        tester.test_analytics_api(),
        tester.test_support_stats_api(),
        tester.test_settings_api(),
        tester.test_user_management_api(),
        tester.test_live_chat_apis()
    ]
    
    all_passed = all(test_results)
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())