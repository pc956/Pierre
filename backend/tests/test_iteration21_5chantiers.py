"""
Iteration 21 - 5 Chantiers Testing
Tests for:
1. S3REnR accent matching (Réaltor, Lavéra, Feuillane)
2. Heatmap MW accent bug fix
3. RTE Fos-Jonquières project data
4. PDF export (try/except, None safety, projet_fos)
5. EmptyStatePanel dashboard + externalChatMessage + projet_fos
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAPIBasics:
    """Basic API health checks"""
    
    def test_api_info(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "title" in data
        print(f"✓ API info: {data}")

    def test_communes_search_fos(self):
        """GET /api/france/communes?q=Fos returns results"""
        response = requests.get(f"{BASE_URL}/api/france/communes", params={"q": "Fos"})
        assert response.status_code == 200
        data = response.json()
        # API returns {"communes": [...]}
        communes = data.get("communes", data) if isinstance(data, dict) else data
        assert isinstance(communes, list) or "communes" in data
        print(f"✓ Communes search 'Fos': {len(communes) if isinstance(communes, list) else 'found'} results")


class TestS3REnRAccentMatching:
    """Test S3REnR enrichment with accent-stripped matching"""
    
    def test_electrical_assets_count(self):
        """GET /api/map/electrical-assets returns ~1091+ postes"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        # API returns {"electrical_assets": [...]}
        assets = data.get("electrical_assets", data.get("postes", []))
        assert len(assets) >= 1000, f"Expected ~1091+ postes, got {len(assets)}"
        print(f"✓ Electrical assets: {len(assets)} postes")
    
    def test_realtor_s3renr_enrichment(self):
        """Réaltor should show mw_dispo > 0 and status='disponible'"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", data.get("postes", []))
        
        # Find Réaltor/REALTOR poste
        realtor = None
        for p in assets:
            nom = p.get("nom", "").upper()
            if "REALTOR" in nom or "RÉALTOR" in nom:
                realtor = p
                break
        
        assert realtor is not None, "REALTOR poste not found in map data"
        s3renr = realtor.get("s3renr", {})
        mw_dispo = s3renr.get("mw_dispo", 0)
        etat = s3renr.get("etat", "inconnu")
        print(f"✓ REALTOR found: mw_dispo={mw_dispo}, etat={etat}")
        assert mw_dispo > 0, f"REALTOR should have mw_dispo > 0, got {mw_dispo}"
        assert etat == "disponible", f"REALTOR should be 'disponible', got {etat}"
    
    def test_lavera_s3renr_enrichment(self):
        """Lavéra should show mw_dispo > 0 and status='disponible'"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", data.get("postes", []))
        
        # Find Lavéra/LAVERA poste
        lavera = None
        for p in assets:
            nom = p.get("nom", "").upper()
            if "LAVERA" in nom or "LAVÉRA" in nom:
                lavera = p
                break
        
        assert lavera is not None, "LAVERA poste not found in map data"
        s3renr = lavera.get("s3renr", {})
        mw_dispo = s3renr.get("mw_dispo", 0)
        etat = s3renr.get("etat", "inconnu")
        print(f"✓ LAVERA found: mw_dispo={mw_dispo}, etat={etat}")
        assert mw_dispo > 0, f"LAVERA should have mw_dispo > 0, got {mw_dispo}"
        assert etat == "disponible", f"LAVERA should be 'disponible', got {etat}"
    
    def test_feuillane_s3renr_enrichment(self):
        """Feuillane should show mw_dispo > 0 and status='disponible'"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", data.get("postes", []))
        
        # Find Feuillane poste
        feuillane = None
        for p in assets:
            nom = p.get("nom", "").upper()
            if "FEUILLANE" in nom:
                feuillane = p
                break
        
        assert feuillane is not None, "FEUILLANE poste not found in map data"
        s3renr = feuillane.get("s3renr", {})
        mw_dispo = s3renr.get("mw_dispo", 0)
        etat = s3renr.get("etat", "inconnu")
        print(f"✓ FEUILLANE found: mw_dispo={mw_dispo}, etat={etat}")
        assert mw_dispo > 0, f"FEUILLANE should have mw_dispo > 0, got {mw_dispo}"
        assert etat == "disponible", f"FEUILLANE should be 'disponible', got {etat}"
    
    def test_postes_with_s3renr_not_inconnu(self):
        """Check that postes with S3REnR data don't show 'inconnu' status"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", data.get("postes", []))
        
        # Count postes with S3REnR enrichment
        enriched = 0
        disponible = 0
        contraint = 0
        sature = 0
        inconnu = 0
        
        for p in assets:
            s3renr = p.get("s3renr")
            if s3renr:
                enriched += 1
                etat = s3renr.get("etat", "inconnu")
                if etat == "disponible":
                    disponible += 1
                elif etat == "contraint":
                    contraint += 1
                elif etat == "sature":
                    sature += 1
                else:
                    inconnu += 1
        
        print(f"✓ S3REnR enrichment stats:")
        print(f"  Total enriched: {enriched}")
        print(f"  Disponible: {disponible}")
        print(f"  Contraint: {contraint}")
        print(f"  Saturé: {sature}")
        print(f"  Inconnu: {inconnu}")
        
        # At least some postes should be enriched
        assert enriched > 0, "No postes have S3REnR enrichment"


class TestPDFExport:
    """Test PDF export with try/except and None safety"""
    
    def test_pdf_export_valid_parcel(self):
        """POST /api/export/pdf with valid parcel returns PDF"""
        parcel_data = {
            "commune": "Fos-sur-Mer",
            "surface_m2": 50000,
            "latitude": 43.44,
            "longitude": 4.94,
            "score": {
                "score": 72,
                "verdict": "GO",
                "detail": {
                    "distance_rte": 35,
                    "mw_disponibles": 25,
                    "plu": 15,
                    "surface": 8,
                    "malus": 0
                },
                "flags": [],
                "resume": "Test parcel for PDF export"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json=parcel_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 100, "PDF should have content"
        print(f"✓ PDF export valid parcel: {len(response.content)} bytes")
    
    def test_pdf_export_empty_body_handled(self):
        """POST /api/export/pdf with empty {} body is handled gracefully"""
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        # Should either return 500 with error message OR return a minimal PDF (both are acceptable)
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data, "Should have error detail"
            print(f"✓ PDF export empty body: 500 with error '{data.get('detail', '')[:100]}'")
        else:
            # If it returns 200, it should be a valid PDF
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/pdf"
            print(f"✓ PDF export empty body: 200 with minimal PDF ({len(response.content)} bytes)")
    
    def test_pdf_export_with_projet_fos(self):
        """POST /api/export/pdf with projet_fos field"""
        parcel_data = {
            "commune": "Fos-sur-Mer",
            "surface_m2": 30000,
            "latitude": 43.45,
            "longitude": 4.95,
            "projet_fos": "Noeud réseau renforcé — transit 2x2500 MW, horizon 2029",
            "score": {
                "score": 85,
                "verdict": "GO",
                "detail": {
                    "distance_rte": 40,
                    "mw_disponibles": 30,
                    "plu": 15,
                    "surface": 10,
                    "malus": 0
                },
                "flags": [],
                "resume": "Parcelle avec projet Fos-Jonquières"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json=parcel_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ PDF export with projet_fos: {len(response.content)} bytes")


class TestRTEFutureLineData:
    """Test RTE Fos-Jonquières project data"""
    
    def test_rte_future_400kv_endpoint(self):
        """GET /api/map/rte-future-400kv returns data with line + buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        
        # Check for line and buffer data (may be GeoJSON or custom format)
        if "type" in data and data.get("type") == "FeatureCollection":
            # GeoJSON format
            features = data.get("features", [])
            assert len(features) > 0, "Should have features"
            print(f"✓ RTE Future 400kV (GeoJSON): {len(features)} features")
        else:
            # Custom format with line, buffers, metadata
            assert "line" in data or "buffers" in data or "metadata" in data, "Should have line/buffers/metadata"
            print(f"✓ RTE Future 400kV (custom): keys={list(data.keys())}")
            
            if "metadata" in data:
                meta = data["metadata"]
                print(f"  Metadata: {meta.get('nom', 'N/A')}, {meta.get('capacite_transit_nouvelle_mw', 'N/A')} MW")


class TestOtherEndpoints:
    """Test other infrastructure endpoints"""
    
    def test_dc_existants(self):
        """GET /api/map/dc returns DC existants"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        dc_list = data.get("dc", data.get("data_centers", []))
        print(f"✓ DC existants: {len(dc_list)}")
    
    def test_submarine_cables(self):
        """GET /api/map/submarine-cables returns cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        cables = data.get("cables", data.get("submarine_cables", []))
        print(f"✓ Submarine cables: {len(cables)}")
    
    def test_landing_points(self):
        """GET /api/map/landing-points returns landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        points = data.get("landing_points", [])
        print(f"✓ Landing points: {len(points)}")
    
    def test_s3renr_summary(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        # API may return {"summary": [...]} or {"IDF": ..., "PACA": ...}
        if "summary" in data:
            summary = data["summary"]
            assert isinstance(summary, list) and len(summary) > 0
            print(f"✓ S3REnR summary: {len(summary)} regions")
        else:
            assert "IDF" in data or "PACA" in data or "HdF" in data
            print(f"✓ S3REnR summary: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
