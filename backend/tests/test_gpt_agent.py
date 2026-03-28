"""
Test GPT Agent Configuration Endpoints
Tests for /api/gpt/config, /api/gpt/openapi-schema, /api/gpt/system-prompt
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


class TestGPTConfig:
    """Tests for GET /api/gpt/config endpoint"""
    
    def test_gpt_config_returns_200(self):
        """GET /api/gpt/config returns 200"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/gpt/config returns 200")
    
    def test_gpt_config_has_required_fields(self):
        """Config contains name, description, system_prompt, openapi_schema_url, setup_instructions"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        required_fields = ['name', 'description', 'system_prompt', 'openapi_schema_url', 'setup_instructions']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Config has all required fields: {required_fields}")
    
    def test_gpt_config_name_is_correct(self):
        """Config name is 'Cockpit Immo — Expert DC France'"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        assert data['name'] == "Cockpit Immo — Expert DC France", f"Unexpected name: {data['name']}"
        print(f"✓ Config name is correct: {data['name']}")
    
    def test_gpt_config_description_not_empty(self):
        """Config description is not empty"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        assert len(data['description']) > 50, "Description too short"
        print(f"✓ Config description is present ({len(data['description'])} chars)")
    
    def test_gpt_config_system_prompt_not_empty(self):
        """System prompt is substantial (>500 chars)"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        assert len(data['system_prompt']) > 500, "System prompt too short"
        print(f"✓ System prompt is substantial ({len(data['system_prompt'])} chars)")
    
    def test_gpt_config_openapi_url_is_https(self):
        """OpenAPI schema URL uses HTTPS"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        assert data['openapi_schema_url'].startswith('https://'), f"URL not HTTPS: {data['openapi_schema_url']}"
        assert '/api/gpt/openapi-schema' in data['openapi_schema_url'], "URL doesn't contain correct path"
        print(f"✓ OpenAPI URL is HTTPS: {data['openapi_schema_url']}")
    
    def test_gpt_config_setup_instructions_has_steps(self):
        """Setup instructions has 6 steps"""
        response = requests.get(f"{BASE_URL}/api/gpt/config")
        data = response.json()
        
        instructions = data['setup_instructions']
        assert isinstance(instructions, dict), "setup_instructions should be a dict"
        assert len(instructions) >= 5, f"Expected at least 5 steps, got {len(instructions)}"
        
        # Check step_1 exists
        assert 'step_1' in instructions, "Missing step_1"
        print(f"✓ Setup instructions has {len(instructions)} steps")


class TestGPTOpenAPISchema:
    """Tests for GET /api/gpt/openapi-schema endpoint"""
    
    def test_openapi_schema_returns_200(self):
        """GET /api/gpt/openapi-schema returns 200"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/gpt/openapi-schema returns 200")
    
    def test_openapi_schema_version_3_1_0(self):
        """Schema is OpenAPI 3.1.0"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert data.get('openapi') == '3.1.0', f"Expected OpenAPI 3.1.0, got {data.get('openapi')}"
        print("✓ Schema is OpenAPI 3.1.0")
    
    def test_openapi_schema_has_info(self):
        """Schema has info with title and version"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert 'info' in data, "Missing info section"
        assert 'title' in data['info'], "Missing title in info"
        assert 'version' in data['info'], "Missing version in info"
        print(f"✓ Schema info: {data['info']['title']} v{data['info']['version']}")
    
    def test_openapi_schema_server_url_is_https(self):
        """Server URL in schema uses HTTPS"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert 'servers' in data, "Missing servers section"
        assert len(data['servers']) > 0, "No servers defined"
        server_url = data['servers'][0]['url']
        assert server_url.startswith('https://'), f"Server URL not HTTPS: {server_url}"
        print(f"✓ Server URL is HTTPS: {server_url}")
    
    def test_openapi_schema_has_dc_search_endpoint(self):
        """Schema includes POST /api/dc/search"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert 'paths' in data, "Missing paths section"
        assert '/api/dc/search' in data['paths'], "Missing /api/dc/search path"
        assert 'post' in data['paths']['/api/dc/search'], "Missing POST method for /api/dc/search"
        print("✓ Schema includes POST /api/dc/search")
    
    def test_openapi_schema_dc_search_has_parameters(self):
        """POST /api/dc/search has documented parameters"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        dc_search = data['paths']['/api/dc/search']['post']
        assert 'requestBody' in dc_search, "Missing requestBody"
        
        schema = dc_search['requestBody']['content']['application/json']['schema']
        props = schema.get('properties', {})
        
        expected_params = ['mw_target', 'mw_min', 'max_delay_months', 'region', 'strategy', 'grid_priority', 'brownfield_only']
        for param in expected_params:
            assert param in props, f"Missing parameter: {param}"
        
        print(f"✓ DC search has all parameters: {expected_params}")
    
    def test_openapi_schema_has_site_detail_endpoint(self):
        """Schema includes GET /api/dc/site/{site_id}"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert '/api/dc/site/{site_id}' in data['paths'], "Missing /api/dc/site/{site_id} path"
        assert 'get' in data['paths']['/api/dc/site/{site_id}'], "Missing GET method"
        print("✓ Schema includes GET /api/dc/site/{site_id}")
    
    def test_openapi_schema_has_s3renr_summary(self):
        """Schema includes GET /api/s3renr/summary"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert '/api/s3renr/summary' in data['paths'], "Missing /api/s3renr/summary path"
        assert 'get' in data['paths']['/api/s3renr/summary'], "Missing GET method"
        print("✓ Schema includes GET /api/s3renr/summary")
    
    def test_openapi_schema_has_top_opportunities(self):
        """Schema includes GET /api/s3renr/top-opportunities"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert '/api/s3renr/top-opportunities' in data['paths'], "Missing /api/s3renr/top-opportunities path"
        assert 'get' in data['paths']['/api/s3renr/top-opportunities'], "Missing GET method"
        print("✓ Schema includes GET /api/s3renr/top-opportunities")
    
    def test_openapi_schema_has_components(self):
        """Schema has components/schemas section"""
        response = requests.get(f"{BASE_URL}/api/gpt/openapi-schema")
        data = response.json()
        
        assert 'components' in data, "Missing components section"
        assert 'schemas' in data['components'], "Missing schemas in components"
        
        expected_schemas = ['SearchResponse', 'SiteResult', 'SiteDetail']
        for schema_name in expected_schemas:
            assert schema_name in data['components']['schemas'], f"Missing schema: {schema_name}"
        
        print(f"✓ Schema has components: {expected_schemas}")


class TestGPTSystemPrompt:
    """Tests for GET /api/gpt/system-prompt endpoint"""
    
    def test_system_prompt_returns_200(self):
        """GET /api/gpt/system-prompt returns 200"""
        response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/gpt/system-prompt returns 200")
    
    def test_system_prompt_has_prompt_field(self):
        """Response has system_prompt field"""
        response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        data = response.json()
        
        assert 'system_prompt' in data, "Missing system_prompt field"
        print("✓ Response has system_prompt field")
    
    def test_system_prompt_content_is_french(self):
        """System prompt is in French"""
        response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        data = response.json()
        
        prompt = data['system_prompt']
        # Check for French keywords
        french_keywords = ['Tu es', 'data centers', 'France', 'Recherche', 'résultats']
        found = sum(1 for kw in french_keywords if kw in prompt)
        assert found >= 3, f"Prompt doesn't appear to be in French (found {found}/5 keywords)"
        print(f"✓ System prompt is in French ({found}/5 keywords found)")
    
    def test_system_prompt_mentions_api_endpoints(self):
        """System prompt mentions API endpoints"""
        response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        data = response.json()
        
        prompt = data['system_prompt']
        endpoints = ['/api/dc/search', '/api/dc/site', '/api/s3renr/summary', '/api/s3renr/top-opportunities']
        found = sum(1 for ep in endpoints if ep in prompt)
        assert found >= 3, f"Prompt doesn't mention enough endpoints (found {found}/4)"
        print(f"✓ System prompt mentions {found}/4 API endpoints")
    
    def test_system_prompt_has_parameter_mapping(self):
        """System prompt explains parameter mapping (e.g., '20MW' -> mw_target: 20)"""
        response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        data = response.json()
        
        prompt = data['system_prompt']
        assert 'mw_target' in prompt, "Missing mw_target parameter explanation"
        assert 'region' in prompt, "Missing region parameter explanation"
        assert 'strategy' in prompt, "Missing strategy parameter explanation"
        print("✓ System prompt has parameter mapping explanations")


class TestGPTEndpointsIntegration:
    """Integration tests - verify schema URL works and matches config"""
    
    def test_schema_url_from_config_is_accessible(self):
        """OpenAPI schema URL from config is accessible"""
        # Get config
        config_response = requests.get(f"{BASE_URL}/api/gpt/config")
        config = config_response.json()
        
        schema_url = config['openapi_schema_url']
        
        # Fetch schema from URL
        schema_response = requests.get(schema_url)
        assert schema_response.status_code == 200, f"Schema URL not accessible: {schema_url}"
        
        schema = schema_response.json()
        assert schema.get('openapi') == '3.1.0', "Schema from URL is not valid OpenAPI"
        print(f"✓ Schema URL from config is accessible and valid")
    
    def test_system_prompt_matches_config(self):
        """System prompt from /api/gpt/system-prompt matches config"""
        config_response = requests.get(f"{BASE_URL}/api/gpt/config")
        prompt_response = requests.get(f"{BASE_URL}/api/gpt/system-prompt")
        
        config = config_response.json()
        prompt_data = prompt_response.json()
        
        assert config['system_prompt'] == prompt_data['system_prompt'], "System prompts don't match"
        print("✓ System prompt from both endpoints matches")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
