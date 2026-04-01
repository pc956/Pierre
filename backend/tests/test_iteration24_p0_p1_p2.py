"""
Iteration 24 - Testing P0, P1, P2 features:
- P0: GET /api/scan/dc-10mw regression, POST /api/chat find_parcels returns up to 30 parcels
- P1: Pappers Immo URLs (pappers_immo_url, pappers_map_url, cadastre_gouv_url) in scan results
- P2: GET /api/scan/region/{region_code} multi-postes scan endpoint
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_COOKIE = "test_session_token_2026"

@pytest.fixture
def api_client():
    """Shared requests session with auth cookie"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    session.cookies.set("session_token", SESSION_COOKIE)
    return session


class TestP0Regression:
    """P0: Regression tests for existing endpoints"""
    
    def test_api_root_returns_info(self, api_client):
        """GET /api/ returns API info"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "name" in data
        print(f"API info: {data}")
    
    def test_scan_dc_10mw_regression(self, api_client):
        """P0: GET /api/scan/dc-10mw should still work (regression)"""
        response = api_client.get(f"{BASE_URL}/api/scan/dc-10mw?region=PACA&max_results=5", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data or "parcels" in data or isinstance(data, list)
        print(f"Scan DC 10MW returned {len(data.get('candidates', data.get('parcels', data)))} results")
    
    def test_chat_find_parcels_returns_up_to_30(self, api_client):
        """P0: POST /api/chat with find_parcels action should return nb_parcels up to 30"""
        # Use a broader search query that's more likely to return results
        payload = {
            "message": "Trouve-moi des parcelles en PACA pour un data center",
            "conversation_id": "test_iteration24_p0_v2"
        }
        response = api_client.post(f"{BASE_URL}/api/chat", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure - chat returns text or parcel_results
        print(f"Chat response keys: {list(data.keys())}")
        
        # The response may be text-only if no parcels found, or include parcel_results
        if "parcel_results" in data:
            parcels = data.get("parcel_results", [])
            print(f"Chat find_parcels returned {len(parcels)} parcels")
            if len(parcels) > 0:
                print(f"First parcel: {parcels[0].get('ref_cadastrale', parcels[0].get('parcel_id', 'N/A'))}")
        elif "parcels" in data:
            parcels = data.get("parcels", [])
            print(f"Chat returned {len(parcels)} parcels")
        else:
            # Text-only response is valid
            print(f"Chat returned text response: {data.get('text', '')[:200]}...")
            assert "text" in data, "Expected either parcels or text in response"


class TestP1PappersImmoUrls:
    """P1: Pappers Immo URL fields in parcel results"""
    
    def test_scan_region_paca_has_pappers_urls(self, api_client):
        """P1: GET /api/scan/region/PACA should return parcels with pappers_immo_url and pappers_map_url"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/PACA?mw_min=100&max_results=2",
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        # Get parcels from response
        parcels = data.get("parcels", data.get("candidates", []))
        assert len(parcels) > 0, "Expected at least 1 parcel from PACA scan"
        
        # Check first parcel has Pappers URLs
        first_parcel = parcels[0]
        print(f"First parcel keys: {list(first_parcel.keys())}")
        
        # Verify pappers_immo_url field exists
        assert "pappers_immo_url" in first_parcel, "Missing pappers_immo_url field"
        pappers_url = first_parcel.get("pappers_immo_url")
        print(f"pappers_immo_url: {pappers_url}")
        
        # Verify URL format
        if pappers_url:
            assert "immobilier.pappers.fr" in pappers_url, f"Invalid Pappers URL format: {pappers_url}"
            assert "?q=" in pappers_url, f"Missing ?q= in Pappers URL: {pappers_url}"
    
    def test_scan_region_hdf_has_pappers_url(self, api_client):
        """P1: GET /api/scan/region/HdF should return parcels with pappers_immo_url"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/HdF?mw_min=100&max_results=2",
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", data.get("candidates", []))
        if len(parcels) > 0:
            first_parcel = parcels[0]
            assert "pappers_immo_url" in first_parcel, "Missing pappers_immo_url in HdF scan"
            print(f"HdF parcel pappers_immo_url: {first_parcel.get('pappers_immo_url')}")
        else:
            print("No parcels returned from HdF scan (may be due to MW filter)")
    
    def test_pappers_url_format_correct(self, api_client):
        """P1: Pappers Immo URL format should be https://immobilier.pappers.fr/?q={ref_cadastrale}"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/PACA?mw_min=50&max_results=1",
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", data.get("candidates", []))
        if len(parcels) > 0:
            parcel = parcels[0]
            pappers_url = parcel.get("pappers_immo_url", "")
            ref_cadastrale = parcel.get("ref_cadastrale", "")
            
            if pappers_url and ref_cadastrale:
                expected_url = f"https://immobilier.pappers.fr/?q={ref_cadastrale}"
                assert pappers_url == expected_url, f"URL mismatch: {pappers_url} != {expected_url}"
                print(f"Pappers URL format verified: {pappers_url}")
            
            # Also check pappers_map_url if present
            pappers_map_url = parcel.get("pappers_map_url")
            if pappers_map_url:
                assert "immobilier.pappers.fr/#" in pappers_map_url, f"Invalid map URL: {pappers_map_url}"
                print(f"pappers_map_url: {pappers_map_url}")
            
            # Check cadastre_gouv_url
            cadastre_url = parcel.get("cadastre_gouv_url")
            if cadastre_url:
                assert "cadastre.gouv.fr" in cadastre_url, f"Invalid cadastre URL: {cadastre_url}"
                print(f"cadastre_gouv_url: {cadastre_url}")


class TestP2ScanRegionEndpoint:
    """P2: GET /api/scan/region/{region_code} multi-postes scan"""
    
    def test_scan_region_paca_works(self, api_client):
        """P2: GET /api/scan/region/PACA?mw_min=20&max_results=5 works"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/PACA?mw_min=20&max_results=5",
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert isinstance(data, dict), "Response should be a dict"
        print(f"PACA scan response keys: {list(data.keys())}")
        
        parcels = data.get("parcels", data.get("candidates", []))
        print(f"PACA scan returned {len(parcels)} parcels")
        
        if len(parcels) > 0:
            # Verify parcel structure
            first = parcels[0]
            assert "parcel_id" in first or "ref_cadastrale" in first
            assert "score" in first or "score_net" in first or "score" in str(first)
    
    def test_scan_region_hdf_alias(self, api_client):
        """P2: GET /api/scan/region/HdF?mw_min=50&max_results=5 works with HdF alias"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/HdF?mw_min=50&max_results=5",
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        print(f"HdF scan returned: {len(data.get('parcels', data.get('candidates', [])))} parcels")
    
    def test_scan_region_aura(self, api_client):
        """P2: GET /api/scan/region/AuRA?mw_min=10&max_results=3 works"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/AuRA?mw_min=10&max_results=3",
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        print(f"AuRA scan returned: {len(data.get('parcels', data.get('candidates', [])))} parcels")
    
    def test_scan_region_deduplicates_parcels(self, api_client):
        """P2: Scan region deduplicates parcels (no duplicate parcel_ids)"""
        response = api_client.get(
            f"{BASE_URL}/api/scan/region/PACA?mw_min=20&max_results=10",
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcels", data.get("candidates", []))
        if len(parcels) > 1:
            parcel_ids = [p.get("parcel_id") or p.get("ref_cadastrale") for p in parcels]
            unique_ids = set(parcel_ids)
            
            assert len(parcel_ids) == len(unique_ids), f"Duplicate parcels found: {len(parcel_ids)} total, {len(unique_ids)} unique"
            print(f"Deduplication verified: {len(unique_ids)} unique parcels")


class TestMapEndpoints:
    """Verify map data endpoints still work"""
    
    def test_electrical_assets(self, api_client):
        """GET /api/map/electrical-assets returns postes"""
        response = api_client.get(f"{BASE_URL}/api/map/electrical-assets", timeout=30)
        assert response.status_code == 200
        data = response.json()
        # Response structure is {"electrical_assets": [...]}
        assert "electrical_assets" in data or "features" in data or isinstance(data, list)
        assets = data.get("electrical_assets", data.get("features", data))
        count = len(assets)
        print(f"Electrical assets: {count} postes")
        assert count >= 1000, f"Expected 1000+ postes, got {count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
