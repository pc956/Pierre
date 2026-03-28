"""
Test suite for AI Chat Assistant feature
Tests POST /api/chat endpoint with various query types:
- Search queries (e.g., "50MW en PACA")
- Summary queries (e.g., "Résumé S3REnR")
- General questions
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestChatAssistant:
    """Tests for POST /api/chat endpoint"""
    
    def test_chat_endpoint_exists(self):
        """Test that /api/chat endpoint exists and accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "test", "session_id": "test_session", "history": []}
        )
        # Should not return 404 or 405
        assert response.status_code != 404, "Chat endpoint not found"
        assert response.status_code != 405, "Chat endpoint does not accept POST"
        print(f"✓ Chat endpoint exists, status: {response.status_code}")
    
    def test_chat_search_query_paca(self):
        """Test search query '50MW en PACA' returns search_results with fly_to"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "50MW en PACA",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30  # LLM calls can take time
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Response type: {data.get('type')}")
        print(f"Response keys: {list(data.keys())}")
        
        # Should return search_results type
        assert data.get("type") == "search_results", f"Expected type=search_results, got {data.get('type')}"
        
        # Should have results array
        assert "results" in data, "Missing 'results' in response"
        assert isinstance(data["results"], list), "Results should be a list"
        
        # Should have fly_to coordinates
        assert "fly_to" in data, "Missing 'fly_to' in response"
        fly_to = data["fly_to"]
        assert "lat" in fly_to, "fly_to missing 'lat'"
        assert "lng" in fly_to, "fly_to missing 'lng'"
        assert "zoom" in fly_to, "fly_to missing 'zoom'"
        
        print(f"✓ Search query returned {len(data['results'])} results")
        print(f"✓ fly_to: lat={fly_to['lat']}, lng={fly_to['lng']}, zoom={fly_to['zoom']}")
    
    def test_chat_search_results_structure(self):
        """Test that search results have correct structure (name, MW, score, saturation)"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "20MW IDF rapide",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        if data.get("type") == "search_results" and data.get("results"):
            result = data["results"][0]
            
            # Check required fields
            assert "name" in result, "Result missing 'name'"
            assert "site_id" in result, "Result missing 'site_id'"
            assert "score" in result, "Result missing 'score'"
            assert "grid" in result, "Result missing 'grid'"
            assert "location" in result, "Result missing 'location'"
            
            # Check score structure
            score = result["score"]
            assert "global" in score, "Score missing 'global'"
            
            # Check grid structure (for saturation badge)
            grid = result["grid"]
            assert "saturation_level" in grid, "Grid missing 'saturation_level'"
            assert "available_capacity_mw" in grid, "Grid missing 'available_capacity_mw'"
            
            print(f"✓ Result structure valid: {result['name']}")
            print(f"  Score: {score['global']}, MW: {grid['available_capacity_mw']}, Saturation: {grid['saturation_level']}")
        else:
            print(f"Note: Response type was {data.get('type')}, not search_results")
    
    def test_chat_results_sorted_by_score(self):
        """Test that search results are sorted by score descending"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Sites HdF réseau dispo",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        if data.get("type") == "search_results" and len(data.get("results", [])) > 1:
            results = data["results"]
            scores = [r["score"]["global"] for r in results]
            
            # Check descending order
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i+1], f"Results not sorted: {scores[i]} < {scores[i+1]}"
            
            print(f"✓ Results sorted by score descending: {scores[:5]}")
        else:
            print(f"Note: Not enough results to verify sorting")
    
    def test_chat_summary_query(self):
        """Test 'Résumé S3REnR' returns type=summary with region data"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Résumé S3REnR",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"Response type: {data.get('type')}")
        
        # Should return summary type
        assert data.get("type") == "summary", f"Expected type=summary, got {data.get('type')}"
        
        # Should have summary array with region data
        assert "summary" in data, "Missing 'summary' in response"
        assert isinstance(data["summary"], list), "Summary should be a list"
        assert len(data["summary"]) > 0, "Summary should not be empty"
        
        # Check region data structure
        region = data["summary"][0]
        assert "region" in region, "Region data missing 'region'"
        assert "status" in region or "status_global" in region, "Region data missing status"
        
        print(f"✓ Summary returned {len(data['summary'])} regions")
        for r in data["summary"][:3]:
            print(f"  {r.get('region')}: {r.get('status') or r.get('status_global')}")
    
    def test_chat_general_question(self):
        """Test general question returns type=text with response"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Bonjour, comment ça va?",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"Response type: {data.get('type')}")
        
        # Should return text type for general questions
        assert data.get("type") in ["text", "chat"], f"Expected type=text or chat, got {data.get('type')}"
        
        # Should have text content
        assert "text" in data or "response" in data, "Missing text content in response"
        
        text = data.get("text") or data.get("response", "")
        assert len(text) > 0, "Response text should not be empty"
        
        print(f"✓ General question returned text response: {text[:100]}...")
    
    def test_chat_fly_to_coordinates_valid(self):
        """Test that fly_to coordinates are valid for France"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "50MW en PACA",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        if data.get("type") == "search_results" and "fly_to" in data:
            fly_to = data["fly_to"]
            lat = fly_to["lat"]
            lng = fly_to["lng"]
            zoom = fly_to["zoom"]
            
            # France bounds: lat 41-51, lng -5 to 10
            assert 41 <= lat <= 51, f"Latitude {lat} out of France bounds"
            assert -5 <= lng <= 10, f"Longitude {lng} out of France bounds"
            assert 5 <= zoom <= 15, f"Zoom {zoom} out of reasonable range"
            
            print(f"✓ fly_to coordinates valid for France: ({lat}, {lng}) zoom={zoom}")
        else:
            print("Note: No fly_to in response to validate")
    
    def test_chat_with_history(self):
        """Test that chat accepts history parameter"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Et en IDF?",
                "session_id": f"test_{int(time.time())}",
                "history": [
                    {"role": "user", "content": "50MW en PACA"},
                    {"role": "assistant", "content": "Voici les résultats pour PACA..."}
                ]
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Chat with history accepted, response type: {data.get('type')}")
    
    def test_chat_meta_information(self):
        """Test that search results include meta information"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "30MW PACA",
                "session_id": f"test_{int(time.time())}",
                "history": []
            },
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        if data.get("type") == "search_results":
            # Should have meta information
            assert "meta" in data, "Missing 'meta' in search results"
            meta = data["meta"]
            
            print(f"✓ Meta information present: {list(meta.keys())}")
            if "total_results" in meta:
                print(f"  Total results: {meta['total_results']}")
            if "strategy" in meta:
                print(f"  Strategy: {meta['strategy']}")
        else:
            print(f"Note: Response type was {data.get('type')}")


class TestChatAssistantEdgeCases:
    """Edge case tests for chat assistant"""
    
    def test_chat_empty_message(self):
        """Test handling of empty message"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "",
                "session_id": "test_empty",
                "history": []
            },
            timeout=30
        )
        # Should handle gracefully (not crash)
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ Empty message handled with status {response.status_code}")
    
    def test_chat_missing_session_id(self):
        """Test that session_id has default value"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "test query",
                "history": []
            },
            timeout=30
        )
        # Should work with default session_id
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ Missing session_id handled with status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
