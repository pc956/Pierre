"""
Test suite for Cockpit Immo Chatbot Parcel Search Feature (Iteration 11)
Tests the new find_parcels action that returns real cadastral parcels from IGN API.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestChatbotParcelSearch:
    """Tests for the new parcel search feature in chatbot"""
    
    def test_parcel_search_returns_parcel_results_type(self):
        """POST /api/chat with parcel search query returns type=parcel_results"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA 2ha minimum",
                "session_id": f"test_parcel_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("type") == "parcel_results", f"Expected type=parcel_results, got {data.get('type')}"
        
    def test_parcel_results_contain_required_fields(self):
        """Each parcel in results has all required fields"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles pour un DC de 30MW en PACA, 2ha minimum",
                "session_id": f"test_fields_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "parcel_results"
        
        parcels = data.get("parcels", [])
        assert len(parcels) > 0, "Expected at least one parcel"
        
        required_fields = [
            "parcel_id", "ref_cadastrale", "commune", "latitude", "longitude",
            "surface_ha", "dist_poste_htb_m", "tension_htb_kv", "plu_zone",
            "dvf_prix_median_m2", "score", "site_origin"
        ]
        
        for parcel in parcels[:3]:  # Check first 3 parcels
            for field in required_fields:
                assert field in parcel, f"Missing field '{field}' in parcel {parcel.get('parcel_id')}"
            
            # Verify score structure
            assert "score_net" in parcel.get("score", {}), "Missing score_net in score"
            assert "verdict" in parcel.get("score", {}), "Missing verdict in score"
    
    def test_parcels_sorted_by_score_descending(self):
        """Parcels are sorted by score descending"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": f"test_sort_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", [])
        if len(parcels) >= 2:
            scores = [p.get("score", {}).get("score_net", 0) for p in parcels]
            assert scores == sorted(scores, reverse=True), "Parcels not sorted by score descending"
    
    def test_response_includes_sites_searched(self):
        """Response includes sites_searched array showing which substations were queried"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": f"test_sites_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        sites_searched = data.get("sites_searched", [])
        assert len(sites_searched) > 0, "Expected sites_searched array"
        
        # Verify site structure
        for site in sites_searched:
            assert "name" in site, "Missing name in site"
            assert "lat" in site, "Missing lat in site"
            assert "lng" in site, "Missing lng in site"
            assert "grid" in site, "Missing grid in site"
    
    def test_response_includes_fly_to_coordinates(self):
        """Response includes fly_to coordinates for map centering"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": f"test_flyto_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        fly_to = data.get("fly_to")
        assert fly_to is not None, "Missing fly_to in response"
        assert "lat" in fly_to, "Missing lat in fly_to"
        assert "lng" in fly_to, "Missing lng in fly_to"
        assert "zoom" in fly_to, "Missing zoom in fly_to"
    
    def test_parcel_has_cadastral_reference(self):
        """Parcels have real cadastral references (not empty)"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA 2ha minimum",
                "session_id": f"test_cadastral_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", [])
        assert len(parcels) > 0, "Expected at least one parcel"
        
        for parcel in parcels[:3]:
            ref = parcel.get("ref_cadastrale", "")
            assert len(ref) > 0, f"Empty ref_cadastrale for parcel {parcel.get('parcel_id')}"
            # French cadastral refs are typically 14 characters
            assert len(ref) >= 10, f"Cadastral ref too short: {ref}"


class TestChatbotMacroSearch:
    """Tests for macro site search (search action) - should still work"""
    
    def test_site_search_returns_search_results_type(self):
        """POST /api/chat with 'Sites en PACA' returns type=search_results"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Sites en PACA",
                "session_id": f"test_macro_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "search_results", f"Expected type=search_results, got {data.get('type')}"
        
        results = data.get("results", [])
        assert len(results) > 0, "Expected at least one site result"


class TestChatbotSummary:
    """Tests for S3REnR summary - should still work"""
    
    def test_summary_returns_summary_type(self):
        """POST /api/chat with 'Résumé S3REnR' returns type=summary"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Résumé S3REnR",
                "session_id": f"test_summary_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "summary", f"Expected type=summary, got {data.get('type')}"
        
        summary = data.get("summary", [])
        assert len(summary) > 0, "Expected at least one region in summary"


class TestChatbotParcelSearchVariations:
    """Tests for different parcel search query variations"""
    
    def test_parcel_search_with_hdf_region(self):
        """Parcel search works with HdF region"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Parcelles zone industrielle HdF",
                "session_id": f"test_hdf_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        # Should return parcel_results or text if no parcels found
        assert data.get("type") in ["parcel_results", "text"], f"Unexpected type: {data.get('type')}"
    
    def test_parcel_search_near_fos(self):
        """Parcel search with 'Terrains 2ha+ près de Fos' works"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Terrains 2ha+ près de Fos",
                "session_id": f"test_fos_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        # Should trigger find_parcels action
        assert data.get("type") in ["parcel_results", "text"], f"Unexpected type: {data.get('type')}"


class TestChatbotParcelDataQuality:
    """Tests for data quality of returned parcels"""
    
    def test_parcel_surface_respects_minimum(self):
        """Parcels respect minimum surface filter"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA 2ha minimum",
                "session_id": f"test_surface_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", [])
        for parcel in parcels:
            surface = parcel.get("surface_ha", 0)
            assert surface >= 2.0, f"Parcel {parcel.get('parcel_id')} has surface {surface}ha < 2ha minimum"
    
    def test_parcel_has_htb_distance(self):
        """Parcels have HTB distance calculated"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": f"test_htb_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", [])
        for parcel in parcels[:3]:
            dist = parcel.get("dist_poste_htb_m", 0)
            assert dist > 0, f"Parcel {parcel.get('parcel_id')} has invalid HTB distance: {dist}"
            assert dist < 100000, f"HTB distance seems too large: {dist}m"
    
    def test_parcel_has_future_400kv_data(self):
        """Parcels include future 400kV line data"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 30MW PACA",
                "session_id": f"test_400kv_{int(time.time())}",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", [])
        for parcel in parcels[:3]:
            assert "dist_future_400kv_m" in parcel, f"Missing dist_future_400kv_m in parcel"
            assert "future_400kv_score_bonus" in parcel, f"Missing future_400kv_score_bonus in parcel"


class TestChatEndpointBasics:
    """Basic endpoint tests"""
    
    def test_chat_endpoint_exists(self):
        """POST /api/chat endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Bonjour",
                "session_id": "test_basic",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
    
    def test_chat_returns_json(self):
        """Chat endpoint returns valid JSON"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Bonjour",
                "session_id": "test_json",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "type" in data, "Response missing 'type' field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
