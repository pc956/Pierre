"""
Iteration 15 Tests: PLU Composite Scoring with Confidence Indicator
Tests the dynamic/static fallback scoring and confidence levels (haute/moyenne/basse)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPLUDynamicConfidence:
    """Test dynamic PLU scoring returns confidence=haute with GPU data"""
    
    def test_dynamic_plu_fos_returns_haute_confidence(self):
        """GET /api/scoring/plu-dynamic?lon=4.94&lat=43.44 returns confidence=haute"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu-dynamic?lon=4.94&lat=43.44")
        assert response.status_code == 200
        data = response.json()
        
        # Must have confidence field
        assert "confidence" in data, "Missing confidence field"
        assert data["confidence"] == "haute", f"Expected haute, got {data['confidence']}"
        
        # Must have confidence_detail mentioning GPU
        assert "confidence_detail" in data, "Missing confidence_detail field"
        assert "GPU" in data["confidence_detail"] or "dynamique" in data["confidence_detail"].lower(), \
            f"confidence_detail should mention GPU: {data['confidence_detail']}"
        
        # Must have gpu_source=dynamic
        assert data.get("gpu_source") == "dynamic", f"Expected gpu_source=dynamic, got {data.get('gpu_source')}"
        
        print(f"✓ Fos dynamic PLU: confidence={data['confidence']}, detail={data['confidence_detail']}")
    
    def test_dynamic_plu_lyon_returns_haute_with_prescriptions(self):
        """GET /api/scoring/plu-dynamic?lon=4.85&lat=45.74 returns confidence=haute with prescriptions/infos"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu-dynamic?lon=4.85&lat=45.74")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("confidence") == "haute", f"Expected haute, got {data.get('confidence')}"
        assert data.get("gpu_source") == "dynamic"
        
        # Should have gpu_data with prescriptions/informations
        gpu_data = data.get("gpu_data", {})
        assert "prescriptions_count" in gpu_data or "informations_count" in gpu_data, \
            "Missing prescriptions_count or informations_count in gpu_data"
        
        # Check destination analysis
        if "destination_analysis" in gpu_data:
            dest = gpu_data["destination_analysis"]
            assert "industrial_signals" in dest or "residential_signals" in dest, \
                "Missing signal counts in destination_analysis"
        
        print(f"✓ Lyon dynamic PLU: confidence={data['confidence']}, prescriptions={gpu_data.get('prescriptions_count', 0)}, infos={gpu_data.get('informations_count', 0)}")


class TestPLUStaticConfidence:
    """Test static PLU scoring returns confidence=basse or moyenne"""
    
    def test_static_plu_ui_returns_basse_confidence(self):
        """GET /api/scoring/plu/UI returns confidence=basse (static scoring, no regulation text)"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu/UI")
        assert response.status_code == 200
        data = response.json()
        
        assert "confidence" in data, "Missing confidence field"
        assert data["confidence"] == "basse", f"Expected basse for static code-only, got {data['confidence']}"
        
        # Should mention static scoring
        assert "confidence_detail" in data
        assert "statique" in data["confidence_detail"].lower(), \
            f"confidence_detail should mention statique: {data['confidence_detail']}"
        
        print(f"✓ Static PLU UI: confidence={data['confidence']}, detail={data['confidence_detail']}")
    
    def test_static_plu_n_returns_moyenne_confidence(self):
        """GET /api/scoring/plu/N returns confidence=moyenne (excluded zones)"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu/N")
        assert response.status_code == 200
        data = response.json()
        
        assert "confidence" in data, "Missing confidence field"
        # N zone is excluded, should have moyenne confidence
        assert data["confidence"] == "moyenne", f"Expected moyenne for excluded zone, got {data['confidence']}"
        assert data["plu_status"] == "EXCLUDED", f"Expected EXCLUDED status, got {data['plu_status']}"
        
        print(f"✓ Static PLU N: confidence={data['confidence']}, status={data['plu_status']}")
    
    def test_static_plu_with_reglement_returns_moyenne(self):
        """POST /api/scoring/plu with reglement_text returns confidence=moyenne or haute"""
        payload = {
            "zone_code": "UX",
            "zone_label": "Zone d'activités économiques",
            "reglement_text": "Zone destinée aux activités industrielles et logistiques. Les installations classées sont autorisées."
        }
        response = requests.post(f"{BASE_URL}/api/scoring/plu", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "confidence" in data
        # With reglement_text, should be at least moyenne
        assert data["confidence"] in ["moyenne", "haute"], \
            f"Expected moyenne or haute with reglement_text, got {data['confidence']}"
        
        # Should mention règlement in detail
        assert "confidence_detail" in data
        assert "règlement" in data["confidence_detail"].lower() or "reglement" in data["confidence_detail"].lower(), \
            f"confidence_detail should mention règlement: {data['confidence_detail']}"
        
        print(f"✓ Static PLU with reglement: confidence={data['confidence']}, detail={data['confidence_detail']}")


class TestChatbotParcelConfidence:
    """Test chatbot parcel search returns parcels with confidence field"""
    
    def test_chat_parcel_search_returns_confidence(self):
        """POST /api/chat parcel search returns parcels with confidence in plu_scoring"""
        payload = {
            "message": "Trouve des parcelles 30MW PACA",
            "session_id": "test_confidence_15",
            "history": []
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Should return parcel_results type
        assert data.get("type") == "parcel_results", f"Expected parcel_results, got {data.get('type')}"
        
        parcels = data.get("parcels", [])
        assert len(parcels) > 0, "No parcels returned"
        
        # Check first parcel has plu_scoring with confidence
        parcel = parcels[0]
        plu_scoring = parcel.get("plu_scoring", {})
        
        assert "confidence" in plu_scoring, f"Missing confidence in plu_scoring: {plu_scoring.keys()}"
        assert plu_scoring["confidence"] in ["haute", "moyenne", "basse"], \
            f"Invalid confidence value: {plu_scoring['confidence']}"
        
        # Check gpu_source
        assert "gpu_source" in plu_scoring, "Missing gpu_source in plu_scoring"
        
        print(f"✓ Chatbot parcel: confidence={plu_scoring['confidence']}, gpu_source={plu_scoring.get('gpu_source')}")
        
        # Count confidence levels
        confidence_counts = {"haute": 0, "moyenne": 0, "basse": 0}
        for p in parcels:
            conf = p.get("plu_scoring", {}).get("confidence", "unknown")
            if conf in confidence_counts:
                confidence_counts[conf] += 1
        
        print(f"  Confidence distribution: {confidence_counts}")


class TestBboxParcelsConfidence:
    """Test bbox parcels endpoint uses dynamic GPU scoring with fallback"""
    
    def test_bbox_parcels_have_confidence(self):
        """GET /api/france/parcelles/bbox returns parcels with confidence in plu_scoring"""
        # Use Fos-sur-Mer area
        params = {
            "min_lon": 4.92,
            "min_lat": 43.42,
            "max_lon": 4.96,
            "max_lat": 43.46,
            "project_type": "colocation_t3",
            "limit": 10
        }
        response = requests.get(f"{BASE_URL}/api/france/parcelles/bbox", params=params)
        assert response.status_code == 200
        data = response.json()
        
        parcels = data.get("parcelles", [])
        if len(parcels) == 0:
            pytest.skip("No parcels in bbox - API may be slow or area has no parcels")
        
        # Check parcels have plu_scoring with confidence
        parcels_with_confidence = 0
        dynamic_count = 0
        static_count = 0
        
        for p in parcels:
            plu = p.get("plu_scoring", {})
            if "confidence" in plu:
                parcels_with_confidence += 1
                if plu.get("gpu_source") == "dynamic":
                    dynamic_count += 1
                else:
                    static_count += 1
        
        assert parcels_with_confidence > 0, "No parcels have confidence field"
        
        print(f"✓ Bbox parcels: {parcels_with_confidence}/{len(parcels)} have confidence")
        print(f"  Dynamic: {dynamic_count}, Static/Fallback: {static_count}")


class TestDynamicGPUSource:
    """Test that dynamic scoring returns gpu_source=dynamic"""
    
    def test_dynamic_returns_gpu_source_dynamic(self):
        """GET /api/scoring/plu-dynamic returns gpu_source=dynamic"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu-dynamic?lon=4.94&lat=43.44")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("gpu_source") == "dynamic", f"Expected gpu_source=dynamic, got {data.get('gpu_source')}"
        print(f"✓ Dynamic PLU returns gpu_source=dynamic")
    
    def test_unavailable_location_returns_fallback(self):
        """GET /api/scoring/plu-dynamic for ocean returns gpu_source=unavailable"""
        # Ocean location (no GPU data)
        response = requests.get(f"{BASE_URL}/api/scoring/plu-dynamic?lon=-5.0&lat=48.0")
        assert response.status_code == 200
        data = response.json()
        
        # Should fallback gracefully
        assert "gpu_source" in data
        assert data["gpu_source"] in ["unavailable", "fallback", "static_from_zone"], \
            f"Expected fallback gpu_source, got {data['gpu_source']}"
        
        print(f"✓ Ocean location returns gpu_source={data['gpu_source']}")


class TestPreviousFeaturesStillWork:
    """Verify previous features still work after confidence changes"""
    
    def test_layer_toggles_data_available(self):
        """GET /api/map/electrical-assets returns postes HTB"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        
        assets = data.get("electrical_assets", [])
        assert len(assets) > 50, f"Expected >50 assets, got {len(assets)}"
        
        postes = [a for a in assets if a.get("type") == "poste_htb"]
        assert len(postes) > 30, f"Expected >30 postes HTB, got {len(postes)}"
        
        print(f"✓ Electrical assets: {len(assets)} total, {len(postes)} postes HTB")
    
    def test_future_400kv_line_available(self):
        """GET /api/map/rte-future-400kv returns line + buffers"""
        response = requests.get(f"{BASE_URL}/api/map/rte-future-400kv")
        assert response.status_code == 200
        data = response.json()
        
        assert "line" in data, "Missing line in response"
        assert "buffers" in data, "Missing buffers in response"
        assert "metadata" in data, "Missing metadata in response"
        
        # Check buffers
        buffers = data["buffers"]
        assert "1km" in buffers, "Missing 1km buffer"
        assert "3km" in buffers, "Missing 3km buffer"
        assert "5km" in buffers, "Missing 5km buffer"
        
        print(f"✓ Future 400kV line: {data['metadata'].get('nom')}")
    
    def test_pdf_export_works(self):
        """POST /api/export/pdf generates PDF"""
        payload = {
            "name": "Test Site",
            "commune": "Fos-sur-Mer",
            "surface_ha": 5.0,
            "score": {"score_net": 75, "verdict": "GO"},
            "plu_scoring": {"confidence": "haute", "plu_score": 85}
        }
        response = requests.post(f"{BASE_URL}/api/export/pdf", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 1000, "PDF too small"
        
        print(f"✓ PDF export: {len(response.content)} bytes")
    
    def test_s3renr_summary_available(self):
        """GET /api/s3renr/summary returns regional data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", [])
        assert len(summary) > 0, "No S3REnR summary data"
        
        # Check structure
        region = summary[0]
        assert "region" in region
        assert "status_global" in region
        
        print(f"✓ S3REnR summary: {len(summary)} regions")


class TestConfidenceLevelLogic:
    """Test the confidence level assignment logic"""
    
    def test_haute_requires_multiple_sources(self):
        """Dynamic scoring with prescriptions+infos should be haute"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu-dynamic?lon=4.94&lat=43.44")
        assert response.status_code == 200
        data = response.json()
        
        gpu_data = data.get("gpu_data", {})
        presc_count = gpu_data.get("prescriptions_count", 0)
        info_count = gpu_data.get("informations_count", 0)
        
        # If we have prescriptions or informations, confidence should be haute
        if presc_count > 0 or info_count > 0:
            assert data["confidence"] == "haute", \
                f"With prescriptions/infos, expected haute, got {data['confidence']}"
            print(f"✓ Haute confidence with {presc_count} prescriptions, {info_count} infos")
        else:
            # Zone only = moyenne
            assert data["confidence"] in ["haute", "moyenne"], \
                f"Zone only should be haute or moyenne, got {data['confidence']}"
            print(f"✓ Confidence {data['confidence']} with zone only")
    
    def test_basse_for_code_only_static(self):
        """Static scoring with code only should be basse"""
        response = requests.get(f"{BASE_URL}/api/scoring/plu/UX")
        assert response.status_code == 200
        data = response.json()
        
        assert data["confidence"] == "basse", \
            f"Code-only static should be basse, got {data['confidence']}"
        
        print(f"✓ Basse confidence for code-only static scoring")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
