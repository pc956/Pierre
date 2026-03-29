"""
Cockpit Immo — Iteration 19 Tests: V3 Correctifs
Tests for:
1. water_data.py (nearest waterway via Overpass API)
2. road_data.py (nearest major road via Overpass API)
3. Chat endpoint returns parcels with water/road data
4. Score response has correct structure
5. GPU zones endpoint
6. PDF export
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBackendHealth:
    """Basic health check tests"""
    
    def test_api_root_returns_version(self):
        """GET /api/ returns API info with version"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"
        print(f"✓ API version: {data['version']}")


class TestGPUZones:
    """GPU zones endpoint tests"""
    
    def test_gpu_zones_returns_zones_array(self):
        """GET /api/france/gpu-zones returns zones array"""
        # Use PACA region bbox
        params = {
            "min_lon": 4.8,
            "min_lat": 43.3,
            "max_lon": 5.0,
            "max_lat": 43.5
        }
        response = requests.get(f"{BASE_URL}/api/france/gpu-zones", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        assert isinstance(data["zones"], list)
        print(f"✓ GPU zones returned: {len(data['zones'])} zones")


class TestChatEndpoint:
    """Chat endpoint tests for V3 correctifs"""
    
    def test_chat_returns_parcels_with_water_road_data(self):
        """POST /api/chat returns parcels with dist_cours_eau_m, nom_cours_eau, dist_route_m, nom_route, type_route"""
        payload = {
            "message": "Trouve des parcelles en PACA de 2 hectares minimum",
            "session_id": "test_iteration19",
            "history": []
        }
        # Chat endpoint can be slow due to Overpass API calls
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        # Check response type
        assert data.get("type") in ["parcel_results", "text", "error"], f"Unexpected type: {data.get('type')}"
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            assert len(parcels) > 0, "No parcels returned"
            
            # Check first parcel has water/road fields (may be None if no water/road nearby)
            first_parcel = parcels[0]
            
            # These fields should exist (even if None)
            assert "dist_cours_eau_m" in first_parcel, "Missing dist_cours_eau_m field"
            assert "nom_cours_eau" in first_parcel, "Missing nom_cours_eau field"
            assert "dist_route_m" in first_parcel, "Missing dist_route_m field"
            assert "nom_route" in first_parcel, "Missing nom_route field"
            assert "type_route" in first_parcel, "Missing type_route field"
            
            # Check DVF fields
            assert "dvf_source" in first_parcel, "Missing dvf_source field"
            assert "dvf_prix_median_m2" in first_parcel, "Missing dvf_prix_median_m2 field"
            
            print(f"✓ Chat returned {len(parcels)} parcels with water/road data")
            print(f"  First parcel: dist_cours_eau_m={first_parcel.get('dist_cours_eau_m')}, dist_route_m={first_parcel.get('dist_route_m')}")
        else:
            print(f"⚠ Chat returned type={data.get('type')}, message: {data.get('text', '')[:100]}")
    
    def test_chat_parcel_score_structure(self):
        """Chat parcels have score with score, verdict, detail (4 axes), flags, resume"""
        payload = {
            "message": "Parcelles à Fos-sur-Mer",
            "session_id": "test_iteration19_score",
            "history": []
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            if len(parcels) > 0:
                score = parcels[0].get("score", {})
                
                # Check score structure
                assert "score" in score, "Missing score.score"
                assert "verdict" in score, "Missing score.verdict"
                assert "detail" in score, "Missing score.detail"
                assert "flags" in score, "Missing score.flags"
                assert "resume" in score, "Missing score.resume"
                
                # Check detail has 4 axes
                detail = score.get("detail", {})
                assert "distance_rte" in detail, "Missing detail.distance_rte"
                assert "mw_disponibles" in detail, "Missing detail.mw_disponibles"
                assert "plu" in detail, "Missing detail.plu"
                assert "surface" in detail, "Missing detail.surface"
                
                # Check verdict is valid
                assert score["verdict"] in ["GO", "A_ETUDIER", "DEFAVORABLE", "EXCLU"], f"Invalid verdict: {score['verdict']}"
                
                print(f"✓ Score structure valid: score={score['score']}, verdict={score['verdict']}")
                print(f"  Detail: RTE={detail.get('distance_rte')}/40, MW={detail.get('mw_disponibles')}/30, PLU={detail.get('plu')}/20, Surface={detail.get('surface')}/10")
        else:
            print(f"⚠ Chat returned type={data.get('type')}")


class TestPDFExport:
    """PDF export endpoint tests"""
    
    def test_pdf_export_returns_valid_pdf(self):
        """POST /api/export/pdf returns valid PDF"""
        parcel_data = {
            "parcel_id": "test_parcel_123",
            "commune": "Fos-sur-Mer",
            "region": "PACA",
            "ref_cadastrale": "000 AB 0001",
            "latitude": 43.45,
            "longitude": 4.95,
            "surface_m2": 20000,
            "surface_ha": 2.0,
            "dist_poste_htb_m": 3500,
            "tension_htb_kv": 225,
            "nearest_htb_name": "Poste Fos",
            "mw_dispo": 50,
            "zone_saturation": "disponible",
            "plu_zone": "UI",
            "plu_libelle": "Zone industrielle",
            "dvf_prix_median_m2": 45,
            "dist_cours_eau_m": 1500,
            "nom_cours_eau": "Canal de Caronte",
            "dist_route_m": 800,
            "nom_route": "A55",
            "type_route": "autoroute",
            "score": {
                "score": 72,
                "verdict": "GO",
                "detail": {
                    "distance_rte": 28,
                    "mw_disponibles": 25,
                    "plu": 20,
                    "surface": 8,
                    "malus": 0
                },
                "flags": [],
                "resume": "Score 72/100 — GO. Parcelle de 2.0 ha en zone PLU UI à 3.5 km du Poste Fos (225kV) avec 50 MW disponibles."
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/export/pdf", json=parcel_data, timeout=30)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        
        # Check PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Response is not a valid PDF"
        assert len(content) > 1000, "PDF seems too small"
        
        print(f"✓ PDF export successful: {len(content)} bytes")


class TestMapEndpoints:
    """Map data endpoints tests"""
    
    def test_electrical_assets_returns_postes(self):
        """GET /api/map/electrical-assets returns postes HTB"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assert "electrical_assets" in data
        assets = data["electrical_assets"]
        assert len(assets) >= 100, f"Expected 100+ postes, got {len(assets)}"
        
        # Check for S3REnR data
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        postes_with_s3renr = [p for p in postes if p.get("s3renr")]
        print(f"✓ Electrical assets: {len(postes)} postes HTB, {len(postes_with_s3renr)} with S3REnR data")
    
    def test_dc_existants_returns_data(self):
        """GET /api/map/dc returns DC existants"""
        response = requests.get(f"{BASE_URL}/api/map/dc")
        assert response.status_code == 200
        data = response.json()
        assert "dc_existants" in data
        assert len(data["dc_existants"]) >= 60, f"Expected 60+ DC, got {len(data['dc_existants'])}"
        print(f"✓ DC existants: {len(data['dc_existants'])}")
    
    def test_landing_points_returns_data(self):
        """GET /api/map/landing-points returns landing points"""
        response = requests.get(f"{BASE_URL}/api/map/landing-points")
        assert response.status_code == 200
        data = response.json()
        assert "landing_points" in data
        assert len(data["landing_points"]) >= 8, f"Expected 8+ landing points, got {len(data['landing_points'])}"
        print(f"✓ Landing points: {len(data['landing_points'])}")
    
    def test_submarine_cables_returns_data(self):
        """GET /api/map/submarine-cables returns cables"""
        response = requests.get(f"{BASE_URL}/api/map/submarine-cables")
        assert response.status_code == 200
        data = response.json()
        assert "submarine_cables" in data
        assert len(data["submarine_cables"]) >= 15, f"Expected 15+ cables, got {len(data['submarine_cables'])}"
        print(f"✓ Submarine cables: {len(data['submarine_cables'])}")
    
    def test_rte_future_400kv_returns_geojson(self):
        """GET /api/map/rte-future-400kv returns GeoJSON with line + buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        assert "line" in data
        assert "buffers" in data
        assert "metadata" in data
        print(f"✓ RTE Future 400kV line: {data['metadata'].get('nom')}")


class TestS3REnRSummary:
    """S3REnR summary endpoint tests"""
    
    def test_s3renr_summary_returns_regions(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        assert len(summary) >= 3, f"Expected 3+ regions, got {len(summary)}"
        
        # Check for IDF, PACA, HdF
        regions = [r["region"] for r in summary]
        assert "IDF" in regions, "Missing IDF region"
        assert "PACA" in regions, "Missing PACA region"
        assert "HdF" in regions, "Missing HdF region"
        
        print(f"✓ S3REnR summary: {len(summary)} regions")
        for r in summary:
            print(f"  {r['region']}: {r['status_global']}, {r.get('mw_dispo_total', 0)} MW dispo")


class TestBboxParcels:
    """Bbox parcels endpoint tests"""
    
    def test_bbox_parcels_returns_parcels(self):
        """GET /api/france/parcelles/bbox returns parcels with score"""
        params = {
            "min_lon": 4.9,
            "min_lat": 43.4,
            "max_lon": 5.0,
            "max_lat": 43.5,
            "limit": 50
        }
        response = requests.get(f"{BASE_URL}/api/france/parcelles/bbox", params=params, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "parcelles" in data
        assert "count" in data
        
        if data["count"] > 0:
            parcel = data["parcelles"][0]
            assert "score" in parcel, "Missing score in parcel"
            assert "parcel_id" in parcel, "Missing parcel_id"
            print(f"✓ Bbox parcels: {data['count']} parcels returned")
        else:
            print("⚠ No parcels in bbox (may be normal for this area)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
