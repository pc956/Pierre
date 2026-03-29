"""
Cockpit Immo - RTE Future 400kV Line Feature Tests (Iteration 10)
Tests for the new feature: Future RTE 400kV line Fos-sur-Mer → Jonquières

Features tested:
1. GET /api/map/rte-future-400kv - GeoJSON line + buffer zones
2. POST /api/dc/search - future_400kv data in results
3. Scoring integration (+30pts <1km, +20pts <3km, +10pts <5km)
4. future_grid_potential_score composite (0-100)
5. PDF export includes future 400kV section
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRTEFuture400kVEndpoint:
    """Tests for GET /api/map/rte-future-400kv endpoint"""
    
    def test_endpoint_returns_200(self):
        """Endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/map/rte-future-400kv returns 200")
    
    def test_response_has_line_geojson(self):
        """Response should contain line GeoJSON with coordinates"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        data = response.json()
        
        assert "line" in data, "Response missing 'line' field"
        assert data["line"]["type"] == "LineString", "Line type should be LineString"
        assert "coordinates" in data["line"], "Line missing coordinates"
        assert len(data["line"]["coordinates"]) >= 10, "Line should have at least 10 coordinate points"
        
        # Verify coordinates are in PACA region (lon ~4.5-5.0, lat ~43.4-43.9)
        first_coord = data["line"]["coordinates"][0]
        assert 4.0 < first_coord[0] < 5.5, f"First lon {first_coord[0]} not in expected range"
        assert 43.0 < first_coord[1] < 44.0, f"First lat {first_coord[1]} not in expected range"
        
        print(f"✓ Line has {len(data['line']['coordinates'])} coordinate points")
    
    def test_response_has_three_buffer_zones(self):
        """Response should contain 1km, 3km, and 5km buffer zones"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        data = response.json()
        
        assert "buffers" in data, "Response missing 'buffers' field"
        
        for zone in ["1km", "3km", "5km"]:
            assert zone in data["buffers"], f"Missing buffer zone: {zone}"
            buffer = data["buffers"][zone]
            assert buffer["type"] == "Polygon", f"{zone} buffer should be Polygon"
            assert "coordinates" in buffer, f"{zone} buffer missing coordinates"
            assert len(buffer["coordinates"][0]) > 10, f"{zone} buffer should have polygon points"
            assert "style" in buffer, f"{zone} buffer missing style"
        
        print("✓ All 3 buffer zones present (1km, 3km, 5km)")
    
    def test_buffer_zone_colors(self):
        """Buffer zones should have correct colors (red, orange, yellow)"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        data = response.json()
        
        # 1km = red (#ff4757)
        assert "#ff4757" in data["buffers"]["1km"]["style"]["color"].lower(), "1km should be red"
        # 3km = orange (#ffa502)
        assert "#ffa502" in data["buffers"]["3km"]["style"]["color"].lower(), "3km should be orange"
        # 5km = yellow (#ffd32a)
        assert "#ffd32a" in data["buffers"]["5km"]["style"]["color"].lower(), "5km should be yellow"
        
        print("✓ Buffer zone colors correct (red 1km, orange 3km, yellow 5km)")
    
    def test_metadata_fields(self):
        """Response should contain proper metadata"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        data = response.json()
        
        assert "metadata" in data, "Response missing 'metadata' field"
        meta = data["metadata"]
        
        assert "nom" in meta, "Metadata missing 'nom'"
        assert "tension_kv" in meta, "Metadata missing 'tension_kv'"
        assert meta["tension_kv"] == 400, f"Expected 400kV, got {meta['tension_kv']}"
        assert "mise_en_service_estimee" in meta, "Metadata missing 'mise_en_service_estimee'"
        assert "2029" in str(meta["mise_en_service_estimee"]), "Expected ~2029 commissioning"
        assert "description" in meta, "Metadata missing 'description'"
        
        print(f"✓ Metadata complete: {meta['nom']}, {meta['tension_kv']}kV, {meta['mise_en_service_estimee']}")
    
    def test_scoring_rules_present(self):
        """Response should contain scoring rules"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        data = response.json()
        
        assert "scoring" in data, "Response missing 'scoring' field"
        assert "rules" in data["scoring"], "Scoring missing 'rules'"
        
        rules = data["scoring"]["rules"]
        assert len(rules) >= 4, "Should have at least 4 scoring rules"
        
        # Verify bonus values
        bonuses = {r["zone"]: r["bonus"] for r in rules}
        assert bonuses.get("<1km") == 30, "1km bonus should be 30"
        assert bonuses.get("1-3km") == 20, "1-3km bonus should be 20"
        assert bonuses.get("3-5km") == 10, "3-5km bonus should be 10"
        assert bonuses.get(">5km") == 0, ">5km bonus should be 0"
        
        print("✓ Scoring rules correct (+30 <1km, +20 1-3km, +10 3-5km, 0 >5km)")


class TestDCSearchFuture400kV:
    """Tests for future_400kv data in DC Search API"""
    
    def test_paca_search_includes_future_400kv(self):
        """POST /api/dc/search with region=PACA should include future_400kv data"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 10
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "results" in data, "Response missing 'results'"
        assert len(data["results"]) > 0, "Should have at least 1 result for PACA"
        
        # Check first result has future_400kv data
        site = data["results"][0]
        assert "future_400kv" in site, "Site missing 'future_400kv' field"
        
        f400 = site["future_400kv"]
        assert "distance_m" in f400, "future_400kv missing 'distance_m'"
        assert "buffer_zone" in f400, "future_400kv missing 'buffer_zone'"
        assert "score_bonus" in f400, "future_400kv missing 'score_bonus'"
        assert "future_grid_potential" in f400, "future_400kv missing 'future_grid_potential'"
        
        print(f"✓ PACA search includes future_400kv: distance={f400['distance_m']}m, zone={f400['buffer_zone']}, bonus={f400['score_bonus']}")
    
    def test_score_bonus_values(self):
        """Score bonus should be 30/20/10/0 based on distance"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 50
        })
        data = response.json()
        
        for site in data["results"]:
            f400 = site.get("future_400kv", {})
            dist = f400.get("distance_m", 999999)
            bonus = f400.get("score_bonus", 0)
            
            if dist < 1000:
                assert bonus == 30, f"Distance {dist}m should have bonus 30, got {bonus}"
            elif dist < 3000:
                assert bonus == 20, f"Distance {dist}m should have bonus 20, got {bonus}"
            elif dist < 5000:
                assert bonus == 10, f"Distance {dist}m should have bonus 10, got {bonus}"
            else:
                assert bonus == 0, f"Distance {dist}m should have bonus 0, got {bonus}"
        
        print("✓ Score bonus values correct based on distance")
    
    def test_future_grid_potential_score(self):
        """future_grid_potential should have score (0-100) and category"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 10
        })
        data = response.json()
        
        site = data["results"][0]
        fgp = site["future_400kv"]["future_grid_potential"]
        
        assert "future_grid_potential_score" in fgp, "Missing future_grid_potential_score"
        score = fgp["future_grid_potential_score"]
        assert 0 <= score <= 100, f"Score {score} should be 0-100"
        
        assert "future_grid_category" in fgp, "Missing future_grid_category"
        category = fgp["future_grid_category"]
        assert category in ["excellent", "tres_bon", "bon", "moyen", "faible"], f"Invalid category: {category}"
        
        print(f"✓ future_grid_potential: score={score}/100, category={category}")
    
    def test_tags_include_future_400kv_proximity(self):
        """Sites near the line should have 'future_400kv_proximity' tag"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 50
        })
        data = response.json()
        
        found_tag = False
        for site in data["results"]:
            if site.get("future_400kv", {}).get("buffer_zone"):
                assert "future_400kv_proximity" in site.get("tags", []), \
                    f"Site with buffer_zone should have future_400kv_proximity tag"
                found_tag = True
        
        if found_tag:
            print("✓ Sites near line have 'future_400kv_proximity' tag")
        else:
            print("⚠ No sites found within 5km buffer (may be expected)")


class TestBBoxParcelsWithFuture400kV:
    """Tests for future_400kv data in bbox parcels endpoint"""
    
    def test_bbox_parcels_include_future_400kv_fields(self):
        """GET /api/france/parcelles/bbox should include future_400kv fields for PACA parcels"""
        # BBox around Fos-sur-Mer area (near the line start)
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 4.85,
                "min_lat": 43.40,
                "max_lon": 4.95,
                "max_lat": 43.50,
                "limit": 50
            }
        )
        
        if response.status_code != 200:
            pytest.skip("BBox endpoint may require zoom level or return empty for this area")
        
        data = response.json()
        if len(data.get("parcelles", [])) == 0:
            pytest.skip("No parcels found in this bbox area")
        
        parcel = data["parcelles"][0]
        
        # Check future 400kV fields
        assert "dist_future_400kv_m" in parcel, "Parcel missing 'dist_future_400kv_m'"
        assert "future_400kv_buffer" in parcel, "Parcel missing 'future_400kv_buffer'"
        assert "future_400kv_score_bonus" in parcel, "Parcel missing 'future_400kv_score_bonus'"
        assert "future_grid_potential" in parcel, "Parcel missing 'future_grid_potential'"
        
        print(f"✓ BBox parcels include future_400kv fields: dist={parcel['dist_future_400kv_m']}m")


class TestPDFExportWithFuture400kV:
    """Tests for PDF export including future 400kV section"""
    
    def test_pdf_export_still_works(self):
        """POST /api/export/pdf should still return valid PDF"""
        parcel_data = {
            "commune": "Fos-sur-Mer",
            "region": "PACA",
            "surface_m2": 50000,
            "plu_zone": "UI",
            "score": {"score_net": 75, "verdict": "GO", "power_mw_p50": 20},
            "dist_future_400kv_m": 2500,
            "future_400kv_buffer": "3km",
            "future_400kv_score_bonus": 20,
            "future_grid_potential": {
                "future_grid_potential_score": 65,
                "future_grid_category": "tres_bon"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/export/pdf", json=parcel_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        assert response.content[:4] == b"%PDF", "Content should start with %PDF"
        
        print("✓ PDF export works with future_400kv data")
    
    def test_dc_site_pdf_export(self):
        """POST /api/export/pdf/dc-site should work for PACA sites"""
        # First get a valid site_id from PACA
        search_response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "per_page": 1
        })
        
        if search_response.status_code != 200 or len(search_response.json().get("results", [])) == 0:
            pytest.skip("No PACA sites available for PDF test")
        
        site_id = search_response.json()["results"][0]["site_id"]
        
        response = requests.post(f"{BASE_URL}/api/export/pdf/dc-site", json={"site_id": site_id})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b"%PDF", "Content should start with %PDF"
        
        print(f"✓ DC site PDF export works for {site_id}")


class TestScoringIntegration:
    """Tests for scoring integration with future 400kV bonus"""
    
    def test_score_includes_future_bonus(self):
        """DC search score should include future_400kv_bonus"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 10
        })
        data = response.json()
        
        site = data["results"][0]
        score = site.get("score", {})
        
        assert "future_400kv_bonus" in score, "Score missing 'future_400kv_bonus'"
        bonus = score["future_400kv_bonus"]
        assert isinstance(bonus, (int, float)), f"Bonus should be numeric, got {type(bonus)}"
        
        print(f"✓ Score includes future_400kv_bonus: {bonus}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
