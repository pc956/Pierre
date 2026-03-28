"""
Test suite for Cockpit Immo - Nationwide Infrastructure APIs
Tests for HTB postes, DC existants, submarine cables, landing points, and parcels
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMapInfrastructureEndpoints:
    """Test nationwide infrastructure map endpoints"""
    
    def test_electrical_assets_returns_101_plus_htb_postes(self):
        """Backend API /api/map/electrical-assets returns 101+ HTB postes nationwide"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "electrical_assets" in data, "Response should contain 'electrical_assets' key"
        
        assets = data["electrical_assets"]
        assert len(assets) >= 101, f"Expected 101+ HTB postes, got {len(assets)}"
        
        # Verify structure of first asset
        if assets:
            first = assets[0]
            assert "asset_id" in first, "Asset should have asset_id"
            assert "nom" in first, "Asset should have nom"
            assert "geometry" in first, "Asset should have geometry"
            assert "tension_kv" in first, "Asset should have tension_kv"
            assert "puissance_mva" in first, "Asset should have puissance_mva"
            assert "region" in first, "Asset should have region"
        
        print(f"✓ Found {len(assets)} HTB postes nationwide")
    
    def test_dc_existants_returns_61_plus_dc(self):
        """Backend API /api/map/dc returns 61+ DC existants nationwide"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "dc_existants" in data, "Response should contain 'dc_existants' key"
        
        dcs = data["dc_existants"]
        assert len(dcs) >= 61, f"Expected 61+ DC existants, got {len(dcs)}"
        
        # Verify structure
        if dcs:
            first = dcs[0]
            assert "dc_id" in first, "DC should have dc_id"
            assert "nom" in first, "DC should have nom"
            assert "operateur" in first, "DC should have operateur"
            assert "geometry" in first, "DC should have geometry"
        
        print(f"✓ Found {len(dcs)} DC existants nationwide")
    
    def test_submarine_cables_returns_15_cables(self):
        """Backend API /api/map/submarine-cables returns 15 cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "submarine_cables" in data, "Response should contain 'submarine_cables' key"
        
        cables = data["submarine_cables"]
        assert len(cables) >= 15, f"Expected 15+ submarine cables, got {len(cables)}"
        
        # Verify structure
        if cables:
            first = cables[0]
            assert "cable_id" in first, "Cable should have cable_id"
            assert "nom" in first, "Cable should have nom"
            assert "geometry" in first, "Cable should have geometry"
            assert "capacite_tbps" in first, "Cable should have capacite_tbps"
        
        print(f"✓ Found {len(cables)} submarine cables")
    
    def test_landing_points_returns_8_points(self):
        """Backend API /api/map/landing-points returns 8 landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "landing_points" in data, "Response should contain 'landing_points' key"
        
        points = data["landing_points"]
        assert len(points) >= 8, f"Expected 8+ landing points, got {len(points)}"
        
        # Verify structure
        if points:
            first = points[0]
            assert "landing_id" in first, "Landing point should have landing_id"
            assert "nom" in first, "Landing point should have nom"
            assert "geometry" in first, "Landing point should have geometry"
            assert "nb_cables_connectes" in first, "Landing point should have nb_cables_connectes"
        
        print(f"✓ Found {len(points)} landing points")


class TestCommuneSearchEndpoint:
    """Test commune search functionality"""
    
    def test_commune_search_villepinte(self):
        """Backend API /api/france/communes search works for commune name queries"""
        response = requests.get(f"{BASE_URL}/api/france/communes?q=Villepinte&limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "communes" in data, "Response should contain 'communes' key"
        
        communes = data["communes"]
        assert len(communes) > 0, "Should find at least one commune for 'Villepinte'"
        
        # Verify structure
        first = communes[0]
        assert "code" in first or "code_insee" in first, "Commune should have code/code_insee"
        assert "nom" in first, "Commune should have nom"
        
        print(f"✓ Found {len(communes)} communes matching 'Villepinte'")
    
    def test_commune_search_short_query_returns_empty(self):
        """Commune search with query < 2 chars returns empty"""
        response = requests.get(f"{BASE_URL}/api/france/communes?q=V&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        communes = data.get("communes", [])
        assert len(communes) == 0, "Short query should return empty results"
        
        print("✓ Short query returns empty as expected")


class TestBboxParcelsEndpoint:
    """Test bbox parcels endpoint with real infrastructure distances"""
    
    def test_bbox_parcels_returns_parcels_with_distances(self):
        """Backend API /api/france/parcelles/bbox returns parcels with real infrastructure distances"""
        # Use a small area near Villepinte (IDF) to avoid timeout
        params = {
            "min_lon": 2.50,
            "min_lat": 48.95,
            "max_lon": 2.55,
            "max_lat": 49.00,
            "project_type": "colocation_t3",
            "limit": 50
        }
        
        response = requests.get(f"{BASE_URL}/api/france/parcelles/bbox", params=params, timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "parcelles" in data, "Response should contain 'parcelles' key"
        assert "count" in data, "Response should contain 'count' key"
        assert "source" in data, "Response should contain 'source' key"
        assert data["source"] == "api_carto_ign", "Source should be api_carto_ign"
        
        parcelles = data["parcelles"]
        print(f"✓ Found {len(parcelles)} parcels in bbox")
        
        # If parcels found, verify they have distance fields
        if parcelles:
            first = parcelles[0]
            assert "dist_poste_htb_m" in first, "Parcel should have dist_poste_htb_m"
            assert "dist_landing_point_km" in first, "Parcel should have dist_landing_point_km"
            assert "score" in first, "Parcel should have score"
            
            # Verify distances are reasonable (not default/placeholder values)
            dist_htb = first.get("dist_poste_htb_m", 0)
            dist_lp = first.get("dist_landing_point_km", 0)
            
            assert dist_htb > 0, "dist_poste_htb_m should be > 0"
            assert dist_lp > 0, "dist_landing_point_km should be > 0"
            
            print(f"  - First parcel: HTB dist={dist_htb}m, LP dist={dist_lp}km")
            print(f"  - Score: {first.get('score', {})}")


class TestCommuneParcelsEndpoint:
    """Test commune parcels endpoint"""
    
    def test_commune_parcels_with_real_htb_distances(self):
        """Backend API /api/france/parcelles/commune/{code_insee} returns scored parcels with real HTB distances"""
        # First search for a commune to get its code
        search_response = requests.get(f"{BASE_URL}/api/france/communes?q=Villepinte&limit=1")
        assert search_response.status_code == 200
        
        communes = search_response.json().get("communes", [])
        if not communes:
            pytest.skip("No commune found for Villepinte")
        
        code_insee = communes[0].get("code") or communes[0].get("code_insee")
        assert code_insee, "Commune should have code_insee"
        
        # Now get parcels for this commune
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/commune/{code_insee}?project_type=colocation_t3",
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "parcelles" in data, "Response should contain 'parcelles' key"
        assert "count" in data, "Response should contain 'count' key"
        
        parcelles = data["parcelles"]
        print(f"✓ Found {len(parcelles)} parcels for commune {code_insee}")
        
        if parcelles:
            first = parcelles[0]
            assert "dist_poste_htb_m" in first, "Parcel should have dist_poste_htb_m"
            assert "tension_htb_kv" in first, "Parcel should have tension_htb_kv"
            assert "dist_landing_point_km" in first, "Parcel should have dist_landing_point_km"
            assert "score" in first, "Parcel should have score"
            
            print(f"  - First parcel: HTB dist={first.get('dist_poste_htb_m')}m, tension={first.get('tension_htb_kv')}kV")


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """API root returns correct info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data or "status" in data
        print(f"✓ API root: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
