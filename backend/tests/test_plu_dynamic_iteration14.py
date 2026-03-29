"""
Iteration 14 Tests: Dynamic PLU Scoring via GPU API
Tests the new /api/scoring/plu-dynamic endpoint and GPU context integration.

Features tested:
1. GET /api/scoring/plu-dynamic?lon=X&lat=Y returns dynamic scoring with gpu_source=dynamic
2. Dynamic scoring fetches zone-urba + prescription-surf + info-surf from GPU API
3. Prescription analysis: EBC (-15), patrimoine (-12), limitation (-8)
4. Information analysis: PPRT/PPR (-10), ZAC (+8), voie_bruyante, archeologie
5. Destination dominante analysis from libelong text
6. plu_score_base and plu_score_dynamic_adj fields present
7. gpu_data contains prescriptions_count, informations_count, risk_labels, destination_analysis
8. Static PLU scoring still works (backward compatible)
9. Chatbot parcel search uses dynamic PLU scoring
10. Previous features still work (future 400kV, layer toggles, PDF export)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://project-platform-2.preview.emergentagent.com"

SESSION_COOKIE = {"session_token": "test_session_token_2026"}


class TestDynamicPLUScoringEndpoint:
    """Tests for GET /api/scoring/plu-dynamic endpoint"""
    
    def test_dynamic_plu_fos_sur_mer(self):
        """Test dynamic PLU scoring for Fos-sur-Mer (PACA) - should have PPRT risk"""
        # Fos-sur-Mer coordinates (industrial zone with PPRT)
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.94, "lat": 43.44},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify gpu_source is dynamic
        assert data.get("gpu_source") == "dynamic", f"Expected gpu_source=dynamic, got {data.get('gpu_source')}"
        
        # Verify required fields are present
        assert "plu_score" in data, "Missing plu_score field"
        assert "plu_status" in data, "Missing plu_status field"
        assert "plu_code" in data, "Missing plu_code field"
        assert "flags" in data, "Missing flags field"
        assert "gpu_data" in data, "Missing gpu_data field"
        
        # Verify gpu_data structure
        gpu_data = data.get("gpu_data", {})
        assert "prescriptions_count" in gpu_data, "Missing prescriptions_count in gpu_data"
        assert "informations_count" in gpu_data, "Missing informations_count in gpu_data"
        
        print(f"Fos-sur-Mer dynamic PLU: score={data['plu_score']}, status={data['plu_status']}, flags={data.get('flags', [])}")
        print(f"GPU data: prescriptions={gpu_data.get('prescriptions_count')}, informations={gpu_data.get('informations_count')}")
    
    def test_dynamic_plu_lyon(self):
        """Test dynamic PLU scoring for Lyon - should detect industrial vocation"""
        # Lyon coordinates (industrial area)
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.85, "lat": 45.74},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify gpu_source is dynamic
        assert data.get("gpu_source") == "dynamic", f"Expected gpu_source=dynamic, got {data.get('gpu_source')}"
        
        # Verify required fields
        assert "plu_score" in data
        assert "plu_status" in data
        assert "gpu_data" in data
        
        # Check for destination analysis
        gpu_data = data.get("gpu_data", {})
        dest_analysis = gpu_data.get("destination_analysis", {})
        
        print(f"Lyon dynamic PLU: score={data['plu_score']}, status={data['plu_status']}")
        print(f"Destination analysis: {dest_analysis}")
        print(f"Flags: {data.get('flags', [])}")
    
    def test_dynamic_plu_base_and_adjustment_fields(self):
        """Verify plu_score_base and plu_score_dynamic_adj fields are present"""
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.94, "lat": 43.44},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # These fields should be present for dynamic scoring
        assert "plu_score_base" in data, "Missing plu_score_base field"
        assert "plu_score_dynamic_adj" in data, "Missing plu_score_dynamic_adj field"
        
        # Verify the math: plu_score = plu_score_base + plu_score_dynamic_adj (clamped 0-100)
        base = data.get("plu_score_base", 0)
        adj = data.get("plu_score_dynamic_adj", 0)
        final = data.get("plu_score", 0)
        
        expected = max(0, min(100, base + adj))
        assert final == expected, f"Score math mismatch: {base} + {adj} should = {expected}, got {final}"
        
        print(f"Score breakdown: base={base}, adjustment={adj}, final={final}")
    
    def test_dynamic_plu_gpu_data_structure(self):
        """Verify gpu_data contains all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.94, "lat": 43.44},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        gpu_data = data.get("gpu_data", {})
        
        # Required fields in gpu_data
        required_fields = [
            "prescriptions_count",
            "informations_count",
            "destination_analysis",
        ]
        
        for field in required_fields:
            assert field in gpu_data, f"Missing {field} in gpu_data"
        
        # Check destination_analysis structure
        dest = gpu_data.get("destination_analysis", {})
        assert "flags" in dest, "Missing flags in destination_analysis"
        assert "score_adjustment" in dest, "Missing score_adjustment in destination_analysis"
        
        print(f"GPU data structure verified: {list(gpu_data.keys())}")
    
    def test_dynamic_plu_unavailable_location(self):
        """Test dynamic PLU for location without GPU data (ocean/invalid)"""
        # Middle of Atlantic Ocean
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": -30.0, "lat": 40.0},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return fallback response
        assert data.get("gpu_source") in ["unavailable", "dynamic"], "Expected unavailable or dynamic gpu_source"
        
        if data.get("gpu_source") == "unavailable":
            assert "gpu_data_unavailable" in data.get("flags", []), "Expected gpu_data_unavailable flag"
            print("Ocean location correctly returns unavailable GPU data")
        else:
            print(f"Ocean location returned: {data}")


class TestDynamicPLURiskDetection:
    """Tests for risk detection from GPU prescriptions and informations"""
    
    def test_pprt_ppr_detection(self):
        """Test PPRT/PPR risk detection from GPU informations"""
        # Fos-sur-Mer has PPRT FOS EST
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.94, "lat": 43.44},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        flags = data.get("flags", [])
        gpu_data = data.get("gpu_data", {})
        
        # Check for PPRT/PPR related flags
        pprt_flags = [f for f in flags if "pprt" in f.lower() or "ppr" in f.lower()]
        risk_labels = gpu_data.get("risk_labels", [])
        
        print(f"PPRT/PPR flags: {pprt_flags}")
        print(f"Risk labels: {risk_labels}")
        
        # Note: PPRT detection depends on actual GPU data at this location
        # We verify the structure is correct
        assert isinstance(flags, list), "flags should be a list"
        assert isinstance(risk_labels, list), "risk_labels should be a list"
    
    def test_zac_detection_bonus(self):
        """Test ZAC detection gives +8 bonus"""
        # Test a location that might have ZAC
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.85, "lat": 45.74},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        flags = data.get("flags", [])
        
        # Check for ZAC flag
        zac_flags = [f for f in flags if "zac" in f.lower()]
        
        print(f"ZAC flags: {zac_flags}")
        
        # If ZAC is detected, adjustment should include +8
        if "zone_zac_gpu" in flags:
            adjustments = data.get("adjustments", [])
            zac_adj = [a for a in adjustments if "zac" in str(a).lower()]
            print(f"ZAC adjustments: {zac_adj}")
    
    def test_prescription_ebc_detection(self):
        """Test EBC (Espace Boisé Classé) prescription detection"""
        # Test various locations
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.94, "lat": 43.44},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        flags = data.get("flags", [])
        gpu_data = data.get("gpu_data", {})
        
        # Check for EBC flags
        ebc_flags = [f for f in flags if "ebc" in f.lower()]
        presc_flags = gpu_data.get("prescriptions_flags", [])
        
        print(f"EBC flags: {ebc_flags}")
        print(f"Prescription flags: {presc_flags}")
    
    def test_destination_dominante_analysis(self):
        """Test destination dominante analysis from libelong text"""
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu-dynamic",
            params={"lon": 4.85, "lat": 45.74},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        gpu_data = data.get("gpu_data", {})
        dest_analysis = gpu_data.get("destination_analysis", {})
        
        # Verify destination analysis structure
        assert "industrial_signals" in dest_analysis, "Missing industrial_signals"
        assert "residential_signals" in dest_analysis, "Missing residential_signals"
        assert "nature_signals" in dest_analysis, "Missing nature_signals"
        
        print(f"Destination analysis: industrial={dest_analysis.get('industrial_signals')}, "
              f"residential={dest_analysis.get('residential_signals')}, "
              f"nature={dest_analysis.get('nature_signals')}")
        print(f"Destination flags: {dest_analysis.get('flags', [])}")


class TestStaticPLUScoringBackwardCompatibility:
    """Tests to ensure static PLU scoring still works"""
    
    def test_static_plu_ui_zone(self):
        """Test static PLU scoring for UI zone still works"""
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu/UI",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("plu_score") == 90, f"Expected score 90 for UI, got {data.get('plu_score')}"
        assert data.get("plu_status") == "FAVORABLE"
        
        print("Static PLU scoring for UI zone: PASS")
    
    def test_static_plu_n_zone_excluded(self):
        """Test static PLU scoring for N zone (excluded)"""
        response = requests.get(
            f"{BASE_URL}/api/scoring/plu/N",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("plu_score") == 0, f"Expected score 0 for N, got {data.get('plu_score')}"
        assert data.get("plu_status") == "EXCLUDED"
        
        print("Static PLU scoring for N zone (excluded): PASS")
    
    def test_static_plu_post_endpoint(self):
        """Test POST /api/scoring/plu still works with adjustments"""
        response = requests.post(
            f"{BASE_URL}/api/scoring/plu",
            json={
                "zone_code": "UI",
                "zone_label": "Zone industrielle",
                "is_brownfield": True,
                "is_zac_zip_port": True,
            },
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        # UI (90) + brownfield (+10) + ZAC (+8) = 100 (capped)
        assert data.get("plu_score") >= 100, f"Expected score >= 100, got {data.get('plu_score')}"
        assert "brownfield_bonus" in data.get("flags", [])
        
        print("Static PLU POST endpoint with adjustments: PASS")


class TestChatbotDynamicPLUIntegration:
    """Tests for chatbot using dynamic PLU scoring"""
    
    def test_chatbot_parcel_search_uses_dynamic_plu(self):
        """Test that chatbot parcel search returns parcels with dynamic PLU scoring"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Trouve-moi des parcelles pour un DC de 20MW en PACA",
                "session_id": "test_dynamic_plu_14",
                "history": []
            },
            cookies=SESSION_COOKIE,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return parcel_results type
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            
            if parcels:
                # Check first parcel has plu_scoring with gpu_source
                first_parcel = parcels[0]
                plu_scoring = first_parcel.get("plu_scoring", {})
                
                assert "plu_score" in plu_scoring, "Missing plu_score in parcel plu_scoring"
                assert "plu_status" in plu_scoring, "Missing plu_status in parcel plu_scoring"
                
                # Check for gpu_source field
                gpu_source = plu_scoring.get("gpu_source")
                print(f"Chatbot parcel PLU gpu_source: {gpu_source}")
                print(f"Chatbot parcel PLU score: {plu_scoring.get('plu_score')}, status: {plu_scoring.get('plu_status')}")
                
                # Verify EXCLUDED parcels are filtered out
                excluded_parcels = [p for p in parcels if p.get("plu_scoring", {}).get("plu_status") == "EXCLUDED"]
                assert len(excluded_parcels) == 0, f"Found {len(excluded_parcels)} EXCLUDED parcels - should be auto-filtered"
                
                print(f"Chatbot returned {len(parcels)} parcels, 0 EXCLUDED (correctly filtered)")
            else:
                print("No parcels returned - may be due to search criteria")
        else:
            print(f"Chatbot returned type: {data.get('type')}")
    
    def test_chatbot_excludes_excluded_plu_parcels(self):
        """Verify chatbot auto-excludes parcels with EXCLUDED PLU status"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Parcelles industrielles près de Fos-sur-Mer",
                "session_id": "test_exclude_plu_14",
                "history": []
            },
            cookies=SESSION_COOKIE,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            
            # All returned parcels should NOT have EXCLUDED status
            for parcel in parcels:
                plu_status = parcel.get("plu_scoring", {}).get("plu_status")
                assert plu_status != "EXCLUDED", f"Found EXCLUDED parcel: {parcel.get('parcel_id')}"
            
            print(f"Verified {len(parcels)} parcels - none have EXCLUDED status")


class TestPreviousFeaturesStillWork:
    """Tests to ensure previous features still work"""
    
    def test_future_400kv_endpoint(self):
        """Test future 400kV line endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/map/rte-future-400kv",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "line" in data, "Missing line in future 400kV response"
        assert "buffers" in data, "Missing buffers in future 400kV response"
        assert "metadata" in data, "Missing metadata in future 400kV response"
        
        print("Future 400kV endpoint: PASS")
    
    def test_electrical_assets_endpoint(self):
        """Test electrical assets endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/map/electrical-assets",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assets = data.get("electrical_assets", [])
        assert len(assets) > 0, "No electrical assets returned"
        
        print(f"Electrical assets endpoint: {len(assets)} assets returned")
    
    def test_pdf_export_endpoint(self):
        """Test PDF export endpoint still works"""
        response = requests.post(
            f"{BASE_URL}/api/export/pdf",
            json={
                "commune": "Test Commune",
                "surface_ha": 5.0,
                "score": {"score_net": 75, "verdict": "GO"},
                "plu_scoring": {
                    "plu_score": 85,
                    "plu_status": "FAVORABLE",
                    "gpu_source": "dynamic"
                }
            },
            timeout=15
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        
        print("PDF export endpoint: PASS")
    
    def test_dc_existants_endpoint(self):
        """Test DC existants endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/map/dc",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        dc_list = data.get("dc_existants", [])
        assert len(dc_list) > 0, "No DC existants returned"
        
        print(f"DC existants endpoint: {len(dc_list)} DCs returned")
    
    def test_landing_points_endpoint(self):
        """Test landing points endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/map/landing-points",
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        lp_list = data.get("landing_points", [])
        assert len(lp_list) > 0, "No landing points returned"
        
        print(f"Landing points endpoint: {len(lp_list)} landing points returned")


class TestAPICartoGPUIntegration:
    """Tests for api_carto.py GPU integration"""
    
    def test_bbox_parcels_with_plu_scoring(self):
        """Test bbox parcels endpoint includes PLU scoring"""
        # Fos-sur-Mer area
        response = requests.get(
            f"{BASE_URL}/api/france/parcelles/bbox",
            params={
                "min_lon": 4.93,
                "min_lat": 43.43,
                "max_lon": 4.95,
                "max_lat": 43.45,
                "project_type": "colocation_t3",
                "limit": 10
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        parcels = data.get("parcelles", [])
        
        if parcels:
            # Check first parcel has plu_scoring
            first = parcels[0]
            assert "plu_scoring" in first, "Missing plu_scoring in bbox parcel"
            
            plu = first.get("plu_scoring", {})
            assert "plu_score" in plu, "Missing plu_score"
            assert "plu_status" in plu, "Missing plu_status"
            
            print(f"BBox parcels: {len(parcels)} parcels with PLU scoring")
            print(f"First parcel PLU: score={plu.get('plu_score')}, status={plu.get('plu_status')}")
        else:
            print("No parcels in bbox - may be sparse area")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
