import pytest
from src.llm.mcp_client import JarvisMCP

@pytest.fixture
def client():
    return JarvisMCP("http://127.0.0.1:8000")

def test_session_and_context(client):
    ctx0 = client.get_context()
    assert isinstance(ctx0, dict)
    client.push_context({"foo":"bar"})
    ctx1 = client.get_context()
    assert ctx1.get("foo") == "bar" 