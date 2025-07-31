from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_all_knowledge_base_entries():
    response = client.get("/api/knowledgebase/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_add_new_knowledge_base_entry():
    mock_payload = {
        "Content": "High CPU temperature",
        "ContentType": "Warning",
        "MachineId": 1,
        "Solution": "Check the cooling system and reduce load"
    }
    response = client.post("/api/knowledgebase/", json=mock_payload)
    assert response.status_code in [200, 201]  # OK or Created response
    assert "KnowledgeId" in response.json()

def test_update_knowledge_base_entry():
    mock_payload = {"solution": "Replace the cooling system"}
    response = client.patch("/api/knowledgebase/1", json=mock_payload)
    assert response.status_code in [200, 404]  # 200 if entry exists, 404 otherwise
    if response.status_code == 200:
        assert response.json()["Solution"] == "Replace the cooling system"
