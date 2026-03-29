"""
Iteration 12 Tests: N+1 Query Optimization & Enhanced Chatbot Filters
Tests:
1. POST /api/chat with PLU filter
2. POST /api/chat with HTB distance filter
3. POST /api/chat with future 400kV distance filter
4. POST /api/chat with tension kV filter
5. POST /api/chat with surface filter
6. filters_applied field validation
7. GET /api/shortlists (N+1 optimized)
8. GET /api/parcels (N+1 optimized)
9. Previous features still work
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = "test_session_token_2026"

class TestChatbotAdvancedFilters:
    """Test enhanced chatbot filters for parcel search"""
    
    def test_plu_zone_filter(self):
        """POST /api/chat with PLU filter: 'parcelles en zone U PACA 1ha' → all parcels have plu_zone=U"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "parcelles en zone U PACA 1ha",
                "session_id": "test_plu_filter",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("type") == "parcel_results", f"Expected parcel_results, got {data.get('type')}"
        assert "filters_applied" in data, "filters_applied field missing"
        assert data["filters_applied"].get("plu_zones") == ["U"], f"Expected plu_zones=['U'], got {data['filters_applied'].get('plu_zones')}"
        
        # Verify all parcels have plu_zone=U or inconnu (API may not have PLU data for all)
        parcels = data.get("parcels", [])
        if parcels:
            for p in parcels:
                assert p.get("plu_zone") in ["U", "inconnu"], f"Parcel {p.get('parcel_id')} has plu_zone={p.get('plu_zone')}, expected U or inconnu"
        print(f"✓ PLU filter test passed: {len(parcels)} parcels returned with plu_zones filter")
    
    def test_htb_distance_filter(self):
        """POST /api/chat with HTB distance filter: 'terrains à moins de 2km d un poste' → all parcels have dist_poste_htb_m ≤ 2000"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "terrains à moins de 2km d un poste PACA",
                "session_id": "test_htb_filter",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "parcel_results"
        assert "filters_applied" in data
        assert data["filters_applied"].get("max_dist_htb_km") == 2, f"Expected max_dist_htb_km=2, got {data['filters_applied'].get('max_dist_htb_km')}"
        
        # Verify all parcels are within 2km of HTB
        parcels = data.get("parcels", [])
        for p in parcels:
            dist_m = p.get("dist_poste_htb_m", 0)
            assert dist_m <= 2000, f"Parcel {p.get('parcel_id')} has dist_poste_htb_m={dist_m}, expected ≤2000"
        print(f"✓ HTB distance filter test passed: {len(parcels)} parcels all within 2km of HTB")
    
    def test_future_400kv_distance_filter(self):
        """POST /api/chat with future 400kV filter: 'parcelles à moins de 3km de la future ligne 400kV' → all parcels have dist_future_400kv_m ≤ 3000"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "parcelles à moins de 3km de la future ligne 400kV PACA 2ha minimum",
                "session_id": "test_future_400kv_filter",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "parcel_results"
        assert "filters_applied" in data
        assert data["filters_applied"].get("max_dist_future_line_km") == 3, f"Expected max_dist_future_line_km=3, got {data['filters_applied'].get('max_dist_future_line_km')}"
        
        # Verify all parcels are within 3km of future line
        parcels = data.get("parcels", [])
        for p in parcels:
            dist_m = p.get("dist_future_400kv_m", 0)
            assert dist_m <= 3000, f"Parcel {p.get('parcel_id')} has dist_future_400kv_m={dist_m}, expected ≤3000"
        print(f"✓ Future 400kV distance filter test passed: {len(parcels)} parcels all within 3km of future line")
    
    def test_tension_kv_filter(self):
        """POST /api/chat with tension filter: 'parcelles près d un poste 400kV' → min_tension_kv=400 in filters_applied"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "parcelles près d un poste 400kV PACA",
                "session_id": "test_tension_filter",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "parcel_results"
        assert "filters_applied" in data
        assert data["filters_applied"].get("min_tension_kv") == 400, f"Expected min_tension_kv=400, got {data['filters_applied'].get('min_tension_kv')}"
        
        # Verify all parcels have tension_htb_kv >= 400
        parcels = data.get("parcels", [])
        for p in parcels:
            tension = p.get("tension_htb_kv", 0)
            assert tension >= 400, f"Parcel {p.get('parcel_id')} has tension_htb_kv={tension}, expected ≥400"
        print(f"✓ Tension kV filter test passed: {len(parcels)} parcels all near 400kV+ substations")
    
    def test_surface_filter(self):
        """POST /api/chat with surface filter: 'terrains de 5 hectares minimum' → min_surface_ha=5 in filters_applied"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "terrains de 5 hectares minimum PACA",
                "session_id": "test_surface_filter",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "parcel_results"
        assert "filters_applied" in data
        assert data["filters_applied"].get("min_surface_ha") == 5, f"Expected min_surface_ha=5, got {data['filters_applied'].get('min_surface_ha')}"
        
        # Verify all parcels have surface_ha >= 5
        parcels = data.get("parcels", [])
        for p in parcels:
            surface = p.get("surface_ha", 0)
            assert surface >= 5, f"Parcel {p.get('parcel_id')} has surface_ha={surface}, expected ≥5"
        print(f"✓ Surface filter test passed: {len(parcels)} parcels all ≥5ha")
    
    def test_filters_applied_field_present(self):
        """Verify filters_applied field is present in response and shows all active filters"""
        # Use a simpler query that reliably triggers parcel search
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve des parcelles 2ha minimum PACA",
                "session_id": "test_all_filters",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "parcel_results", f"Expected parcel_results, got {data.get('type')}"
        filters = data.get("filters_applied", {})
        
        # Check all filter fields are present
        required_fields = ["min_surface_ha", "max_surface_ha", "max_dist_htb_km", "min_tension_kv", "max_dist_future_line_km", "plu_zones", "search_radius_m"]
        for field in required_fields:
            assert field in filters, f"filters_applied missing field: {field}"
        
        print(f"✓ filters_applied field validation passed: {filters}")
    
    def test_summary_still_works(self):
        """POST /api/chat with general question 'Résumé S3REnR' still returns summary type"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Résumé S3REnR",
                "session_id": "test_summary",
                "history": []
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("type") == "summary", f"Expected type=summary, got {data.get('type')}"
        assert "summary" in data, "summary field missing"
        assert len(data["summary"]) >= 3, f"Expected at least 3 regions in summary, got {len(data['summary'])}"
        print(f"✓ S3REnR summary still works: {len(data['summary'])} regions")


class TestN1QueryOptimization:
    """Test N+1 query optimizations in shortlists and parcels endpoints"""
    
    def test_shortlists_endpoint_returns_200(self):
        """GET /api/shortlists returns 200 with shortlists (optimized N+1)"""
        response = requests.get(
            f"{BASE_URL}/api/shortlists",
            headers={"Cookie": f"session_token={SESSION_TOKEN}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "shortlists" in data, "shortlists field missing"
        print(f"✓ GET /api/shortlists returns 200 with {len(data['shortlists'])} shortlists")
    
    def test_parcels_endpoint_returns_200(self):
        """GET /api/parcels returns 200 (optimized N+1)"""
        response = requests.get(
            f"{BASE_URL}/api/parcels?region=PACA&limit=10",
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "parcels" in data, "parcels field missing"
        assert "count" in data, "count field missing"
        print(f"✓ GET /api/parcels returns 200 with {data['count']} parcels")


class TestPreviousFeaturesStillWork:
    """Verify previous features still work after changes"""
    
    def test_future_400kv_line_endpoint(self):
        """GET /api/map/rte-future-400kv returns line + buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "line" in data, "line field missing"
        assert "buffers" in data, "buffers field missing"
        print("✓ Future 400kV line endpoint still works")
    
    def test_layer_toggles_electrical_assets(self):
        """GET /api/map/electrical-assets returns postes HTB"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "electrical_assets" in data, "electrical_assets field missing"
        assert len(data["electrical_assets"]) > 0, "No electrical assets returned"
        print(f"✓ Electrical assets endpoint still works: {len(data['electrical_assets'])} assets")
    
    def test_pdf_export_endpoint(self):
        """POST /api/export/pdf returns valid PDF"""
        test_parcel = {
            "parcel_id": "test_parcel",
            "commune": "Test Commune",
            "surface_ha": 5.0,
            "latitude": 43.45,
            "longitude": 4.95,
            "dist_poste_htb_m": 1500,
            "tension_htb_kv": 400,
            "plu_zone": "U",
            "score": {"score_net": 75, "verdict": "GO"}
        }
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json=test_parcel,
            timeout=30
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 1000, "PDF content too small"
        print("✓ PDF export endpoint still works")
    
    def test_dvf_endpoint(self):
        """GET /api/dvf/commune/13039 returns DVF data"""
        response = requests.get(f"{BASE_URL}/api/dvf/commune/13039", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "prix_median_m2" in data or "error" not in data, "DVF data missing"
        print("✓ DVF endpoint still works")
    
    def test_dc_search_endpoint(self):
        """POST /api/dc/search returns search results"""
        response = requests.post(
            f"{BASE_URL}/api/dc/search",
            json={"mw_target": 20, "region": "PACA"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data, "results field missing"
        print(f"✓ DC search endpoint still works: {len(data['results'])} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
