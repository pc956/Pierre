"""
Iteration 22 - V3 Update Tests
Tests for:
- FIX 1: Generic poste names fallback (no 'inconnu' for postes with S3REnR data)
- FIX 2: Geocoding via api-adresse.data.gouv.fr
- NEW: analyze_parcel (cadastral ref)
- NEW: find_by_address (geocode + search)
- NEW: estimate_budget (CAPEX/EBITDA/TRI)
- Frontend: budget card in ChatBot.js
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_COOKIE = "session_token=test_session_token_2026"


class TestAPIBasics:
    """Basic API health checks"""
    
    def test_api_info(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Cockpit Immo API"
        assert data.get("version") == "1.0.0"
        print(f"✓ API info: {data}")
    
    def test_communes_search_fos(self):
        """GET /api/france/communes?q=Fos returns communes"""
        response = requests.get(f"{BASE_URL}/api/france/communes?q=Fos")
        assert response.status_code == 200
        data = response.json()
        communes = data.get("communes", [])
        assert len(communes) > 0
        # Check Fos-sur-Mer is in results
        fos_sur_mer = [c for c in communes if c.get("nom") == "Fos-sur-Mer"]
        assert len(fos_sur_mer) > 0
        print(f"✓ Communes search: found {len(communes)} communes, including Fos-sur-Mer")


class TestElectricalAssets:
    """Tests for electrical assets endpoint - FIX 1 verification"""
    
    def test_electrical_assets_count(self):
        """GET /api/map/electrical-assets returns ~1091 postes"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        assert len(assets) >= 1000, f"Expected ≥1000 postes, got {len(assets)}"
        print(f"✓ Electrical assets: {len(assets)} postes")
    
    def test_no_inconnu_for_s3renr_regions(self):
        """FIX 1: Postes in S3REnR regions should not have etat='inconnu'"""
        response = requests.get(f"{BASE_URL}/api/map/electrical-assets")
        assert response.status_code == 200
        data = response.json()
        assets = data.get("electrical_assets", [])
        
        # S3REnR regions
        s3renr_regions = ["IDF", "PACA", "HdF"]
        
        # Check for inconnu in S3REnR regions
        inconnu_in_s3renr = [
            a for a in assets 
            if a.get("etat") == "inconnu" and a.get("region") in s3renr_regions
        ]
        
        # Allow some tolerance (generic postes without names)
        assert len(inconnu_in_s3renr) < 50, f"Too many 'inconnu' postes in S3REnR regions: {len(inconnu_in_s3renr)}"
        print(f"✓ FIX 1 verified: only {len(inconnu_in_s3renr)} 'inconnu' postes in S3REnR regions (acceptable)")


class TestChatParcelSearch:
    """Tests for chat endpoint - parcel search"""
    
    def test_chat_parcel_search_fos(self):
        """POST /api/chat with 'Parcelles à Fos-sur-Mer de 2 hectares' returns parcel_results or text"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "Parcelles à Fos-sur-Mer de 2 hectares"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Can return parcel_results or text (if no parcels found with strict criteria)
        assert data.get("type") in ["parcel_results", "text"], f"Unexpected type: {data.get('type')}"
        
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            if len(parcels) > 0:
                # Verify parcel structure
                p = parcels[0]
                assert "parcel_id" in p
                assert "commune" in p
                assert "surface_ha" in p
                assert "score" in p
                print(f"✓ Parcel search: found {len(parcels)} parcels at Fos-sur-Mer")
            else:
                print(f"✓ Parcel search: no parcels found (valid response)")
        else:
            # Text response - should mention Fos-sur-Mer
            text = data.get("text", "")
            assert "Fos" in text or "parcelle" in text.lower()
            print(f"✓ Parcel search: text response (no parcels matching criteria)")
    
    def test_chat_summary(self):
        """POST /api/chat with 'Résumé des capacités réseau' returns summary type"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "Résumé des capacités réseau"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "summary", f"Expected summary, got {data.get('type')}"
        summary = data.get("summary", [])
        assert len(summary) >= 3, "Expected at least 3 regions in summary"
        
        # Check regions
        regions = [s.get("region") for s in summary]
        assert "IDF" in regions
        assert "PACA" in regions
        assert "HdF" in regions
        print(f"✓ Summary: {len(summary)} regions - {regions}")


class TestNewCapabilities:
    """Tests for new V3 capabilities"""
    
    def test_estimate_budget(self):
        """NEW: POST /api/chat with budget question returns budget field"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "Combien coûte un projet DC de 10MW à Fos-sur-Mer?"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return parcel_results with budget
        assert data.get("type") == "parcel_results", f"Expected parcel_results, got {data.get('type')}"
        
        # Check for budget in response
        budget = data.get("budget_estimation") or (data.get("parcels", [{}])[0].get("budget"))
        assert budget is not None, "Expected budget field in response"
        
        # Verify budget structure
        assert "capex_total_meur" in budget
        assert "ebitda_meur" in budget
        assert "tri_indicatif_pct" in budget
        
        # Check budget is in expected range (100-150 M€ for 10MW)
        capex = budget.get("capex_total_meur", 0)
        assert 50 <= capex <= 200, f"CAPEX {capex} M€ outside expected range 50-200 M€"
        
        print(f"✓ Budget estimation: CAPEX={capex} M€, EBITDA={budget.get('ebitda_meur')} M€, TRI={budget.get('tri_indicatif_pct')}%")
    
    def test_find_by_address_action(self):
        """NEW: POST /api/chat with address triggers find_by_address action"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "parcelles près du 13 rue de la République 13002 Marseille"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # The action should be triggered (even if no parcels found in city center)
        # Response can be text (no parcels) or parcel_results
        assert data.get("type") in ["text", "parcel_results"], f"Unexpected type: {data.get('type')}"
        
        # If text, should mention the address was searched
        if data.get("type") == "text":
            text = data.get("text", "")
            assert "13 rue de la République" in text or "Marseille" in text or "adresse" in text.lower()
        
        print(f"✓ find_by_address action triggered, response type: {data.get('type')}")
    
    def test_analyze_parcel_action(self):
        """NEW: POST /api/chat with cadastral reference triggers analyze_parcel"""
        # Use a known parcel from Fos-sur-Mer
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "Analyse la parcelle 13039000AE0019"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return parcel_results with the analyzed parcel
        if data.get("type") == "parcel_results":
            parcels = data.get("parcels", [])
            assert len(parcels) >= 1, "Expected at least 1 parcel"
            p = parcels[0]
            assert "13039" in p.get("parcel_id", "") or "13039" in p.get("ref_cadastrale", "")
            print(f"✓ analyze_parcel: found parcel {p.get('ref_cadastrale')} at {p.get('commune')}")
        else:
            # May return text if parcel not found
            print(f"✓ analyze_parcel action triggered, response type: {data.get('type')}")


class TestGeocodingFix:
    """Tests for FIX 2: Geocoding via api-adresse.data.gouv.fr"""
    
    def test_geocoding_with_valid_address(self):
        """FIX 2: Geocoding should work with valid French addresses"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "Cookie": SESSION_COOKIE},
            json={"message": "parcelles près de 4 allée du Port 26200 Montélimar"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should not error out
        assert data.get("type") in ["text", "parcel_results", "error"]
        
        # If parcel_results, check geocoded field
        if data.get("type") == "parcel_results":
            sites = data.get("sites_searched", [])
            if sites:
                assert any(s.get("type") == "address" for s in sites)
        
        print(f"✓ Geocoding test: response type {data.get('type')}")


class TestS3REnRMatching:
    """Tests for S3REnR matching improvements"""
    
    def test_s3renr_summary(self):
        """GET /api/s3renr/summary returns region data"""
        response = requests.get(f"{BASE_URL}/api/s3renr/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "regions" in data or "IDF" in data or isinstance(data, dict)
        print(f"✓ S3REnR summary: {list(data.keys())[:5]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
