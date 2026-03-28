"""
Test suite for parcel click bug fix - iteration 3
Tests: Unique parcel IDs, geometry presence, bbox/commune endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestParcelUniqueIDs:
    """Test that parcels have unique IDs (bug fix for duplicate keys)"""
    
    def test_bbox_parcels_have_unique_ids(self):
        """BBox endpoint returns parcels with unique parcel_id values"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 2.50,
                "min_lat": 48.95,
                "max_lon": 2.55,
                "max_lat": 49.00,
                "limit": 100
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        assert len(parcels) > 0, "Should return at least some parcels"
        
        # Check for unique IDs
        ids = [p.get("parcel_id") for p in parcels]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), f"Found {len(ids) - len(unique_ids)} duplicate parcel IDs"
        
        # Verify ID format (should start with fr_)
        for parcel_id in ids[:10]:
            assert parcel_id.startswith("fr_"), f"Parcel ID should start with 'fr_': {parcel_id}"
            assert len(parcel_id) > 5, f"Parcel ID too short: {parcel_id}"
    
    def test_commune_parcels_have_unique_ids(self):
        """Commune endpoint returns parcels with unique parcel_id values"""
        # Villepinte commune code
        response = requests.get(f"{BASE_URL}/api/france/parcelles/commune/93078")
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        assert len(parcels) > 0, "Villepinte should have parcels"
        
        # Check for unique IDs
        ids = [p.get("parcel_id") for p in parcels]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), f"Found {len(ids) - len(unique_ids)} duplicate parcel IDs"


class TestParcelGeometry:
    """Test that parcels have polygon geometry for rendering"""
    
    def test_bbox_parcels_have_geometry(self):
        """BBox parcels should have geometry for polygon rendering"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 2.50,
                "min_lat": 48.95,
                "max_lon": 2.55,
                "max_lat": 49.00,
                "limit": 50
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        
        # Check geometry presence
        parcels_with_geom = [p for p in parcels if p.get("geometry")]
        assert len(parcels_with_geom) > 0, "At least some parcels should have geometry"
        
        # Verify geometry structure
        sample = parcels_with_geom[0]["geometry"]
        assert "type" in sample, "Geometry should have type"
        assert sample["type"] in ["Polygon", "MultiPolygon"], f"Unexpected geometry type: {sample['type']}"
        assert "coordinates" in sample, "Geometry should have coordinates"
    
    def test_commune_parcels_have_geometry(self):
        """Commune parcels should have geometry for polygon rendering"""
        response = requests.get(f"{BASE_URL}/api/france/parcelles/commune/93078")
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        
        # Check geometry presence
        parcels_with_geom = [p for p in parcels if p.get("geometry")]
        assert len(parcels_with_geom) > 0, "At least some parcels should have geometry"


class TestParcelScoreAndDistances:
    """Test that parcels have score and infrastructure distances"""
    
    def test_parcels_have_score_data(self):
        """Parcels should have score with verdict"""
        response = requests.get(f"{BASE_URL}/api/france/parcelles/commune/93078")
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        assert len(parcels) > 0
        
        # Check score structure
        sample = parcels[0]
        assert "score" in sample, "Parcel should have score"
        score = sample["score"]
        assert "score_net" in score, "Score should have score_net"
        assert "verdict" in score, "Score should have verdict"
        assert score["verdict"] in ["GO", "CONDITIONNEL", "NO_GO"], f"Invalid verdict: {score['verdict']}"
    
    def test_parcels_have_infrastructure_distances(self):
        """Parcels should have HTB and landing point distances"""
        response = requests.get(f"{BASE_URL}/api/france/parcelles/commune/93078")
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        assert len(parcels) > 0
        
        sample = parcels[0]
        assert "dist_poste_htb_m" in sample, "Should have HTB distance"
        assert "dist_landing_point_km" in sample, "Should have landing point distance"
        assert "landing_point_nom" in sample, "Should have landing point name"
        assert "surface_ha" in sample, "Should have surface in hectares"
        
        # Verify distances are reasonable (not 999999 default)
        assert sample["dist_poste_htb_m"] < 500000, "HTB distance should be reasonable"


class TestCommuneSearch:
    """Test commune search functionality"""
    
    def test_commune_search_villepinte(self):
        """Search for Villepinte returns correct commune"""
        response = requests.get(f"{BASE_URL}/api/france/communes", params={"q": "Villepinte"})
        assert response.status_code == 200
        
        data = response.json()
        communes = data.get("communes", [])
        assert len(communes) > 0, "Should find Villepinte"
        
        # First result should be Villepinte 93
        first = communes[0]
        assert first["nom"] == "Villepinte"
        assert first["code"] == "93078"
        assert "centre" in first, "Should have center coordinates"
        assert first["centre"]["coordinates"][0] > 2.5, "Longitude should be around 2.53"


class TestBboxEndpointParams:
    """Test bbox endpoint parameter handling"""
    
    def test_bbox_with_limit(self):
        """BBox respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 2.50,
                "min_lat": 48.95,
                "max_lon": 2.55,
                "max_lat": 49.00,
                "limit": 10
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        assert len(parcels) <= 10, "Should respect limit parameter"
    
    def test_bbox_returns_count(self):
        """BBox returns count field"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 2.50,
                "min_lat": 48.95,
                "max_lon": 2.55,
                "max_lat": 49.00,
                "limit": 50
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data, "Should return count"
        assert data["count"] == len(data.get("parcelles", []))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
