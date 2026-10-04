import os
import io
import uuid
import pytest
from httpx import AsyncClient


async def create_authenticated_user(async_client: AsyncClient, name: str = "Test User"):
    """Helper to create a user and return the auth headers and user data."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"

    register_res = await async_client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert register_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    user = login_res.json()["user"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, user


@pytest.mark.asyncio
async def test_upload_document_success(async_client: AsyncClient):
    headers, user = await create_authenticated_user(async_client, "Uploader")

    file_content = b"This is a test document content for AI knowledge base."
    files = {
        "file": ("test_doc.txt", io.BytesIO(file_content), "text/plain"),
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 201
    doc = response.json()
    assert doc["original_filename"] == "test_doc.txt"
    assert doc["file_type"] == "txt"
    assert doc["file_size"] == len(file_content)
    assert doc["status"] == "uploaded"
    assert "id" in doc

    # Verify physical file existence in uploads/{user_id}/
    user_upload_dir = os.path.join("uploads", str(user["id"]))
    assert os.path.isdir(user_upload_dir)
    assert any(doc["filename"] in f for f in os.listdir(user_upload_dir))


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(async_client: AsyncClient):
    headers, _ = await create_authenticated_user(async_client)

    files = {
        "file": ("malicious.exe", io.BytesIO(b"binary content"), "application/octet-stream"),
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 415
    assert "not supported" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_rejects_oversized_file(async_client: AsyncClient, monkeypatch):
    headers, _ = await create_authenticated_user(async_client)

    # Mock max_file_size_bytes to a tiny limit (10 bytes) for testing
    from app.config import settings

    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0.00001)

    large_content = b"A" * 100
    files = {
        "file": ("large.txt", io.BytesIO(large_content), "text/plain"),
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files,
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_and_get_user_documents(async_client: AsyncClient):
    headers, _ = await create_authenticated_user(async_client, "List User")

    # Upload two documents
    for name in ["doc1.pdf", "doc2.docx"]:
        files = {"file": (name, io.BytesIO(b"Dummy content"), "application/octet-stream")}
        upload_res = await async_client.post("/api/v1/documents/upload", headers=headers, files=files)
        assert upload_res.status_code == 201

    # List documents
    list_res = await async_client.get("/api/v1/documents", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 2
    filenames = [d["original_filename"] for d in data["documents"]]
    assert "doc1.pdf" in filenames
    assert "doc2.docx" in filenames

    # Get specific document
    doc_id = data["documents"][0]["id"]
    get_res = await async_client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_user_isolation(async_client: AsyncClient):
    # User A uploads a doc
    headers_a, _ = await create_authenticated_user(async_client, "User A")
    files_a = {"file": ("private_a.pdf", io.BytesIO(b"User A secret content"), "application/pdf")}
    res_a = await async_client.post("/api/v1/documents/upload", headers=headers_a, files=files_a)
    doc_a_id = res_a.json()["id"]

    # User B tries to view and delete User A's document
    headers_b, _ = await create_authenticated_user(async_client, "User B")

    # User B list should NOT contain doc_a
    list_b = await async_client.get("/api/v1/documents", headers=headers_b)
    b_doc_ids = [d["id"] for d in list_b.json()["documents"]]
    assert doc_a_id not in b_doc_ids

    # User B GET doc A -> 404
    get_res = await async_client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B DELETE doc A -> 404
    del_res = await async_client.delete(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(async_client: AsyncClient):
    headers, user = await create_authenticated_user(async_client, "Deleter")

    # Upload document
    files = {"file": ("to_delete.txt", io.BytesIO(b"Delete me soon"), "text/plain")}
    upload_res = await async_client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc = upload_res.json()
    doc_id = doc["id"]
    filename = doc["filename"]

    file_path = os.path.join("uploads", str(user["id"]), filename)
    assert os.path.exists(file_path)

    # Delete document
    del_res = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["document_id"] == doc_id

    # Verify physical file removed
    assert not os.path.exists(file_path)

    # Verify 404 on subsequent get
    get_res = await async_client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_endpoints_require_authentication(async_client: AsyncClient):
    # Unauthenticated requests should all return 401
    assert (await async_client.get("/api/v1/documents")).status_code == 401
    assert (await async_client.get("/api/v1/documents/1")).status_code == 401
    assert (await async_client.delete("/api/v1/documents/1")).status_code == 401
    assert (await async_client.post("/api/v1/documents/upload")).status_code == 401
