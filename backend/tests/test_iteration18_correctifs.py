"""
Iteration 18 - Test 3 Correctifs Applied
1) 5 new map layers (industrial zones GPU, flood zones, S3REnR MW heatmap, waterways WMS, road overlay)
2) Real DVF via Cerema API with 3-level cascade (commune API -> dept hardcode -> region fallback)
3) Complete cleanup of project_type from server.py, models.py (removed ProjectType enum, updated Verdict enum)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://project-platform-2.preview.emergentagent.com')


class TestCorrectif1_MapLayers:
    """Test new map layers: GPU zones, flood zones, heatmap MW, waterways, roads"""
    
    def test_gpu_zones_endpoint_exists(self):
        """GET /api/france/gpu-zones returns industrial zones"""
        response = requests.get(
            f"{BASE_URL}/api/france/gpu-zones",
            params={
                "min_lon": 5.0,
                "min_lat": 43.0,
                "max_lon": 6.0,
                "max_lat": 44.0
            }
        )
        assert response.status_code == 200, f"GPU zones endpoint failed: {response.text}"
        data = response.json()
        assert "zones" in data, "Response should contain 'zones' array"
        print(f"GPU zones endpoint returned {len(data['zones'])} industrial zones")
    
    def test_electrical_assets_for_heatmap(self):
        """GET /api/map/electrical-assets returns postes with s3renr data for heatmap"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        assert len(postes) > 0, "Should have HTB postes"
        
        # Check some postes have s3renr data for heatmap
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        print(f"Found {len(postes_with_s3renr)}/{len(postes)} postes with S3REnR data for heatmap")
        
        # Verify s3renr structure
        if postes_with_s3renr:
            s3renr = postes_with_s3renr[0]["s3renr"]
            assert "etat" in s3renr, "s3renr should have 'etat' field"
            print(f"Sample s3renr: etat={s3renr.get('etat')}, mw_dispo={s3renr.get('mw_dispo')}")


class TestCorrectif2_DVFCascade:
    """Test DVF real API with 3-level cascade"""
    
    def test_dvf_commune_endpoint(self):
        """GET /api/dvf/commune/{code_insee} returns DVF data"""
        # Test with a known commune (Marseille)
        response = requests.get(f"{BASE_URL}/api/dvf/commune/13055")
        assert response.status_code == 200
        data = response.json()
        assert "prix_median_m2" in data, "Should have prix_median_m2"
        assert "source" in data, "Should have source field"
        print(f"DVF commune 13055: {data.get('prix_median_m2')}€/m², source={data.get('source')}")
    
    def test_dvf_region_endpoint(self):
        """GET /api/dvf/region/{region} returns aggregated DVF data"""
        response = requests.get(f"{BASE_URL}/api/dvf/region/PACA")
        assert response.status_code == 200
        data = response.json()
        assert "prix_moyen_pondere_m2" in data, "Should have prix_moyen_pondere_m2"
        assert "departements" in data, "Should have departements list"
        print(f"DVF region PACA: {data.get('prix_moyen_pondere_m2')}€/m², {len(data.get('departements', []))} départements")
    
    def test_chat_returns_dvf_source(self):
        """POST /api/chat returns parcels with dvf_source field"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve 3 parcelles en PACA",
                "session_id": "test_dvf_cascade",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            if parcels:
                # Check dvf_source field exists
                parcel = parcels[0]
                assert "dvf_prix_median_m2" in parcel, "Parcel should have dvf_prix_median_m2"
                assert "dvf_source" in parcel, "Parcel should have dvf_source field"
                print(f"Parcel DVF: {parcel.get('dvf_prix_median_m2')}€/m², source={parcel.get('dvf_source')}")
        else:
            print(f"Chat returned type={data.get('type')}, skipping DVF check")


class TestCorrectif3_ProjectTypeCleanup:
    """Test project_type completely removed from API signatures"""
    
    def test_api_root(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("version") == "1.0.0"
        print(f"API root: {data}")
    
    def test_parcels_no_project_type(self):
        """GET /api/parcels works without project_type param"""
        response = requests.get(f"{BASE_URL}/api/parcels", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "parcels" in data
        print(f"GET /api/parcels returned {len(data.get('parcels', []))} parcels")
    
    def test_map_parcels_no_project_type(self):
        """GET /api/map/parcels works without project_type param"""
        response = requests.get(
            f"{BASE_URL}/api/map/parcels",
            params={
                "min_lng": 2.0,
                "min_lat": 48.0,
                "max_lng": 3.0,
                "max_lat": 49.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "parcels" in data
        print(f"GET /api/map/parcels returned {len(data.get('parcels', []))} parcels")
    
    def test_france_parcelles_bbox_no_project_type(self):
        """GET /api/france/parcelles/bbox works without project_type param"""
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 5.0,
                "min_lat": 43.0,
                "max_lon": 5.1,
                "max_lat": 43.1,
                "limit": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "parcelles" in data
        print(f"GET /api/france/parcelles/bbox returned {len(data.get('parcelles', []))} parcelles")
    
    def test_parcel_score_simplified(self):
        """GET /api/parcels/{id}/score works without project_type in URL"""
        # First get a parcel ID
        response = requests.get(f"{BASE_URL}/api/parcels", params={"limit": 1})
        if response.status_code == 200:
            parcels = response.json().get("parcels", [])
            if parcels:
                parcel_id = parcels[0].get("parcel_id")
                # Test simplified score endpoint
                score_response = requests.get(f"{BASE_URL}/api/parcels/{parcel_id}/score")
                assert score_response.status_code in [200, 404], f"Score endpoint failed: {score_response.text}"
                if score_response.status_code == 200:
                    score_data = score_response.json()
                    print(f"Score endpoint returned: score={score_data.get('score')}, verdict={score_data.get('verdict')}")
                else:
                    print("No parcel found for score test")
            else:
                print("No parcels in database for score test")
        else:
            print("Could not fetch parcels for score test")


class TestScoreFormat:
    """Test score response format: score.score (not score_net), correct verdicts"""
    
    def test_score_structure(self):
        """Score should have: score, verdict, detail, flags, resume"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve 2 parcelles en PACA",
                "session_id": "test_score_format",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            if parcels:
                parcel = parcels[0]
                score = parcel.get("score", {})
                
                # Check score structure
                assert "score" in score, "Score should have 'score' field (not score_net)"
                assert "verdict" in score, "Score should have 'verdict' field"
                assert "detail" in score, "Score should have 'detail' field"
                assert "flags" in score, "Score should have 'flags' field"
                assert "resume" in score, "Score should have 'resume' field"
                
                # Check verdict values
                valid_verdicts = ["GO", "A_ETUDIER", "DEFAVORABLE", "EXCLU"]
                assert score["verdict"] in valid_verdicts, f"Verdict should be one of {valid_verdicts}, got {score['verdict']}"
                
                # Check detail has 4 axes
                detail = score.get("detail", {})
                expected_axes = ["distance_rte", "mw_disponibles", "plu", "surface"]
                for axis in expected_axes:
                    assert axis in detail, f"Detail should have '{axis}' axis"
                
                print(f"Score structure verified: score={score['score']}, verdict={score['verdict']}")
                print(f"Detail axes: {list(detail.keys())}")
        else:
            print(f"Chat returned type={data.get('type')}, skipping score format check")
    
    def test_verdict_labels(self):
        """Verdicts should be GO, A_ETUDIER, DEFAVORABLE, EXCLU (not CONDITIONNEL or NO_GO)"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve 5 parcelles en PACA",
                "session_id": "test_verdict_labels",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            verdicts_found = set()
            for p in parcels:
                verdict = p.get("score", {}).get("verdict")
                if verdict:
                    verdicts_found.add(verdict)
                    # Ensure old verdicts are not used
                    assert verdict != "CONDITIONNEL", "Should not use CONDITIONNEL verdict"
                    assert verdict != "NO_GO", "Should not use NO_GO verdict"
            
            print(f"Verdicts found: {verdicts_found}")


class TestPDFExport:
    """Test PDF export works"""
    
    def test_pdf_export(self):
        """POST /api/export/pdf returns valid PDF"""
        test_parcel = {
            "parcel_id": "test_parcel_123",
            "commune": "Fos-sur-Mer",
            "region": "PACA",
            "surface_ha": 5.0,
            "latitude": 43.45,
            "longitude": 4.95,
            "score": {
                "score": 75,
                "verdict": "GO",
                "detail": {
                    "distance_rte": 35,
                    "mw_disponibles": 25,
                    "plu": 10,
                    "surface": 5
                },
                "flags": [],
                "resume": "Excellent site pour data center"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json=test_parcel,
            timeout=30
        )
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF content type"
        assert len(response.content) > 1000, "PDF should have substantial content"
        print(f"PDF export successful: {len(response.content)} bytes")


class TestMapInfrastructure:
    """Test map infrastructure endpoints"""
    
    def test_map_dc(self):
        """GET /api/map/dc returns DC existants"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        dc_list = data.get("dc_existants", [])
        assert len(dc_list) > 0, "Should have DC existants"
        print(f"Map DC: {len(dc_list)} data centers")
    
    def test_map_landing_points(self):
        """GET /api/map/landing-points returns landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        lp_list = data.get("landing_points", [])
        assert len(lp_list) > 0, "Should have landing points"
        print(f"Map landing points: {len(lp_list)} points")
    
    def test_map_submarine_cables(self):
        """GET /api/map/submarine-cables returns cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        cables = data.get("submarine_cables", [])
        assert len(cables) > 0, "Should have submarine cables"
        print(f"Map submarine cables: {len(cables)} cables")
    
    def test_map_electrical_assets(self):
        """GET /api/map/electrical-assets returns postes and lignes"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        assert len(assets) > 0, "Should have electrical assets"
        
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        lignes_400 = [a for a in assets if a.get("type") == "ligne_400kv"]
        lignes_225 = [a for a in assets if a.get("type") == "ligne_225kv"]
        
        print(f"Electrical assets: {len(postes)} postes HTB, {len(lignes_400)} lignes 400kV, {len(lignes_225)} lignes 225kV")
    
    def test_rte_future_400kv(self):
        """GET /api/map/rte-future-400kv returns future line with buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        assert "line" in data, "Should have 'line' GeoJSON"
        assert "buffers" in data, "Should have 'buffers' dict"
        assert "metadata" in data, "Should have 'metadata'"
        
        buffers = data.get("buffers", {})
        assert "1km" in buffers, "Should have 1km buffer"
        assert "3km" in buffers, "Should have 3km buffer"
        assert "5km" in buffers, "Should have 5km buffer"
        
        print(f"RTE future 400kV: {data.get('metadata', {}).get('nom')}")


class TestS3REnRSummary:
    """Test S3REnR summary endpoint"""
    
    def test_s3renr_summary(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", [])
        assert len(summary) > 0, "Should have S3REnR summary"
        
        regions = [s["region"] for s in summary]
        assert "IDF" in regions, "Should have IDF region"
        assert "PACA" in regions, "Should have PACA region"
        assert "HdF" in regions, "Should have HdF region"
        
        for s in summary:
            print(f"S3REnR {s['region']}: {s.get('status_global')}, {s.get('mw_dispo_total')} MW dispo")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
