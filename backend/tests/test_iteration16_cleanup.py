"""
Iteration 16 - Dashboard Cleanup Tests
Tests that backend APIs still work after frontend cleanup (removal of Table/filter bar)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://project-platform-2.preview.emergentagent.com')


class TestAPIEndpoints:
    """Test all required backend API endpoints"""
    
    def test_api_root(self):
        """GET /api/ - API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cockpit Immo API"
        assert data["version"] == "1.0.0"
        print("✓ GET /api/ returns API info")
    
    def test_electrical_assets(self):
        """GET /api/map/electrical-assets - HTB postes and lines"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        assert len(assets) > 100, f"Expected 100+ assets, got {len(assets)}"
        
        # Check for postes HTB
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        assert len(postes) > 90, f"Expected 90+ postes HTB, got {len(postes)}"
        print(f"✓ GET /api/map/electrical-assets returns {len(assets)} assets ({len(postes)} postes)")
    
    def test_dc_existants(self):
        """GET /api/map/dc - Existing data centers"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        dc_list = data.get("dc_existants", [])
        assert len(dc_list) > 50, f"Expected 50+ DCs, got {len(dc_list)}"
        print(f"✓ GET /api/map/dc returns {len(dc_list)} data centers")
    
    def test_landing_points(self):
        """GET /api/map/landing-points - Submarine cable landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        lp_list = data.get("landing_points", [])
        assert len(lp_list) >= 8, f"Expected 8+ landing points, got {len(lp_list)}"
        print(f"✓ GET /api/map/landing-points returns {len(lp_list)} landing points")
    
    def test_chat_endpoint(self):
        """POST /api/chat - AI chatbot endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Bonjour",
                "session_id": "test_iteration16",
                "history": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "type" in data
        assert data["type"] == "text"
        assert "text" in data
        print(f"✓ POST /api/chat returns response: {data['text'][:50]}...")
    
    def test_s3renr_summary(self):
        """GET /api/s3renr/summary - S3REnR regional capacity data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", [])
        assert len(summary) >= 3, f"Expected 3+ regions, got {len(summary)}"
        
        # Check for expected regions
        regions = [s["region"] for s in summary]
        assert "IDF" in regions, "IDF region missing"
        assert "PACA" in regions, "PACA region missing"
        assert "HdF" in regions, "HdF region missing"
        print(f"✓ GET /api/s3renr/summary returns {len(summary)} regions")
    
    def test_rte_future_400kv(self):
        """GET /api/map/rte-future-400kv - Future 400kV line data"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        assert "line" in data, "Missing 'line' in response"
        assert "buffers" in data, "Missing 'buffers' in response"
        assert "metadata" in data, "Missing 'metadata' in response"
        
        # Check buffers
        buffers = data["buffers"]
        assert "1km" in buffers, "Missing 1km buffer"
        assert "3km" in buffers, "Missing 3km buffer"
        assert "5km" in buffers, "Missing 5km buffer"
        print("✓ GET /api/map/rte-future-400kv returns line + buffers")
    
    def test_submarine_cables(self):
        """GET /api/map/submarine-cables - Submarine cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        cables = data.get("submarine_cables", [])
        assert len(cables) >= 10, f"Expected 10+ cables, got {len(cables)}"
        print(f"✓ GET /api/map/submarine-cables returns {len(cables)} cables")


class TestChatbotParcelSearch:
    """Test chatbot parcel search functionality"""
    
    def test_parcel_search_query(self):
        """POST /api/chat - Parcel search via chatbot"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": "test_iteration16_search",
                "history": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Response type should be parcel_results or search_results
        assert data["type"] in ["parcel_results", "search_results", "text"], f"Unexpected type: {data['type']}"
        print(f"✓ Chatbot parcel search returns type: {data['type']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
