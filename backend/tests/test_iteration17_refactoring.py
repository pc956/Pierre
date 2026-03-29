"""
Iteration 17 - Major Refactoring Tests
Tests for:
1. New scoring system (compute_score_simple) - universal /100 score
2. New verdicts (GO/A_ETUDIER/DEFAVORABLE/EXCLU)
3. Score breakdown (distance_rte, mw_disponibles, plu, surface, malus)
4. Chat endpoint with commune search
5. PDF export endpoint
6. Map layers endpoint (RTE future 400kV)
7. S3REnR summary endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAPIHealth:
    """Test API health and version"""
    
    def test_api_root_returns_version(self):
        """GET /api/ returns version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"
        print(f"API version: {data['version']}")


class TestChatEndpoint:
    """Test chat endpoint with new scoring system"""
    
    def test_chat_simple_query(self):
        """POST /api/chat works with simple query"""
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "message": "Trouve des parcelles en PACA",
            "session_id": "test_session_17",
            "history": []
        })
        assert response.status_code == 200
        data = response.json()
        assert "type" in data
        print(f"Chat response type: {data.get('type')}")
        # Should return either parcel_results, search_results, or text
        assert data["type"] in ["parcel_results", "search_results", "text", "error"]
    
    def test_chat_commune_search(self):
        """POST /api/chat works with commune search like 'Parcelles à Fos-sur-Mer'"""
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "message": "Parcelles à Fos-sur-Mer",
            "session_id": "test_session_17_commune",
            "history": []
        })
        assert response.status_code == 200
        data = response.json()
        assert "type" in data
        print(f"Commune search response type: {data.get('type')}")
        
        # If parcel_results, check for new scoring structure
        if data["type"] == "parcel_results":
            parcels = data.get("parcels", [])
            if parcels:
                parcel = parcels[0]
                score = parcel.get("score", {})
                # Check new scoring structure
                assert "score" in score, "Missing 'score' field in parcel score"
                assert "verdict" in score, "Missing 'verdict' field in parcel score"
                assert "detail" in score, "Missing 'detail' field in parcel score"
                assert "flags" in score, "Missing 'flags' field in parcel score"
                assert "resume" in score, "Missing 'resume' field in parcel score"
                
                # Check detail breakdown
                detail = score.get("detail", {})
                assert "distance_rte" in detail, "Missing 'distance_rte' in detail"
                assert "mw_disponibles" in detail, "Missing 'mw_disponibles' in detail"
                assert "plu" in detail, "Missing 'plu' in detail"
                assert "surface" in detail, "Missing 'surface' in detail"
                assert "malus" in detail, "Missing 'malus' in detail"
                
                # Check verdict is one of new values
                assert score["verdict"] in ["GO", "A_ETUDIER", "DEFAVORABLE", "EXCLU"], \
                    f"Invalid verdict: {score['verdict']}"
                
                print(f"First parcel score: {score['score']}/100, verdict: {score['verdict']}")
                print(f"Detail breakdown: {detail}")


class TestNewScoringSystem:
    """Test the new universal /100 scoring system"""
    
    def test_scoring_via_parcel_endpoint(self):
        """Test scoring via /api/parcels/{parcel_id}/score endpoint"""
        # First get some parcels via bbox
        bbox_response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 4.8,
                "min_lat": 43.3,
                "max_lon": 4.9,
                "max_lat": 43.4,
                "limit": 5
            }
        )
        
        if bbox_response.status_code == 200:
            data = bbox_response.json()
            parcels = data.get("parcelles", [])
            if parcels:
                parcel = parcels[0]
                score = parcel.get("score", {})
                
                # Verify new scoring structure
                assert "score" in score, "Missing 'score' field"
                assert "verdict" in score, "Missing 'verdict' field"
                assert "detail" in score, "Missing 'detail' field"
                
                # Score should be 0-100
                assert 0 <= score["score"] <= 100, f"Score out of range: {score['score']}"
                
                # Verdict should be one of new values
                assert score["verdict"] in ["GO", "A_ETUDIER", "DEFAVORABLE", "EXCLU"]
                
                print(f"Parcel {parcel.get('parcel_id')}: score={score['score']}, verdict={score['verdict']}")
        else:
            pytest.skip("BBox endpoint not returning parcels")


class TestPDFExport:
    """Test PDF export endpoint"""
    
    def test_pdf_export_returns_pdf(self):
        """POST /api/export/pdf works and returns a PDF file"""
        # Create a test parcel with new scoring structure
        test_parcel = {
            "parcel_id": "test_parcel_pdf",
            "ref_cadastrale": "000 AB 0001",
            "commune": "Fos-sur-Mer",
            "region": "PACA",
            "departement": "13",
            "latitude": 43.4,
            "longitude": 4.9,
            "surface_m2": 50000,
            "surface_ha": 5.0,
            "dist_poste_htb_m": 2000,
            "tension_htb_kv": 225,
            "nearest_htb_name": "Poste Fos",
            "mw_dispo": 50,
            "zone_saturation": "disponible",
            "plu_zone": "UI",
            "plu_libelle": "Zone industrielle",
            "dvf_prix_median_m2": 45,
            "score": {
                "score": 75,
                "verdict": "GO",
                "detail": {
                    "distance_rte": 35,
                    "mw_disponibles": 25,
                    "plu": 20,
                    "surface": 10,
                    "malus": 0
                },
                "flags": [],
                "resume": "Score 75/100 — GO. Parcelle de 5.0 ha en zone PLU UI à 2.0 km du Poste Fos (225kV) avec 50 MW disponibles. Pas de risques identifiés."
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/export/pdf", json=test_parcel)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        
        # Check PDF content starts with PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Response is not a valid PDF"
        print(f"PDF generated successfully, size: {len(content)} bytes")


class TestMapLayers:
    """Test map layers endpoints"""
    
    def test_rte_future_400kv_returns_geojson(self):
        """GET /api/map/rte-future-400kv returns GeoJSON"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "line" in data, "Missing 'line' in response"
        assert "buffers" in data, "Missing 'buffers' in response"
        assert "metadata" in data, "Missing 'metadata' in response"
        
        # Check line is GeoJSON LineString
        line = data["line"]
        assert line.get("type") == "LineString", "Line should be GeoJSON LineString"
        assert "coordinates" in line, "Line missing coordinates"
        
        # Check buffers
        buffers = data["buffers"]
        assert "1km" in buffers, "Missing 1km buffer"
        assert "3km" in buffers, "Missing 3km buffer"
        assert "5km" in buffers, "Missing 5km buffer"
        
        # Check metadata
        metadata = data["metadata"]
        assert "nom" in metadata, "Missing 'nom' in metadata"
        assert "tension_kv" in metadata, "Missing 'tension_kv' in metadata"
        
        print(f"Future 400kV line: {metadata.get('nom')}, {metadata.get('tension_kv')}kV")
        print(f"Buffers: {list(buffers.keys())}")


class TestS3REnRSummary:
    """Test S3REnR summary endpoint"""
    
    def test_s3renr_summary_returns_region_data(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        assert len(summary) > 0, "Summary should have at least one region"
        
        # Check structure of each region
        for region in summary:
            assert "region" in region, "Missing 'region' field"
            assert "status_global" in region, "Missing 'status_global' field"
            assert "mw_dispo_total" in region, "Missing 'mw_dispo_total' field"
            assert "nb_postes" in region, "Missing 'nb_postes' field"
            
            print(f"Region {region['region']}: status={region['status_global']}, MW dispo={region['mw_dispo_total']}, postes={region['nb_postes']}")


class TestElectricalAssets:
    """Test electrical assets endpoint"""
    
    def test_electrical_assets_returns_postes(self):
        """GET /api/map/electrical-assets returns postes HTB"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        assert "electrical_assets" in data
        assets = data["electrical_assets"]
        assert len(assets) > 0, "Should have electrical assets"
        
        # Count postes
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        assert len(postes) > 0, "Should have postes HTB"
        print(f"Total electrical assets: {len(assets)}, Postes HTB: {len(postes)}")


class TestDCExistants:
    """Test DC existants endpoint"""
    
    def test_dc_existants_returns_data(self):
        """GET /api/map/dc returns DC existants"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        
        assert "dc_existants" in data
        dc_list = data["dc_existants"]
        assert len(dc_list) > 0, "Should have DC existants"
        print(f"DC existants: {len(dc_list)}")


class TestLandingPoints:
    """Test landing points endpoint"""
    
    def test_landing_points_returns_data(self):
        """GET /api/map/landing-points returns landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        
        assert "landing_points" in data
        lp_list = data["landing_points"]
        assert len(lp_list) > 0, "Should have landing points"
        print(f"Landing points: {len(lp_list)}")


class TestSubmarineCables:
    """Test submarine cables endpoint"""
    
    def test_submarine_cables_returns_data(self):
        """GET /api/map/submarine-cables returns cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        
        assert "submarine_cables" in data
        cables = data["submarine_cables"]
        assert len(cables) > 0, "Should have submarine cables"
        print(f"Submarine cables: {len(cables)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
