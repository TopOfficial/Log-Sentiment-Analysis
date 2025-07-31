from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

def test_get_solution_for_error():
    # Payload must match the schema exactly
    mock_payload = {"log_content": "Disk space running low"}
    response = client.post("/api/chat/solution", json=mock_payload)

    # Assert that the response is successful
    assert response.status_code == 200
    response_data = response.json()

    # Response should include either a known solution or a generated solution
    assert "knownError" in response_data
    if response_data["knownError"]:
        assert "solution" in response_data
    else:
        assert "generatedSolution" in response_data


def test_create_conversation_with_messages():
    mock_payload = {
        "conversation": {"LogId": 1},
        "messages": [
            {"SentDate": datetime(2023, 10, 1, 10, 0, 0).isoformat(), "Role": 1, "Content": "What does this error mean?"},
            {"SentDate": datetime(2023, 10, 1, 10, 1, 0).isoformat(), "Role": 0, "Content": "Disk space is running low."}
        ]
    }

    response = client.post("/api/chat/conversation", json=mock_payload)
    assert response.status_code == 200

    # Validate response
    response_data = response.json()
    assert "ConversationId" in response_data
    assert response_data["LogId"] == 1

def test_add_messages_to_existing_conversation():
    conversation_id = 1  # Ensure this conversation exists in the database
    mock_payload = [
    {
        "SentDate": datetime(2023, 10, 1, 11, 0, 0).isoformat(),  # Convert datetime to ISO 8601 string
        "Role": 1,
        "Content": "Another question about the error.",
        "ConversationId": conversation_id
    },
    {
        "SentDate": datetime(2023, 10, 1, 11, 1, 0).isoformat(),  # Convert datetime to ISO 8601 string
        "Role": 0,
        "Content": "Please provide more details.",
        "ConversationId": conversation_id
    }
]
    response = client.put(f"/api/chat/conversation/{conversation_id}/messages", json=mock_payload)
    assert response.status_code == 200

    # Validate response
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["ConversationId"] == conversation_id



