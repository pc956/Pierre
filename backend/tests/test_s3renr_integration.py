"""
Test S3REnR Integration - Cockpit Immo
Tests for S3REnR data enrichment on HTB postes and new endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestS3REnRSummaryEndpoint:
    """Tests for GET /api/s3renr/summary endpoint"""
    
    def test_summary_returns_200(self):
        """Summary endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /api/s3renr/summary returns 200")
    
    def test_summary_has_three_regions(self):
        """Summary contains IDF, PACA, HdF regions"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        data = response.json()
        assert "summary" in data, "Response missing 'summary' key"
        regions = [r["region"] for r in data["summary"]]
        assert "IDF" in regions, "Missing IDF region"
        assert "PACA" in regions, "Missing PACA region"
        assert "HdF" in regions, "Missing HdF region"
        print(f"✓ Summary contains all 3 regions: {regions}")
    
    def test_idf_is_saturated(self):
        """IDF region shows SATURE status"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        data = response.json()
        idf = next((r for r in data["summary"] if r["region"] == "IDF"), None)
        assert idf is not None, "IDF region not found"
        assert idf["status_global"] == "SATURE", f"IDF should be SATURE, got {idf['status_global']}"
        assert idf["mw_dispo_total"] == 0, f"IDF should have 0 MW dispo, got {idf['mw_dispo_total']}"
        assert idf["nb_satures"] == 10, f"IDF should have 10 saturated postes, got {idf['nb_satures']}"
        print(f"✓ IDF is SATURE with 0 MW dispo and {idf['nb_satures']} saturated postes")
    
    def test_paca_is_active(self):
        """PACA region shows ACTIF status with available capacity"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        data = response.json()
        paca = next((r for r in data["summary"] if r["region"] == "PACA"), None)
        assert paca is not None, "PACA region not found"
        assert paca["status_global"] == "ACTIF", f"PACA should be ACTIF, got {paca['status_global']}"
        assert paca["mw_dispo_total"] > 0, f"PACA should have MW dispo > 0, got {paca['mw_dispo_total']}"
        assert paca["nb_disponibles"] > 0, f"PACA should have disponible postes"
        print(f"✓ PACA is ACTIF with {paca['mw_dispo_total']} MW dispo, {paca['nb_disponibles']} disponible postes")
    
    def test_hdf_is_active(self):
        """HdF region shows ACTIF status with available capacity"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        data = response.json()
        hdf = next((r for r in data["summary"] if r["region"] == "HdF"), None)
        assert hdf is not None, "HdF region not found"
        assert hdf["status_global"] == "ACTIF", f"HdF should be ACTIF, got {hdf['status_global']}"
        assert hdf["mw_dispo_total"] > 0, f"HdF should have MW dispo > 0, got {hdf['mw_dispo_total']}"
        print(f"✓ HdF is ACTIF with {hdf['mw_dispo_total']} MW dispo, {hdf['nb_disponibles']} disponible postes")


class TestS3REnRTopOpportunitiesEndpoint:
    """Tests for GET /api/s3renr/top-opportunities endpoint"""
    
    def test_opportunities_returns_200(self):
        """Top opportunities endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/s3renr/top-opportunities")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /api/s3renr/top-opportunities returns 200")
    
    def test_opportunities_sorted_by_mw(self):
        """Opportunities are sorted by MW available descending"""
        response = requests.get(f"{BASE_URL}/api/s3renr/top-opportunities?min_mw=30&limit=20")
        data = response.json()
        assert "opportunities" in data, "Response missing 'opportunities' key"
        opps = data["opportunities"]
        assert len(opps) > 0, "No opportunities returned"
        
        # Check sorted descending
        mw_values = [o["mw_dispo"] for o in opps]
        assert mw_values == sorted(mw_values, reverse=True), "Opportunities not sorted by MW descending"
        print(f"✓ {len(opps)} opportunities returned, sorted by MW descending (top: {mw_values[0]} MW)")
    
    def test_opportunities_respect_min_mw_filter(self):
        """Opportunities respect min_mw filter"""
        min_mw = 100
        response = requests.get(f"{BASE_URL}/api/s3renr/top-opportunities?min_mw={min_mw}&limit=10")
        data = response.json()
        opps = data["opportunities"]
        
        for opp in opps:
            assert opp["mw_dispo"] >= min_mw, f"Opportunity {opp['poste']} has {opp['mw_dispo']} MW < {min_mw}"
        print(f"✓ All {len(opps)} opportunities have >= {min_mw} MW")
    
    def test_opportunities_have_required_fields(self):
        """Opportunities have all required fields"""
        response = requests.get(f"{BASE_URL}/api/s3renr/top-opportunities?limit=5")
        data = response.json()
        opps = data["opportunities"]
        
        required_fields = ["region", "poste", "mw_reserve", "mw_consomme", "mw_dispo", "etat", "score_dc"]
        for opp in opps:
            for field in required_fields:
                assert field in opp, f"Opportunity missing field: {field}"
        print(f"✓ All opportunities have required fields: {required_fields}")


class TestElectricalAssetsS3REnREnrichment:
    """Tests for S3REnR enrichment on /api/map/electrical-assets"""
    
    def test_electrical_assets_returns_200(self):
        """Electrical assets endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /api/map/electrical-assets returns 200")
    
    def test_postes_have_s3renr_field(self):
        """HTB postes in covered regions have s3renr field"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        postes = [a for a in data["electrical_assets"] if a.get("type") == "poste_htb"]
        
        # Check postes in IDF, PACA, HdF have s3renr
        covered_regions = ["IDF", "PACA", "HdF"]
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        
        assert len(postes_with_s3renr) > 0, "No postes have s3renr field"
        print(f"✓ {len(postes_with_s3renr)} out of {len(postes)} postes have s3renr field")
    
    def test_calais_has_direct_s3renr_match(self):
        """Poste Calais has direct S3REnR match with MW data"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        postes = [a for a in data["electrical_assets"] if a.get("type") == "poste_htb"]
        
        calais = next((p for p in postes if "CALAIS" in p["nom"].upper()), None)
        assert calais is not None, "Poste Calais not found"
        assert calais.get("s3renr") is not None, "Calais missing s3renr field"
        
        s3renr = calais["s3renr"]
        assert s3renr.get("mw_dispo") == 28, f"Calais should have 28 MW dispo, got {s3renr.get('mw_dispo')}"
        assert s3renr.get("etat") == "disponible", f"Calais should be disponible, got {s3renr.get('etat')}"
        assert s3renr.get("score_dc") == 6, f"Calais should have score_dc=6, got {s3renr.get('score_dc')}"
        print(f"✓ Calais has direct S3REnR match: {s3renr['mw_dispo']} MW dispo, etat={s3renr['etat']}")
    
    def test_valenciennes_has_direct_s3renr_match(self):
        """Poste Valenciennes has direct S3REnR match with MW data"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        postes = [a for a in data["electrical_assets"] if a.get("type") == "poste_htb"]
        
        valenciennes = next((p for p in postes if "VALENCIENNES" in p["nom"].upper()), None)
        assert valenciennes is not None, "Poste Valenciennes not found"
        assert valenciennes.get("s3renr") is not None, "Valenciennes missing s3renr field"
        
        s3renr = valenciennes["s3renr"]
        assert s3renr.get("mw_dispo") == 65, f"Valenciennes should have 65 MW dispo, got {s3renr.get('mw_dispo')}"
        assert s3renr.get("etat") == "disponible", f"Valenciennes should be disponible, got {s3renr.get('etat')}"
        print(f"✓ Valenciennes has direct S3REnR match: {s3renr['mw_dispo']} MW dispo, etat={s3renr['etat']}")
    
    def test_idf_postes_show_sature_status(self):
        """IDF postes without direct match show region-level sature status"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        postes = [a for a in data["electrical_assets"] if a.get("type") == "poste_htb"]
        
        idf_postes = [p for p in postes if p.get("region") == "IDF"]
        assert len(idf_postes) > 0, "No IDF postes found"
        
        for p in idf_postes:
            s3renr = p.get("s3renr")
            assert s3renr is not None, f"IDF poste {p['nom']} missing s3renr"
            assert s3renr.get("etat") == "sature", f"IDF poste {p['nom']} should be sature, got {s3renr.get('etat')}"
            assert s3renr.get("mw_dispo") == 0, f"IDF poste {p['nom']} should have 0 MW dispo"
        
        print(f"✓ All {len(idf_postes)} IDF postes show sature status with 0 MW dispo")
    
    def test_s3renr_field_structure(self):
        """S3REnR field has correct structure"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        postes = [a for a in data["electrical_assets"] if a.get("type") == "poste_htb" and a.get("s3renr")]
        
        # Check a poste with direct match (has all fields)
        direct_match = next((p for p in postes if p["s3renr"].get("mw_dispo") and p["s3renr"]["mw_dispo"] > 0), None)
        if direct_match:
            s3renr = direct_match["s3renr"]
            expected_fields = ["region", "etat", "mw_dispo"]
            for field in expected_fields:
                assert field in s3renr, f"S3REnR missing field: {field}"
            print(f"✓ S3REnR field has correct structure with fields: {list(s3renr.keys())}")


class TestExistingMapLayersStillWork:
    """Tests to verify existing map layers still work correctly"""
    
    def test_dc_existants_endpoint(self):
        """DC existants endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        assert "dc_existants" in data
        assert len(data["dc_existants"]) == 61, f"Expected 61 DC, got {len(data['dc_existants'])}"
        print(f"✓ /api/map/dc returns {len(data['dc_existants'])} DC existants")
    
    def test_landing_points_endpoint(self):
        """Landing points endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        assert "landing_points" in data
        assert len(data["landing_points"]) == 8, f"Expected 8 landing points, got {len(data['landing_points'])}"
        print(f"✓ /api/map/landing-points returns {len(data['landing_points'])} landing points")
    
    def test_submarine_cables_endpoint(self):
        """Submarine cables endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        assert "submarine_cables" in data
        assert len(data["submarine_cables"]) == 15, f"Expected 15 cables, got {len(data['submarine_cables'])}"
        print(f"✓ /api/map/submarine-cables returns {len(data['submarine_cables'])} cables")
    
    def test_electrical_assets_still_has_lignes(self):
        """Electrical assets still includes lignes 400kV and 225kV"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        data = response.json()
        assets = data["electrical_assets"]
        
        lignes_400 = [a for a in assets if a.get("type") == "ligne_400kv"]
        lignes_225 = [a for a in assets if a.get("type") == "ligne_225kv"]
        
        assert len(lignes_400) > 0, "No lignes 400kV found"
        assert len(lignes_225) > 0, "No lignes 225kV found"
        print(f"✓ Electrical assets includes {len(lignes_400)} lignes 400kV and {len(lignes_225)} lignes 225kV")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
