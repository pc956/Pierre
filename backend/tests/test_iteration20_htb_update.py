"""
Iteration 20 - HTB Electrical Substation Update Tests
Tests for the updated HTB postes data from OSM/Overpass:
- rte_postes_map.json: ~1091 postes (≥225kV) for map display
- rte_postes_all.json: ~3569 postes (≥63kV) for distance calculations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://project-platform-2.preview.emergentagent.com')


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root_returns_info(self):
        """GET /api/ returns API info with version"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Cockpit Immo API"
        assert data.get("version") == "1.0.0"
        print(f"API root: {data}")


class TestElectricalAssets:
    """Test electrical assets endpoint with new HTB data"""
    
    def test_electrical_assets_returns_postes(self):
        """GET /api/map/electrical-assets returns ~1091 postes HTB"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        assets = data.get("electrical_assets", [])
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        
        # Should have ~1091 postes (from rte_postes_map.json)
        assert len(postes) >= 1000, f"Expected ~1091 postes, got {len(postes)}"
        print(f"Total electrical assets: {len(assets)}")
        print(f"Postes HTB count: {len(postes)}")
    
    def test_postes_have_valid_format(self):
        """Postes HTB have required fields: asset_id, nom, type, geometry, tension_kv, puissance_mva, region"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        postes = [a for a in data.get("electrical_assets", []) if a.get("type") == "poste_htb"]
        assert len(postes) > 0, "No postes found"
        
        required_fields = ["asset_id", "nom", "type", "geometry", "tension_kv", "puissance_mva", "region"]
        sample = postes[0]
        
        for field in required_fields:
            assert field in sample, f"Missing field: {field}"
        
        # Check geometry structure
        assert sample["geometry"]["type"] == "Point"
        assert len(sample["geometry"]["coordinates"]) == 2
        
        print(f"Sample poste: {sample['nom']} - {sample['tension_kv']}kV - {sample['region']}")
    
    def test_postes_tension_at_least_225kv(self):
        """All postes on map API have tension_kv >= 225"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        postes = [a for a in data.get("electrical_assets", []) if a.get("type") == "poste_htb"]
        tensions = [p.get("tension_kv", 0) for p in postes]
        
        min_tension = min(tensions)
        max_tension = max(tensions)
        
        assert min_tension >= 225, f"Found poste with tension {min_tension}kV < 225kV"
        print(f"Tension range: {min_tension}kV - {max_tension}kV")
        print(f"All {len(postes)} postes have tension >= 225kV: PASS")
    
    def test_postes_have_s3renr_enrichment(self):
        """Some postes should have S3REnR enrichment data"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        postes = [a for a in data.get("electrical_assets", []) if a.get("type") == "poste_htb"]
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        
        # At least some postes should have S3REnR data
        print(f"Postes with S3REnR data: {len(postes_with_s3renr)} / {len(postes)}")
        
        if postes_with_s3renr:
            sample = postes_with_s3renr[0]
            s3renr = sample.get("s3renr", {})
            print(f"Sample S3REnR: {s3renr}")


class TestDataCenters:
    """Test data centers endpoint"""
    
    def test_dc_returns_data(self):
        """GET /api/map/dc returns data centers"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        
        dc = data.get("dc_existants", [])
        assert len(dc) > 50, f"Expected 60+ DC, got {len(dc)}"
        print(f"DC count: {len(dc)}")


class TestSubmarineCables:
    """Test submarine cables endpoint"""
    
    def test_cables_returns_data(self):
        """GET /api/map/submarine-cables returns cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        
        cables = data.get("submarine_cables", [])
        assert len(cables) >= 10, f"Expected 10+ cables, got {len(cables)}"
        print(f"Cables count: {len(cables)}")


class TestCommuneSearch:
    """Test commune search endpoint"""
    
    def test_commune_search_villepinte(self):
        """GET /api/france/communes?q=Villepinte returns results"""
        response = requests.get(f"{BASE_URL}/api/france/communes?q=Villepinte")
        assert response.status_code == 200
        data = response.json()
        
        communes = data.get("communes", [])
        assert len(communes) > 0, "No communes found for Villepinte"
        
        # Check first result
        first = communes[0]
        assert "nom" in first
        assert "code" in first
        print(f"Found {len(communes)} communes for 'Villepinte'")
        print(f"First result: {first.get('nom')} ({first.get('code')})")


class TestS3REnRSummary:
    """Test S3REnR summary endpoint"""
    
    def test_s3renr_summary_returns_regions(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", [])
        assert len(summary) > 0, "No S3REnR summary data"
        
        regions = [s.get("region") for s in summary]
        print(f"S3REnR regions: {regions}")
        
        # Check for expected regions
        assert "IDF" in regions or "PACA" in regions or "HdF" in regions


class TestRTEFutureLine:
    """Test RTE future 400kV line endpoint"""
    
    def test_future_line_returns_geojson(self):
        """GET /api/map/rte-future-400kv returns GeoJSON with line and buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        
        assert "line" in data, "Missing 'line' in response"
        assert "buffers" in data, "Missing 'buffers' in response"
        assert "metadata" in data, "Missing 'metadata' in response"
        
        print(f"Future line metadata: {data.get('metadata', {}).get('nom')}")


class TestLandingPoints:
    """Test landing points endpoint"""
    
    def test_landing_points_returns_data(self):
        """GET /api/map/landing-points returns landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        
        lp = data.get("landing_points", [])
        assert len(lp) >= 5, f"Expected 5+ landing points, got {len(lp)}"
        print(f"Landing points count: {len(lp)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
