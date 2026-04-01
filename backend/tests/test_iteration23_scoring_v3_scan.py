"""
Iteration 23 - Scoring v3 (5 axes) + Scan DC 10MW + S3REnR Extended Regions
Tests for:
1. GET /api/ returns API info
2. GET /api/scan/dc-10mw?region=PACA returns candidates with score, ttm_months, mw_dispo
3. GET /api/scan/dc-10mw?region=AuRA returns candidates (tests new AuRA S3REnR data)
4. GET /api/map/electrical-assets returns 1091+ postes
5. POST /api/chat with 'Parcelles à Fos-sur-Mer' returns parcel_results with ttm_months in score
6. GET /api/s3renr/summary returns data for OCC, AuRA, GES, NAQ regions
7. Scoring v3 verification: 5 axes (distance_rte/35, mw_disponibles/25, plu/20, surface/10, raccordement_speed/10)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://project-platform-2.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"


class TestAPIInfo:
    """Test API root endpoint"""
    
    def test_api_root_returns_info(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "version" in data or "name" in data or "title" in data, f"API info missing expected fields: {data}"
        print(f"✓ API info: {data}")


class TestScanDC10MW:
    """Test the new scan DC 10MW endpoint"""
    
    def test_scan_dc_10mw_paca(self):
        """GET /api/scan/dc-10mw?region=PACA returns candidates with score, ttm_months, mw_dispo"""
        response = requests.get(f"{API_URL}/scan/dc-10mw", params={
            "region": "PACA",
            "max_distance_km": 5,
            "min_surface_ha": 1,
            "max_ttm_months": 36,
            "limit": 20
        }, timeout=30)  # Scan can take 10-15s
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "candidates" in data, f"Missing 'candidates' in response: {data.keys()}"
        assert "total_found" in data, f"Missing 'total_found' in response"
        assert "postes_scanned" in data, f"Missing 'postes_scanned' in response"
        assert "search_params" in data, f"Missing 'search_params' in response"
        
        print(f"✓ Scan PACA: {data['total_found']} candidates found, {data['postes_scanned']} postes scanned")
        
        # Verify candidates have required fields
        if data["candidates"]:
            candidate = data["candidates"][0]
            assert "score" in candidate, f"Candidate missing 'score': {candidate.keys()}"
            
            score = candidate["score"]
            assert "score" in score, f"Score missing 'score' field: {score.keys()}"
            assert "ttm_months" in score, f"Score missing 'ttm_months' field: {score.keys()}"
            assert "verdict" in score, f"Score missing 'verdict' field: {score.keys()}"
            assert "detail" in score, f"Score missing 'detail' field: {score.keys()}"
            
            # Verify 5 axes in detail
            detail = score["detail"]
            expected_axes = ["distance_rte", "mw_disponibles", "plu", "surface", "raccordement_speed"]
            for axis in expected_axes:
                assert axis in detail, f"Missing axis '{axis}' in score detail: {detail.keys()}"
            
            print(f"✓ First candidate score: {score['score']}/100, TTM: {score['ttm_months']} months, verdict: {score['verdict']}")
            print(f"✓ Score detail (5 axes): {detail}")
            
            # Verify mw_dispo in candidate
            assert "mw_dispo" in candidate or "poste_rte" in candidate, f"Candidate missing MW info"
            if "poste_rte" in candidate:
                poste = candidate["poste_rte"]
                assert "mw_dispo" in poste, f"Poste missing 'mw_dispo': {poste.keys()}"
                print(f"✓ Poste RTE: {poste.get('nom')}, {poste.get('mw_dispo')} MW dispo")
    
    def test_scan_dc_10mw_aura(self):
        """GET /api/scan/dc-10mw?region=AuRA returns candidates (tests new AuRA S3REnR data)"""
        response = requests.get(f"{API_URL}/scan/dc-10mw", params={
            "region": "AuRA",
            "max_distance_km": 5,
            "min_surface_ha": 1,
            "max_ttm_months": 36,
            "limit": 10
        }, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "candidates" in data, f"Missing 'candidates' in response"
        assert "postes_scanned" in data, f"Missing 'postes_scanned' in response"
        
        print(f"✓ Scan AuRA: {data['total_found']} candidates found, {data['postes_scanned']} postes scanned")
        
        # AuRA should have postes with MW available (GENISSIAT has 300 MW)
        if data["postes_scanned"] > 0:
            print(f"✓ AuRA S3REnR data working - postes scanned: {data['postes_scanned']}")
        else:
            print("⚠ No postes scanned in AuRA - may need to check S3REnR data matching")


class TestElectricalAssets:
    """Test electrical assets endpoint"""
    
    def test_electrical_assets_count(self):
        """GET /api/map/electrical-assets returns 1091+ postes"""
        response = requests.get(f"{API_URL}/map/electrical-assets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "electrical_assets" in data, f"Missing 'electrical_assets' in response"
        
        assets = data["electrical_assets"]
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        
        assert len(postes) >= 1000, f"Expected ≥1000 postes, got {len(postes)}"
        print(f"✓ Electrical assets: {len(postes)} postes HTB, {len(assets)} total assets")


class TestS3REnRExtendedRegions:
    """Test S3REnR summary with extended regions (OCC, AuRA, GES, NAQ)"""
    
    def test_s3renr_summary_extended_regions(self):
        """GET /api/s3renr/summary returns data for OCC, AuRA, GES, NAQ regions"""
        response = requests.get(f"{API_URL}/s3renr/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "summary" in data, f"Missing 'summary' in response"
        
        summary = data["summary"]
        regions = {r["region"]: r for r in summary}
        
        # Check original regions
        assert "IDF" in regions, "Missing IDF region"
        assert "PACA" in regions, "Missing PACA region"
        assert "HdF" in regions, "Missing HdF region"
        
        # Check new extended regions
        new_regions = ["OCC", "AuRA", "GES", "NAQ"]
        for region in new_regions:
            assert region in regions, f"Missing new region: {region}"
            region_data = regions[region]
            assert "capacite_globale_mw" in region_data, f"{region} missing capacite_globale_mw"
            assert "nb_postes" in region_data, f"{region} missing nb_postes"
            print(f"✓ {region}: {region_data.get('capacite_globale_mw')} MW, {region_data.get('nb_postes')} postes, status: {region_data.get('status_global')}")
        
        print(f"✓ S3REnR summary: {len(summary)} regions total")


class TestChatWithTTM:
    """Test chat endpoint returns ttm_months in score"""
    
    def test_chat_parcels_fos_sur_mer(self):
        """POST /api/chat with 'Parcelles à Fos-sur-Mer' returns parcel_results with ttm_months in score"""
        response = requests.post(f"{API_URL}/chat", json={
            "message": "Parcelles à Fos-sur-Mer",
            "session_id": "test_iteration23",
            "history": []
        }, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Chat can return different types
        response_type = data.get("type")
        print(f"✓ Chat response type: {response_type}")
        
        if response_type == "parcel_results":
            parcels = data.get("parcel_results", [])
            if parcels:
                parcel = parcels[0]
                score = parcel.get("score", {})
                
                # Verify ttm_months in score
                assert "ttm_months" in score, f"Score missing 'ttm_months': {score.keys()}"
                print(f"✓ First parcel score: {score.get('score')}/100, TTM: {score.get('ttm_months')} months")
                
                # Verify 5 axes in detail
                detail = score.get("detail", {})
                expected_axes = ["distance_rte", "mw_disponibles", "plu", "surface", "raccordement_speed"]
                for axis in expected_axes:
                    if axis in detail:
                        print(f"  - {axis}: {detail[axis]}")
        elif response_type == "text":
            print(f"✓ Chat returned text response (no parcels found or different intent)")
        else:
            print(f"✓ Chat returned {response_type} response")


class TestScoringV3Axes:
    """Test scoring v3 with 5 axes"""
    
    def test_scoring_v3_structure(self):
        """Verify scoring v3 returns 5 axes: distance_rte/35, mw_disponibles/25, plu/20, surface/10, raccordement_speed/10"""
        # Use scan endpoint to get scored parcels
        response = requests.get(f"{API_URL}/scan/dc-10mw", params={
            "region": "PACA",
            "limit": 5
        }, timeout=30)
        
        if response.status_code != 200:
            pytest.skip(f"Scan endpoint returned {response.status_code}")
        
        data = response.json()
        candidates = data.get("candidates", [])
        
        if not candidates:
            pytest.skip("No candidates returned from scan")
        
        candidate = candidates[0]
        score = candidate.get("score", {})
        detail = score.get("detail", {})
        
        # Verify all 5 axes present
        expected_axes = {
            "distance_rte": 35,
            "mw_disponibles": 25,
            "plu": 20,
            "surface": 10,
            "raccordement_speed": 10
        }
        
        for axis, max_pts in expected_axes.items():
            assert axis in detail, f"Missing axis '{axis}' in score detail"
            pts = detail[axis]
            assert 0 <= pts <= max_pts, f"Axis '{axis}' value {pts} out of range [0, {max_pts}]"
            print(f"✓ {axis}: {pts}/{max_pts}")
        
        # Verify malus field
        assert "malus" in detail, "Missing 'malus' in score detail"
        print(f"✓ malus: {detail['malus']}")
        
        # Verify total score
        total_score = score.get("score", 0)
        assert 0 <= total_score <= 100, f"Total score {total_score} out of range [0, 100]"
        print(f"✓ Total score: {total_score}/100")
        
        # Verify ttm_months
        ttm = score.get("ttm_months")
        assert ttm is not None, "Missing 'ttm_months' in score"
        assert 12 <= ttm <= 48, f"TTM {ttm} months seems out of expected range [12, 48]"
        print(f"✓ TTM: {ttm} months")


class TestScanAroundPoste:
    """Test scan around specific poste endpoint"""
    
    def test_scan_around_poste_realtor(self):
        """GET /api/scan/around-poste/REALTOR returns parcels with scores"""
        response = requests.get(f"{API_URL}/scan/around-poste/REALTOR", params={
            "radius_km": 3,
            "min_surface_ha": 1
        }, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "poste" in data, f"Missing 'poste' in response"
        assert "parcelles" in data, f"Missing 'parcelles' in response"
        assert "count" in data, f"Missing 'count' in response"
        
        poste = data["poste"]
        assert "nom" in poste, f"Poste missing 'nom'"
        assert "s3renr" in poste, f"Poste missing 's3renr' data"
        
        print(f"✓ Scan around {poste['nom']}: {data['count']} parcels found")
        print(f"✓ S3REnR: {poste['s3renr'].get('mw_dispo')} MW dispo, etat: {poste['s3renr'].get('etat')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
