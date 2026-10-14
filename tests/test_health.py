def test_api_health(client):
    """Test health endpoint responds and reports FalkorDB connection status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "AlphaTrace"
    assert data["status"] == "healthy"
    assert data["database"]["backend"] == "FalkorDB"
    assert data["database"]["node_count"] > 0
    assert "SYNTHETIC" in data["synthetic_data_disclaimer"]
