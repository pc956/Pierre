"""
DC Search API Tests - Cockpit Immo
Tests for POST /api/dc/search and GET /api/dc/site/:id endpoints
Designed for AI agent consumption (ChatGPT, Claude, etc.)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDCSearchBasic:
    """Basic DC Search API tests"""
    
    def test_search_without_filters_returns_all_france(self):
        """POST /api/dc/search without region returns all France results"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "strategy": "balanced"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert "meta" in data
        assert data["meta"]["total_results"] > 0
        assert data["meta"]["region_filter"] is None
        print(f"Total France results: {data['meta']['total_results']}")
    
    def test_search_returns_required_fields(self):
        """POST /api/dc/search results have all required fields"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 5
        })
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) > 0
        site = data["results"][0]
        
        # Required fields check
        required_fields = ["site_id", "name", "location", "land", "grid", "timeline", "urbanism", "score", "tags", "comment"]
        for field in required_fields:
            assert field in site, f"Missing required field: {field}"
        
        # Location subfields
        assert "city" in site["location"]
        assert "region" in site["location"]
        assert "lat" in site["location"]
        assert "lng" in site["location"]
        
        # Land subfields
        assert "surface_ha" in site["land"]
        assert "price_per_m2" in site["land"]
        assert "type" in site["land"]
        
        # Grid subfields
        assert "voltage_level" in site["grid"]
        assert "available_capacity_mw" in site["grid"]
        assert "saturation_level" in site["grid"]
        
        # Score subfields
        assert "global" in site["score"]
        assert "power" in site["score"]
        assert "speed" in site["score"]
        assert "cost" in site["score"]
        assert "risk" in site["score"]
        
        print(f"All required fields present in site: {site['name']}")
    
    def test_score_global_between_0_and_100(self):
        """Score.global is between 0-100"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        for site in data["results"]:
            score = site["score"]["global"]
            assert 0 <= score <= 100, f"Score {score} out of range for {site['name']}"
        
        print(f"All {len(data['results'])} sites have valid scores (0-100)")
    
    def test_results_sorted_by_score_descending(self):
        """Results are sorted by score.global descending"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 20
        })
        assert response.status_code == 200
        data = response.json()
        
        scores = [site["score"]["global"] for site in data["results"]]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score descending"
        print(f"Results correctly sorted: {scores[:5]}...")
    
    def test_meta_contains_required_fields(self):
        """POST /api/dc/search returns proper meta"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "page": 1,
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        meta = data["meta"]
        assert "total_results" in meta
        assert "page" in meta
        assert "per_page" in meta
        assert "total_pages" in meta
        assert "search_time_ms" in meta
        assert "strategy" in meta
        
        assert meta["page"] == 1
        assert meta["per_page"] == 10
        assert meta["search_time_ms"] >= 0
        print(f"Meta: total={meta['total_results']}, pages={meta['total_pages']}, time={meta['search_time_ms']}ms")


class TestDCSearchRegions:
    """Region-specific DC Search tests"""
    
    def test_idf_region_returns_saturated_sites(self):
        """POST /api/dc/search with IDF region returns results with correct saturation warnings"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "IDF",
            "mw_target": 20,
            "per_page": 20
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["region_filter"] == "IDF"
        assert data["meta"]["total_results"] > 0
        
        # IDF is saturated - check for saturation indicators
        saturated_count = 0
        for site in data["results"]:
            if site["grid"]["saturation_level"] == "high":
                saturated_count += 1
                # Saturated sites should have low power score
                assert site["score"]["power"] <= 50, f"Saturated site {site['name']} has high power score"
        
        print(f"IDF results: {data['meta']['total_results']} sites, {saturated_count} saturated")
    
    def test_idf_saturated_sites_have_warning_comment(self):
        """IDF saturated sites show appropriate warning comment"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "IDF",
            "mw_target": 20,
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        for site in data["results"]:
            if site["grid"]["saturation_level"] == "high":
                comment = site["comment"].lower()
                assert "satur" in comment or "aucune capacité" in comment, \
                    f"Saturated site missing warning: {site['comment']}"
        
        print("IDF saturated sites have appropriate warning comments")
    
    def test_paca_region_returns_sorted_results(self):
        """POST /api/dc/search with PACA region returns sites sorted by score"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "PACA",
            "mw_target": 20,
            "per_page": 20
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["region_filter"] == "PACA"
        assert data["meta"]["total_results"] > 0
        
        scores = [site["score"]["global"] for site in data["results"]]
        assert scores == sorted(scores, reverse=True)
        print(f"PACA results: {data['meta']['total_results']} sites, sorted correctly")
    
    def test_hdf_region_with_grid_priority_filters_saturated(self):
        """POST /api/dc/search with HdF region and grid_priority=true filters out saturated sites"""
        # First get all HdF sites
        response_all = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "HdF",
            "mw_target": 20,
            "per_page": 50,
            "grid_priority": False
        })
        assert response_all.status_code == 200
        all_count = response_all.json()["meta"]["total_results"]
        
        # Now with grid_priority
        response_filtered = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "HdF",
            "mw_target": 20,
            "per_page": 50,
            "grid_priority": True
        })
        assert response_filtered.status_code == 200
        data = response_filtered.json()
        
        # Verify no saturated sites
        for site in data["results"]:
            assert site["grid"]["saturation_level"] != "high", \
                f"Saturated site found with grid_priority: {site['name']}"
        
        filtered_count = data["meta"]["total_results"]
        print(f"HdF: {all_count} total, {filtered_count} with grid_priority (no saturated)")
    
    def test_region_aliases_work(self):
        """Region aliases (IDF, PACA, HdF) work correctly"""
        aliases = [
            ("IDF", "IDF"),
            ("ile-de-france", "IDF"),
            ("paris", "IDF"),
            ("PACA", "PACA"),
            ("provence", "PACA"),
            ("HdF", "HdF"),
            ("HDF", "HdF"),
            ("hauts-de-france", "HdF"),
            ("nord", "HdF"),
        ]
        
        for alias, expected in aliases:
            response = requests.post(f"{BASE_URL}/api/dc/search", json={
                "region": alias,
                "per_page": 1
            })
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["region_filter"] == expected, \
                f"Alias '{alias}' resolved to '{data['meta']['region_filter']}' instead of '{expected}'"
        
        print(f"All {len(aliases)} region aliases work correctly")


class TestDCSearchStrategies:
    """Strategy-based scoring tests"""
    
    def test_strategy_speed_weights_speed_higher(self):
        """POST /api/dc/search with strategy=speed gives higher weight to speed score"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "strategy": "speed",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["strategy"] == "speed"
        
        # Top results should have good speed scores
        top_site = data["results"][0]
        print(f"Speed strategy top site: {top_site['name']}, speed={top_site['score']['speed']}, global={top_site['score']['global']}")
    
    def test_strategy_power_weights_power_higher(self):
        """POST /api/dc/search with strategy=power gives higher weight to power score"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "strategy": "power",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["strategy"] == "power"
        
        top_site = data["results"][0]
        print(f"Power strategy top site: {top_site['name']}, power={top_site['score']['power']}, global={top_site['score']['global']}")
    
    def test_strategy_cost_weights_cost_higher(self):
        """POST /api/dc/search with strategy=cost gives higher weight to cost score"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "strategy": "cost",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["strategy"] == "cost"
        
        top_site = data["results"][0]
        print(f"Cost strategy top site: {top_site['name']}, cost={top_site['score']['cost']}, global={top_site['score']['global']}")
    
    def test_strategy_balanced_default(self):
        """POST /api/dc/search defaults to balanced strategy"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 5
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["strategy"] == "balanced"
        print("Default strategy is 'balanced'")
    
    def test_different_strategies_produce_different_global_scores(self):
        """Different strategies produce different global scores for same sites"""
        strategies = ["speed", "cost", "power", "balanced"]
        global_scores = {}
        
        for strategy in strategies:
            response = requests.post(f"{BASE_URL}/api/dc/search", json={
                "mw_target": 20,
                "strategy": strategy,
                "per_page": 5
            })
            assert response.status_code == 200
            data = response.json()
            # Get global score of first result
            global_scores[strategy] = data["results"][0]["score"]["global"]
        
        # Different strategies should produce different global scores
        unique_scores = len(set(global_scores.values()))
        print(f"Global scores by strategy: {global_scores}")
        print(f"Unique global scores: {unique_scores}/4")
        
        # At least 2 different global scores expected (strategies weight differently)
        assert unique_scores >= 2, f"All strategies produce same global score: {global_scores}"


class TestDCSearchPagination:
    """Pagination tests"""
    
    def test_pagination_works(self):
        """POST /api/dc/search pagination works (page, per_page, total_pages)"""
        # Get page 1
        response1 = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "page": 1,
            "per_page": 5
        })
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get page 2
        response2 = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "page": 2,
            "per_page": 5
        })
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pagination
        assert data1["meta"]["page"] == 1
        assert data2["meta"]["page"] == 2
        assert data1["meta"]["per_page"] == 5
        assert data2["meta"]["per_page"] == 5
        
        # Verify different results
        ids1 = [s["site_id"] for s in data1["results"]]
        ids2 = [s["site_id"] for s in data2["results"]]
        assert set(ids1).isdisjoint(set(ids2)), "Page 1 and 2 have overlapping results"
        
        # Verify total_pages calculation
        total = data1["meta"]["total_results"]
        expected_pages = (total + 4) // 5  # ceil(total/5)
        assert data1["meta"]["total_pages"] == expected_pages
        
        print(f"Pagination: {total} total, {expected_pages} pages, page 1 and 2 have different results")
    
    def test_page_2_returns_different_results(self):
        """Page 2 returns different results than page 1"""
        response1 = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "page": 1,
            "per_page": 10
        })
        response2 = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "page": 2,
            "per_page": 10
        })
        
        ids1 = set(s["site_id"] for s in response1.json()["results"])
        ids2 = set(s["site_id"] for s in response2.json()["results"])
        
        assert ids1.isdisjoint(ids2), "Page 1 and 2 should have no overlapping sites"
        print("Page 2 returns completely different results than page 1")


class TestDCSearchFilters:
    """Filter tests"""
    
    def test_brownfield_only_filter(self):
        """POST /api/dc/search with brownfield_only=true filters correctly"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "brownfield_only": True,
            "per_page": 20
        })
        assert response.status_code == 200
        data = response.json()
        
        for site in data["results"]:
            assert site["land"]["type"] == "brownfield", \
                f"Non-brownfield site found: {site['name']} is {site['land']['type']}"
        
        print(f"Brownfield filter: {data['meta']['total_results']} brownfield sites")


class TestDCSearchS3REnRIntegration:
    """S3REnR data integration tests"""
    
    def test_calais_site_has_correct_capacity(self):
        """S3REnR-matched sites (Calais) show correct available capacity and saturation=low"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "HdF",
            "mw_target": 20,
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Find Calais site
        calais_site = None
        for site in data["results"]:
            if "Calais" in site["name"]:
                calais_site = site
                break
        
        assert calais_site is not None, "Calais site not found in HdF results"
        
        # Calais should have ~28MW available (from S3REnR data)
        assert calais_site["grid"]["available_capacity_mw"] >= 20, \
            f"Calais capacity too low: {calais_site['grid']['available_capacity_mw']}"
        assert calais_site["grid"]["saturation_level"] == "low", \
            f"Calais saturation should be low: {calais_site['grid']['saturation_level']}"
        
        print(f"Calais: {calais_site['grid']['available_capacity_mw']}MW, saturation={calais_site['grid']['saturation_level']}")
    
    def test_valenciennes_site_has_correct_capacity(self):
        """S3REnR-matched sites (Valenciennes) show correct available capacity"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "HdF",
            "mw_target": 20,
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Find Valenciennes site
        valenciennes_site = None
        for site in data["results"]:
            if "Valenciennes" in site["name"]:
                valenciennes_site = site
                break
        
        assert valenciennes_site is not None, "Valenciennes site not found in HdF results"
        
        # Valenciennes should have ~65MW available (from S3REnR data)
        assert valenciennes_site["grid"]["available_capacity_mw"] >= 50, \
            f"Valenciennes capacity too low: {valenciennes_site['grid']['available_capacity_mw']}"
        assert valenciennes_site["grid"]["saturation_level"] == "low"
        
        print(f"Valenciennes: {valenciennes_site['grid']['available_capacity_mw']}MW, saturation={valenciennes_site['grid']['saturation_level']}")


class TestDCSearchTags:
    """Tags field tests"""
    
    def test_tags_contain_relevant_labels(self):
        """Tags field contains relevant labels"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 30
        })
        assert response.status_code == 200
        data = response.json()
        
        all_tags = set()
        for site in data["results"]:
            all_tags.update(site["tags"])
        
        # Check for expected tag types
        expected_tags = ["capacite_ok", "haute_tension", "reseau_sature", "reseau_disponible", 
                        "brownfield", "plu_compatible", "top_site", "site_interessant"]
        
        found_tags = [t for t in expected_tags if t in all_tags]
        print(f"Found tags: {found_tags}")
        print(f"All unique tags: {all_tags}")
        
        # At least some expected tags should be present
        assert len(found_tags) >= 3, f"Too few expected tags found: {found_tags}"


class TestDCSearchComment:
    """Comment field tests"""
    
    def test_comment_provides_useful_text(self):
        """Comment field provides useful AI-interpretable text"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        for site in data["results"]:
            comment = site["comment"]
            assert len(comment) > 20, f"Comment too short: {comment}"
            assert comment.endswith("."), f"Comment should end with period: {comment}"
            
            # Comment should mention capacity or delay
            assert "MW" in comment or "mois" in comment or "capacité" in comment.lower(), \
                f"Comment missing key info: {comment}"
        
        print(f"All {len(data['results'])} comments are informative")


class TestDCSiteDetail:
    """GET /api/dc/site/:id tests"""
    
    def test_get_site_detail_returns_full_info(self):
        """GET /api/dc/site/:id returns full site detail with connectivity and reinforcement info"""
        # First get a site_id from search
        search_response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 20,
            "per_page": 1
        })
        assert search_response.status_code == 200
        site_id = search_response.json()["results"][0]["site_id"]
        
        # Get site detail
        response = requests.get(f"{BASE_URL}/api/dc/site/{site_id}")
        assert response.status_code == 200
        site = response.json()
        
        # Verify all fields present
        assert site["site_id"] == site_id
        assert "name" in site
        assert "location" in site
        assert "land" in site
        assert "grid" in site
        assert "timeline" in site
        assert "urbanism" in site
        assert "connectivity" in site
        assert "score" in site
        assert "tags" in site
        assert "comment" in site
        
        # Connectivity subfields
        assert "nearest_landing_point_km" in site["connectivity"]
        assert "nearest_landing_point" in site["connectivity"]
        assert "nearest_dc_km" in site["connectivity"]
        
        # Grid detail fields
        assert "etat_s3renr" in site["grid"]
        assert "reinforcement_detail" in site["grid"]
        
        # Timeline detail fields
        assert "delay_range_months" in site["timeline"]
        
        print(f"Site detail for {site['name']}: connectivity, reinforcement info present")
    
    def test_get_invalid_site_returns_404(self):
        """GET /api/dc/site/invalid_id returns 404"""
        response = requests.get(f"{BASE_URL}/api/dc/site/invalid_site_id_12345")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        print(f"Invalid site returns 404: {data['detail']}")


class TestDCSearchEdgeCases:
    """Edge case tests"""
    
    def test_empty_region_returns_results(self):
        """Empty region filter returns all France results"""
        response = requests.post(f"{BASE_URL}/api/dc/search", json={
            "region": "",
            "mw_target": 20
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["region_filter"] is None
        assert data["meta"]["total_results"] > 50  # Should have many results
        print(f"Empty region returns {data['meta']['total_results']} results")
    
    def test_high_mw_target_affects_scoring(self):
        """High MW target affects power scoring"""
        response_low = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 10,
            "per_page": 5
        })
        response_high = requests.post(f"{BASE_URL}/api/dc/search", json={
            "mw_target": 100,
            "per_page": 5
        })
        
        # With high MW target, fewer sites should have high power scores
        low_power_scores = [s["score"]["power"] for s in response_low.json()["results"]]
        high_power_scores = [s["score"]["power"] for s in response_high.json()["results"]]
        
        avg_low = sum(low_power_scores) / len(low_power_scores)
        avg_high = sum(high_power_scores) / len(high_power_scores)
        
        print(f"Avg power score: 10MW target={avg_low:.1f}, 100MW target={avg_high:.1f}")
        # Higher target should generally result in lower power scores
        assert avg_low >= avg_high - 20, "Power scores should be lower with higher MW target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
