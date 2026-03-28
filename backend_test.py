#!/usr/bin/env python3
"""
Cockpit Immo - Backend API Testing
Tests all API endpoints for the French DC land prospection platform
"""
import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CockpitImmoAPITester:
    def __init__(self, base_url: str = "https://project-platform-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data if success else None
        })

    def test_api_root(self) -> bool:
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "message" in data and "Cockpit Immo" in data["message"]:
                self.log_test("API Root Endpoint", True, f"Status: {response.status_code}", data)
                return True
            else:
                self.log_test("API Root Endpoint", False, f"Expected Cockpit Immo message, got: {data}")
                return False
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_admin_stats(self) -> bool:
        """Test admin stats endpoint"""
        try:
            response = requests.get(f"{self.api_url}/admin/stats", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success:
                # Check if stats contain expected fields
                expected_fields = ["parcels", "scores", "users", "shortlists", "regions"]
                has_fields = all(field in data for field in expected_fields)
                
                if has_fields:
                    self.log_test("Admin Stats Endpoint", True, 
                                f"Parcels: {data.get('parcels', 0)}, Scores: {data.get('scores', 0)}", data)
                    return True
                else:
                    self.log_test("Admin Stats Endpoint", False, f"Missing expected fields in response: {data}")
                    return False
            else:
                self.log_test("Admin Stats Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Stats Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_parcels_endpoint(self) -> bool:
        """Test parcels endpoint with basic parameters"""
        try:
            # Test basic parcels endpoint
            response = requests.get(f"{self.api_url}/parcels", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "parcels" in data:
                parcels = data["parcels"]
                count = data.get("count", 0)
                
                if len(parcels) > 0:
                    # Check first parcel structure
                    first_parcel = parcels[0]
                    required_fields = ["parcel_id", "commune", "region", "surface_ha", "score"]
                    has_required = all(field in first_parcel for field in required_fields)
                    
                    if has_required and first_parcel.get("score"):
                        self.log_test("Parcels Endpoint", True, 
                                    f"Found {count} parcels with scores", {"count": count, "sample": first_parcel})
                        return True
                    else:
                        self.log_test("Parcels Endpoint", False, f"Missing required fields or score in parcel: {first_parcel}")
                        return False
                else:
                    self.log_test("Parcels Endpoint", False, "No parcels returned")
                    return False
            else:
                self.log_test("Parcels Endpoint", False, f"Status: {response.status_code}, Data: {data}")
                return False
        except Exception as e:
            self.log_test("Parcels Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_parcels_with_filters(self) -> bool:
        """Test parcels endpoint with filters"""
        try:
            # Test with region filter
            response = requests.get(f"{self.api_url}/parcels?region=IDF&project_type=colocation_t3", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "parcels" in data:
                parcels = data["parcels"]
                # Check if all parcels are from IDF region
                idf_parcels = [p for p in parcels if p.get("region") == "IDF"]
                
                if len(idf_parcels) == len(parcels) and len(parcels) > 0:
                    self.log_test("Parcels with Region Filter", True, 
                                f"Found {len(parcels)} IDF parcels", {"count": len(parcels)})
                    return True
                else:
                    self.log_test("Parcels with Region Filter", False, 
                                f"Filter not working properly. Total: {len(parcels)}, IDF: {len(idf_parcels)}")
                    return False
            else:
                self.log_test("Parcels with Region Filter", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Parcels with Region Filter", False, f"Exception: {str(e)}")
            return False

    def test_search_project(self) -> bool:
        """Test search project endpoint"""
        try:
            # Test search with project type
            payload = {
                "project_type": "colocation_t3",
                "regions": ["IDF", "PACA"],
                "score_min": 30
            }
            
            response = requests.post(f"{self.api_url}/search/project", 
                                   json=payload, 
                                   headers={"Content-Type": "application/json"},
                                   timeout=15)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "sites" in data:
                sites = data["sites"]
                count = data.get("count", 0)
                best_ttm = data.get("best_ttm")
                best_irr = data.get("best_irr")
                
                if len(sites) > 0:
                    # Check if sites have scores
                    scored_sites = [s for s in sites if s.get("score") and s["score"].get("score_net", 0) >= 30]
                    
                    if len(scored_sites) > 0:
                        self.log_test("Search Project Endpoint", True, 
                                    f"Found {count} sites, {len(scored_sites)} with score >= 30", 
                                    {"count": count, "best_ttm": best_ttm, "best_irr": best_irr})
                        return True
                    else:
                        self.log_test("Search Project Endpoint", False, "No sites with adequate scores found")
                        return False
                else:
                    self.log_test("Search Project Endpoint", True, "No sites match criteria (expected)", {"count": 0})
                    return True
            else:
                self.log_test("Search Project Endpoint", False, f"Status: {response.status_code}, Data: {data}")
                return False
        except Exception as e:
            self.log_test("Search Project Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_map_parcels(self) -> bool:
        """Test map parcels endpoint"""
        try:
            # Test map parcels with bounding box (IDF area)
            params = {
                "project_type": "colocation_t3",
                "min_lng": 1.5,
                "min_lat": 48.0,
                "max_lng": 3.5,
                "max_lat": 49.5
            }
            
            response = requests.get(f"{self.api_url}/map/parcels", params=params, timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "parcels" in data:
                parcels = data["parcels"]
                
                if len(parcels) > 0:
                    # Check if parcels have required map fields
                    first_parcel = parcels[0]
                    map_fields = ["parcel_id", "commune", "centroid", "score_net", "verdict"]
                    has_map_fields = all(field in first_parcel for field in map_fields)
                    
                    if has_map_fields:
                        self.log_test("Map Parcels Endpoint", True, 
                                    f"Found {len(parcels)} map parcels", {"count": len(parcels)})
                        return True
                    else:
                        self.log_test("Map Parcels Endpoint", False, f"Missing map fields in parcel: {first_parcel}")
                        return False
                else:
                    self.log_test("Map Parcels Endpoint", True, "No parcels in bounding box (expected)", {"count": 0})
                    return True
            else:
                self.log_test("Map Parcels Endpoint", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Map Parcels Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_specific_parcel(self) -> bool:
        """Test getting a specific parcel by ID"""
        try:
            # First get a parcel ID from the parcels endpoint
            response = requests.get(f"{self.api_url}/parcels?limit=1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("parcels") and len(data["parcels"]) > 0:
                    parcel_id = data["parcels"][0]["parcel_id"]
                    
                    # Now test getting specific parcel
                    response = requests.get(f"{self.api_url}/parcels/{parcel_id}", timeout=10)
                    success = response.status_code == 200
                    parcel_data = response.json() if success else {}
                    
                    if success and parcel_data.get("parcel_id") == parcel_id:
                        # Check if it has scores for different project types
                        scores = parcel_data.get("scores", {})
                        
                        if len(scores) > 0:
                            self.log_test("Specific Parcel Endpoint", True, 
                                        f"Parcel {parcel_id} with {len(scores)} project type scores", 
                                        {"parcel_id": parcel_id, "score_types": list(scores.keys())})
                            return True
                        else:
                            self.log_test("Specific Parcel Endpoint", False, f"No scores found for parcel {parcel_id}")
                            return False
                    else:
                        self.log_test("Specific Parcel Endpoint", False, f"Status: {response.status_code}")
                        return False
                else:
                    self.log_test("Specific Parcel Endpoint", False, "No parcels available to test with")
                    return False
            else:
                self.log_test("Specific Parcel Endpoint", False, "Could not get parcel list for testing")
                return False
        except Exception as e:
            self.log_test("Specific Parcel Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_auth_endpoints(self) -> bool:
        """Test auth endpoints (without actual authentication)"""
        try:
            # Test /auth/me without authentication (should return 401)
            response = requests.get(f"{self.api_url}/auth/me", timeout=10)
            
            if response.status_code == 401:
                self.log_test("Auth Me Endpoint (Unauthenticated)", True, 
                            "Correctly returns 401 for unauthenticated request")
                return True
            else:
                self.log_test("Auth Me Endpoint (Unauthenticated)", False, 
                            f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Auth Me Endpoint (Unauthenticated)", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting Cockpit Immo Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test all endpoints
        tests = [
            self.test_api_root,
            self.test_admin_stats,
            self.test_parcels_endpoint,
            self.test_parcels_with_filters,
            self.test_search_project,
            self.test_map_parcels,
            self.test_specific_parcel,
            self.test_auth_endpoints,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Test execution failed: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            success_rate = 100
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = CockpitImmoAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] == 100 else 1

if __name__ == "__main__":
    sys.exit(main())