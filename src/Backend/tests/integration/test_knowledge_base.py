import base64
import json
import uuid
import pytest
import sqlalchemy as sa
from httpx import AsyncClient

from api import models


@pytest.mark.asyncio
async def test_register_uploads(client: AsyncClient, session_factory):
    payload = {
        "files": [
            {
                "filename": "pedagogy-guide.pdf",
                "content_type": "application/pdf",
                "size_bytes": 10240,
            },
            {
                "filename": "lecture-video.mp4",
                "content_type": "video/mp4",
                "size_bytes": 5242880,
            },
        ]
    }

    response = await client.post(
        "/api/v1/admin/knowledge-base/register-uploads", json=payload
    )
    assert response.status_code == 200

    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 2

    # Check first item response schema
    pdf_item = data["files"][0]
    assert pdf_item["filename"] == "pedagogy-guide.pdf"
    assert "signed_url" in pdf_item
    assert "signed=true" in pdf_item["signed_url"]

    # Check database records
    async with session_factory() as session:
        stmt = sa.select(models.KnowledgeBaseFile).where(
            models.KnowledgeBaseFile.filename == "pedagogy-guide.pdf"
        )
        res = await session.execute(stmt)
        db_file = res.scalars().one()

        assert db_file.status == "registering"
        assert db_file.content_type == "application/pdf"
        assert db_file.bucket_name == "test-kb-bucket"


@pytest.mark.asyncio
async def test_register_uploads_invalid_type(client: AsyncClient):
    payload = {
        "files": [
            {
                "filename": "malicious.exe",
                "content_type": "application/octet-stream",
                "size_bytes": 5000,
            }
        ]
    }
    response = await client.post(
        "/api/v1/admin/knowledge-base/register-uploads", json=payload
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_uploads_exceed_limit(client: AsyncClient):
    payload = {
        "files": [
            {
                "filename": "too-large.pdf",
                "content_type": "application/pdf",
                "size_bytes": 201 * 1024 * 1024,  # 201MB (limit is 200MB)
            }
        ]
    }
    response = await client.post(
        "/api/v1/admin/knowledge-base/register-uploads", json=payload
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_confirm_upload(client: AsyncClient, session_factory, mock_publisher):
    # 1. Register file
    register_payload = {
        "files": [
            {
                "filename": "classroom-dynamics.mp4",
                "content_type": "video/mp4",
                "size_bytes": 20480,
            }
        ]
    }
    register_res = await client.post(
        "/api/v1/admin/knowledge-base/register-uploads", json=register_payload
    )
    file_id = register_res.json()["files"][0]["id"]

    # 2. Confirm Upload
    confirm_res = await client.post(
        f"/api/v1/admin/knowledge-base/files/{file_id}/confirm-upload"
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "uploaded"

    # 3. Check DB
    async with session_factory() as session:
        stmt = sa.select(models.KnowledgeBaseFile).where(
            models.KnowledgeBaseFile.id == uuid.UUID(file_id)
        )
        res = await session.execute(stmt)
        db_file = res.scalars().one()
        assert db_file.status == "uploaded"

    # 4. Check Pub/Sub Mock
    assert len(mock_publisher.published) == 1
    published_msg, topic = mock_publisher.published[0]
    assert published_msg.file_id == file_id
    assert topic == "kb_processing_topic"


@pytest.mark.asyncio
async def test_list_files(client: AsyncClient, session_factory):
    # Clean database first
    async with session_factory() as session:
        await session.execute(sa.delete(models.KnowledgeBaseFile))
        await session.commit()

    # Pre-populate database with files
    async with session_factory() as session:
        f1_id = uuid.uuid4()
        f1 = models.KnowledgeBaseFile(
            filename="doc1.pdf",
            file_path="kb-files/doc1.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=5000,
            status="completed",
            indexing_status="completed",
            vector_status="completed",
        )
        f1.id = f1_id

        f2_id = uuid.uuid4()
        f2 = models.KnowledgeBaseFile(
            filename="doc2.pdf",
            file_path="kb-files/doc2.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=8000,
            status="processing",
            indexing_status="pending",
            vector_status="pending",
        )
        f2.id = f2_id
        session.add(f1)
        session.add(f2)
        await session.commit()

    response = await client.get("/api/v1/admin/knowledge-base/files?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["filename"] == "doc2.pdf"  # ordered by desc created_at


@pytest.mark.asyncio
async def test_delete_file(client: AsyncClient, session_factory, mock_gen_ai):
    from conftest import MockStorage
    MockStorage.deleted_paths = []
    mock_gen_ai.deleted_doc_ids = []

    # 1. Populate a file
    file_id = uuid.uuid4()
    async with session_factory() as session:
        f = models.KnowledgeBaseFile(
            filename="trash.pdf",
            file_path="kb-files/trash.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=1000,
            status="completed",
            indexing_status="completed",
            vector_status="completed",
        )
        f.id = file_id
        session.add(f)
        await session.commit()

    # 2. Delete file
    response = await client.delete(f"/api/v1/admin/knowledge-base/files/{file_id}")
    assert response.status_code == 204

    # 3. Verify GCS and Vector DB deletion
    assert "kb-files/trash.pdf" in MockStorage.deleted_paths
    assert str(file_id) in mock_gen_ai.deleted_doc_ids

    # 4. Verify DB deletion
    async with session_factory() as session:
        stmt = sa.select(models.KnowledgeBaseFile).where(
            models.KnowledgeBaseFile.id == file_id
        )
        res = await session.execute(stmt)
        assert res.scalars().one_or_none() is None


@pytest.mark.asyncio
async def test_process_message_endpoint(client: AsyncClient, session_factory):
    # 1. Populate file
    file_id = uuid.uuid4()
    async with session_factory() as session:
        f = models.KnowledgeBaseFile(
            filename="process-target.pdf",
            file_path="kb-files/process-target.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=1000,
            status="uploaded",
            indexing_status="pending",
            vector_status="pending",
        )
        f.id = file_id
        session.add(f)
        await session.commit()

    # 2. Simulate Pub/Sub Push Message
    payload_data = {"file_id": str(file_id)}
    encoded_data = base64.b64encode(json.dumps(payload_data).encode("utf-8")).decode(
        "utf-8"
    )

    pubsub_req = {
        "subscription": "kb_processing_subs",
        "message": {"messageId": "999", "data": encoded_data},
    }

    response = await client.post(
        "/api/v1/admin/knowledge-base/process-message", json=pubsub_req
    )
    assert response.status_code == 200

    # 3. Check file status transitions to 'completed'
    import asyncio
    db_file = None
    for _ in range(20):
        async with session_factory() as session:
            stmt = sa.select(models.KnowledgeBaseFile).where(
                models.KnowledgeBaseFile.id == file_id
            )
            res = await session.execute(stmt)
            db_file = res.scalars().one()
            if db_file.status == "completed":
                break
        await asyncio.sleep(0.2)

    assert db_file is not None
    assert db_file.status == "completed"
    assert db_file.indexing_status == "completed"
    assert db_file.vector_status == "completed"


@pytest.mark.asyncio
async def test_get_file_view_url(client: AsyncClient, session_factory):
    # 1. Populate a file
    file_id = uuid.uuid4()
    async with session_factory() as session:
        f = models.KnowledgeBaseFile(
            filename="view.pdf",
            file_path="kb-files/view.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=1000,
            status="completed",
            indexing_status="completed",
            vector_status="completed",
        )
        f.id = file_id
        session.add(f)
        await session.commit()

    # 2. Call view URL endpoint
    response = await client.get(f"/api/v1/admin/knowledge-base/files/{file_id}/view")
    assert response.status_code == 200
    assert "url" in response.json()
    assert "signed=true" in response.json()["url"]


@pytest.mark.asyncio
async def test_retry_file_processing(client: AsyncClient, session_factory):
    # 1. Populate a failed file
    file_id = uuid.uuid4()
    async with session_factory() as session:
        f = models.KnowledgeBaseFile(
            filename="retry.pdf",
            file_path="kb-files/retry.pdf",
            bucket_name="test-kb-bucket",
            content_type="application/pdf",
            size_bytes=1000,
            status="failed",
            indexing_status="failed",
            vector_status="failed",
        )
        f.id = file_id
        session.add(f)
        await session.commit()

    # 2. Call retry endpoint
    response = await client.post(f"/api/v1/admin/knowledge-base/files/{file_id}/retry")
    assert response.status_code == 200
    assert response.json()["message"] == "Processing retried successfully"

    # 3. Check status is updated back to processing
    async with session_factory() as session:
        stmt = sa.select(models.KnowledgeBaseFile).where(models.KnowledgeBaseFile.id == file_id)
        res = await session.execute(stmt)
        db_file = res.scalars().one()
        assert db_file.status == "processing"
        assert db_file.indexing_status == "pending"
        assert db_file.vector_status == "pending"

