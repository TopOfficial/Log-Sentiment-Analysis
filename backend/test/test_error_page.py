from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal

client = TestClient(app)

# Mock database dependency for testing
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_get_all_errors():
    response = client.get("/api/errors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Should return a list

def test_filter_errors_by_resolved_status():
    response = client.get("/api/errors/?resolved=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    for error in response.json():
        assert error["Resolved"] == True

def test_update_resolved_status():
    mock_data = {"resolved": True}
    response = client.patch("/api/errors/1", json=mock_data)
    assert response.status_code in [200, 404]  # 200 if item exists, 404 otherwise
    if response.status_code == 200:
        response_data = response.json()
        assert response_data["success"] == True
