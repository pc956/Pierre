"""
Test PLU (GPU API) integration and mobile responsive features
Tests for iteration 5: PLU zones from GPU API + mobile responsive design
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPLUIntegration:
    """Test PLU zone data from GPU API"""
    
    def test_bbox_parcels_urban_area_returns_plu_u(self):
        """Urban area (Calais) should return PLU zone U"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 1.84,
                "min_lat": 50.93,
                "max_lon": 1.88,
                "max_lat": 50.96,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have parcels and GPU zones
        assert data.get("count", 0) > 0, "Should return parcels"
        assert data.get("gpu_zones_count", 0) > 0, "Should have GPU zones"
        
        # Check PLU fields exist
        parcels = data.get("parcelles", [])
        assert len(parcels) > 0
        
        # At least some parcels should have PLU=U (urban)
        plu_zones = [p.get("plu_zone") for p in parcels]
        assert "U" in plu_zones, f"Urban area should have PLU=U, got: {set(plu_zones)}"
        
        # Check PLU fields structure
        first_parcel = parcels[0]
        assert "plu_zone" in first_parcel
        assert "plu_libelle" in first_parcel
        assert "plu_libelong" in first_parcel
    
    def test_bbox_parcels_rural_area_returns_plu_n_or_a(self):
        """Rural area (Crau) should return PLU zone N or A"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 4.80,
                "min_lat": 43.55,
                "max_lon": 4.85,
                "max_lat": 43.58,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("count", 0) > 0, "Should return parcels"
        
        parcels = data.get("parcelles", [])
        plu_zones = [p.get("plu_zone") for p in parcels]
        
        # Rural area should have N (natural) or A (agricultural) zones
        rural_zones = {"N", "A"}
        found_rural = any(z in rural_zones for z in plu_zones)
        assert found_rural, f"Rural area should have PLU=N or A, got: {set(plu_zones)}"
    
    def test_bbox_parcels_plu_varies_by_location(self):
        """Different areas should return different PLU zones"""
        # Urban area
        urban_resp = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={"min_lon": 1.84, "min_lat": 50.93, "max_lon": 1.88, "max_lat": 50.96, "limit": 5}
        )
        # Rural area
        rural_resp = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={"min_lon": 4.80, "min_lat": 43.55, "max_lon": 4.85, "max_lat": 43.58, "limit": 5}
        )
        
        assert urban_resp.status_code == 200
        assert rural_resp.status_code == 200
        
        urban_zones = set(p.get("plu_zone") for p in urban_resp.json().get("parcelles", []))
        rural_zones = set(p.get("plu_zone") for p in rural_resp.json().get("parcelles", []))
        
        # Urban should have U, rural should have N or A
        assert "U" in urban_zones, f"Urban should have U, got {urban_zones}"
        assert "N" in rural_zones or "A" in rural_zones, f"Rural should have N or A, got {rural_zones}"
    
    def test_bbox_parcels_returns_gpu_zones_count(self):
        """Response should include gpu_zones_count field"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={"min_lon": 2.3, "min_lat": 48.8, "max_lon": 2.4, "max_lat": 48.9, "limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "gpu_zones_count" in data, "Response should include gpu_zones_count"
        assert isinstance(data["gpu_zones_count"], int)


class TestS3REnRStillWorks:
    """Verify S3REnR integration still works after PLU changes"""
    
    def test_s3renr_summary_endpoint(self):
        """S3REnR summary should return regional data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", [])
        assert len(summary) >= 3, "Should have at least 3 regions"
        
        regions = {r["region"] for r in summary}
        assert "IDF" in regions
        assert "PACA" in regions
        assert "HdF" in regions
    
    def test_s3renr_top_opportunities_endpoint(self):
        """S3REnR top opportunities should return sorted list"""
        response = requests.get(
            f"{BASE_URL}/api/s3renr/top-opportunities",
            params={"min_mw": 30, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        opportunities = data.get("opportunities", [])
        assert len(opportunities) > 0, "Should have opportunities"
        
        # Check sorted by MW descending
        mw_values = [o.get("mw_dispo", 0) for o in opportunities]
        assert mw_values == sorted(mw_values, reverse=True), "Should be sorted by MW descending"
    
    def test_electrical_assets_have_s3renr_enrichment(self):
        """Electrical assets should have S3REnR enrichment"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        assets = data.get("electrical_assets", [])
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        
        # Some postes should have s3renr field
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        assert len(postes_with_s3renr) > 0, "Some postes should have S3REnR data"


class TestExistingEndpointsStillWork:
    """Verify existing endpoints still work"""
    
    def test_api_root(self):
        """API root should return version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Cockpit Immo API"
        assert data.get("version") == "1.0.0"
    
    def test_map_dc_endpoint(self):
        """DC existants endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("dc_existants", [])) > 0
    
    def test_map_landing_points_endpoint(self):
        """Landing points endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("landing_points", [])) > 0
    
    def test_map_submarine_cables_endpoint(self):
        """Submarine cables endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("submarine_cables", [])) > 0
    
    def test_commune_search_endpoint(self):
        """Commune search should work"""
        response = requests.get(f"{BASE_URL}/api/france/communes", params={"q": "Calais"})
        assert response.status_code == 200
        data = response.json()
        communes = data.get("communes", [])
        assert len(communes) > 0
        assert any("Calais" in c.get("nom", "") for c in communes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
