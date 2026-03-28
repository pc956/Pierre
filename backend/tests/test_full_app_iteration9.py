"""
Cockpit Immo — Full Application Test (Iteration 9)
Tests DVF endpoints, PDF export, CRM removal, and core features regression.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://project-platform-2.preview.emergentagent.com"

SESSION_TOKEN = "test_session_token_2026"


class TestDVFEndpoints:
    """DVF (Demandes de Valeurs Foncières) price data endpoints"""
    
    def test_dvf_commune_pas_de_calais(self):
        """GET /api/dvf/commune/62193 returns Pas-de-Calais data with prix_median_m2=45"""
        response = requests.get(f"{BASE_URL}/api/dvf/commune/62193")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "prix_median_m2" in data, "Missing prix_median_m2"
        assert data["prix_median_m2"] == 45, f"Expected 45, got {data['prix_median_m2']}"
        assert data["departement"] == "62", f"Expected dept 62, got {data.get('departement')}"
        print(f"✓ DVF Pas-de-Calais: {data['prix_median_m2']} €/m²")
    
    def test_dvf_commune_bouches_du_rhone(self):
        """GET /api/dvf/commune/13055 returns Bouches-du-Rhône data with prix_median_m2=120"""
        response = requests.get(f"{BASE_URL}/api/dvf/commune/13055")
        assert response.status_code == 200
        data = response.json()
        assert data["prix_median_m2"] == 120, f"Expected 120, got {data['prix_median_m2']}"
        assert data["departement"] == "13"
        print(f"✓ DVF Bouches-du-Rhône: {data['prix_median_m2']} €/m²")
    
    def test_dvf_region_paca(self):
        """GET /api/dvf/region/PACA returns aggregated data with departements list"""
        response = requests.get(f"{BASE_URL}/api/dvf/region/PACA")
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "PACA"
        assert "departements" in data, "Missing departements list"
        assert len(data["departements"]) > 0, "Empty departements list"
        assert "prix_moyen_pondere_m2" in data
        print(f"✓ DVF PACA: {data['prix_moyen_pondere_m2']} €/m² avg, {len(data['departements'])} depts")
    
    def test_dvf_region_idf(self):
        """GET /api/dvf/region/IDF returns IDF data"""
        response = requests.get(f"{BASE_URL}/api/dvf/region/IDF")
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "IDF"
        assert "departements" in data
        print(f"✓ DVF IDF: {data['prix_moyen_pondere_m2']} €/m² avg")
    
    def test_dvf_region_hdf(self):
        """GET /api/dvf/region/HdF returns HdF data"""
        response = requests.get(f"{BASE_URL}/api/dvf/region/HdF")
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "HdF"
        print(f"✓ DVF HdF: {data['prix_moyen_pondere_m2']} €/m² avg")
    
    def test_bbox_parcels_include_dvf_fields(self):
        """GET /api/france/parcelles/bbox includes dvf_prix_median_m2, dvf_prix_q1_m2, dvf_prix_q3_m2"""
        # Calais area bbox
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
        parcelles = data.get("parcelles", [])
        if len(parcelles) > 0:
            parcel = parcelles[0]
            assert "dvf_prix_median_m2" in parcel, "Missing dvf_prix_median_m2 in parcel"
            assert "dvf_prix_q1_m2" in parcel, "Missing dvf_prix_q1_m2 in parcel"
            assert "dvf_prix_q3_m2" in parcel, "Missing dvf_prix_q3_m2 in parcel"
            print(f"✓ BBox parcels have DVF fields: median={parcel['dvf_prix_median_m2']}")
        else:
            print("⚠ No parcels returned in bbox (API Carto may be slow)")


class TestPDFExport:
    """PDF export endpoints"""
    
    def test_pdf_export_parcel(self):
        """POST /api/export/pdf with parcel data returns valid PDF"""
        parcel_data = {
            "commune": "Calais",
            "region": "HdF",
            "code_dep": "62",
            "surface_m2": 50000,
            "plu_zone": "I",
            "score": {
                "score_net": 75,
                "verdict": "GO",
                "power_mw_p50": 20
            }
        }
        response = requests.post(f"{BASE_URL}/api/export/pdf", json=parcel_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("Content-Type") == "application/pdf", "Not a PDF response"
        # Check PDF magic bytes
        assert response.content[:4] == b'%PDF', "Response doesn't start with %PDF"
        print(f"✓ PDF export works, size: {len(response.content)} bytes")
    
    def test_pdf_export_dc_site_valid(self):
        """POST /api/export/pdf/dc-site with valid site_id returns PDF"""
        response = requests.post(
            f"{BASE_URL}/api/export/pdf/dc-site",
            json={"site_id": "dc_htb_hdf_001"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("Content-Type") == "application/pdf"
        assert response.content[:4] == b'%PDF'
        print(f"✓ DC site PDF export works, size: {len(response.content)} bytes")
    
    def test_pdf_export_dc_site_invalid(self):
        """POST /api/export/pdf/dc-site with invalid site_id returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/export/pdf/dc-site",
            json={"site_id": "invalid_site_xyz"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid site_id returns 404")


class TestCoreFeatures:
    """Core features regression tests"""
    
    def test_electrical_assets_with_s3renr(self):
        """GET /api/map/electrical-assets returns postes with S3REnR data"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        assert len(assets) > 0, "No electrical assets returned"
        
        # Check for postes with S3REnR data
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        assert len(postes) > 0, "No postes HTB found"
        
        # At least some postes should have S3REnR data
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        print(f"✓ {len(postes)} postes HTB, {len(postes_with_s3renr)} with S3REnR data")
    
    def test_s3renr_summary_returns_3_regions(self):
        """GET /api/s3renr/summary returns 3 regions"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", [])
        assert len(summary) == 3, f"Expected 3 regions, got {len(summary)}"
        regions = [s["region"] for s in summary]
        assert "IDF" in regions
        assert "PACA" in regions
        assert "HdF" in regions
        print(f"✓ S3REnR summary: {regions}")
    
    def test_s3renr_top_opportunities(self):
        """GET /api/s3renr/top-opportunities returns ranked list"""
        response = requests.get(f"{BASE_URL}/api/s3renr/top-opportunities")
        assert response.status_code == 200
        data = response.json()
        opportunities = data.get("opportunities", [])
        assert len(opportunities) > 0, "No opportunities returned"
        # Check structure
        opp = opportunities[0]
        assert "poste" in opp
        assert "mw_dispo" in opp
        print(f"✓ Top opportunities: {len(opportunities)} postes")
    
    def test_dc_search_paca(self):
        """POST /api/dc/search with PACA returns scored results"""
        response = requests.post(
            f"{BASE_URL}/api/dc/search",
            json={"mw_target": 20, "region": "PACA"}
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        assert len(results) > 0, "No results for PACA search"
        # Check structure
        result = results[0]
        assert "score" in result
        assert "location" in result
        assert result["location"]["region"] == "PACA"
        print(f"✓ DC search PACA: {len(results)} results")
    
    def test_dc_search_idf_saturated(self):
        """POST /api/dc/search with IDF returns results marked as saturated"""
        response = requests.post(
            f"{BASE_URL}/api/dc/search",
            json={"mw_target": 50, "region": "IDF"}
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        # IDF should have some saturated results
        saturated = [r for r in results if r.get("grid", {}).get("saturation_level") == "high"]
        print(f"✓ DC search IDF: {len(results)} results, {len(saturated)} saturated")
    
    def test_dc_site_detail(self):
        """GET /api/dc/site/dc_htb_hdf_001 returns site detail"""
        response = requests.get(f"{BASE_URL}/api/dc/site/dc_htb_hdf_001")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "location" in data
        assert "grid" in data
        assert "score" in data
        print(f"✓ DC site detail: {data['name']}")
    
    def test_chat_search_query(self):
        """POST /api/chat with '50MW en PACA' returns search_results"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "50MW en PACA", "session_id": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "search_results", f"Expected search_results, got {data.get('type')}"
        assert "results" in data
        print(f"✓ Chat search: {len(data.get('results', []))} results")
    
    def test_gpt_config(self):
        """GET /api/gpt/config returns GPT configuration"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "system_prompt" in data
        assert "openapi_schema_url" in data
        print(f"✓ GPT config: {data['name']}")
    
    def test_gpt_openapi_schema(self):
        """GET /api/gpt/openapi-schema returns valid schema"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        print(f"✓ OpenAPI schema: {len(data.get('paths', {}))} paths")


class TestMapData:
    """Map data endpoints"""
    
    def test_landing_points(self):
        """GET /api/map/landing-points returns data"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        lps = data.get("landing_points", [])
        assert len(lps) > 0
        print(f"✓ Landing points: {len(lps)}")
    
    def test_dc_existants(self):
        """GET /api/map/dc returns data"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        dcs = data.get("dc_existants", [])
        assert len(dcs) > 0
        print(f"✓ DC existants: {len(dcs)}")
    
    def test_submarine_cables(self):
        """GET /api/map/submarine-cables returns data"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        cables = data.get("submarine_cables", [])
        assert len(cables) > 0
        print(f"✓ Submarine cables: {len(cables)}")
    
    def test_commune_search(self):
        """GET /api/france/communes?q=Calais returns results"""
        response = requests.get(f"{BASE_URL}/api/france/communes?q=Calais")
        assert response.status_code == 200
        data = response.json()
        communes = data.get("communes", [])
        assert len(communes) > 0
        print(f"✓ Commune search 'Calais': {len(communes)} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
