import base64
import dataclasses
import json
import logging
import urllib.parse
import uuid

import fastapi
import fastapi_injector
from pydantic import BaseModel

from api import dependencies, errors, models, ports, typings
from api.adapters import google
from api.helpers import auth
from api.routers.schemas import PubsubRequest

from . import schemas

router = fastapi.APIRouter(tags=["knowledge-base"])
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class KBProcessingMessage(typings.Message):
    file_id: str


@router.post(
    "/register-uploads",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.RegisterUploadsResponse,
)
async def register_uploads(
    request: schemas.RegisterUploadsRequest,
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    storage_factory: ports.StorageFactory = fastapi_injector.Injected(
        ports.StorageFactory
    ),
) -> schemas.RegisterUploadsResponse:
    bucket_name = settings.get(
        "kb_bucket_path", f"{settings.get('project_id')}-aira-kb-files"
    )

    storage = storage_factory(bucket_name)

    response_files = []

    async with uow_builder() as uow:
        for file_req in request.files:
            # 1. Validation
            allowed_types = {
                "application/pdf",
                "video/mp4",
                "video/webm",
                "audio/mpeg",
                "audio/mp3",
                "audio/wav",
                "audio/x-wav",
            }
            if file_req.content_type not in allowed_types:
                raise fastapi.HTTPException(
                    status_code=400,
                    detail=f"Content type {file_req.content_type} is not allowed.",
                )

            # Max size validation: 200MB for PDF, 5GB for video, 500MB for audio
            max_pdf_size = 200 * 1024 * 1024
            max_video_size = 5 * 1024 * 1024 * 1024
            max_audio_size = 500 * 1024 * 1024
            if file_req.content_type == "application/pdf":
                if file_req.size_bytes > max_pdf_size:
                    raise fastapi.HTTPException(
                        status_code=400,
                        detail="PDF file size exceeds the 200MB limit.",
                    )
            elif file_req.content_type.startswith("video/"):
                if file_req.size_bytes > max_video_size:
                    raise fastapi.HTTPException(
                        status_code=400,
                        detail="Video file size exceeds the 5GB limit.",
                    )
            elif file_req.content_type.startswith("audio/"):
                if file_req.size_bytes > max_audio_size:
                    raise fastapi.HTTPException(
                        status_code=400,
                        detail="Audio file size exceeds the 500MB limit.",
                    )

            # Sanitize original filename
            safe_original_name = (
                urllib.parse.unquote(file_req.filename)
                .replace("/", "_")
                .replace("\\", "_")
            )

            file_id = uuid.uuid4()
            extension = (
                safe_original_name.split(".")[-1]
                if "." in safe_original_name
                else "bin"
            )
            file_path = f"kb-files/{file_id}/{file_id}.{extension}"

            # 2. Database entry
            kb_file = models.KnowledgeBaseFile(
                filename=safe_original_name,
                file_path=file_path,
                bucket_name=bucket_name,
                content_type=file_req.content_type,
                size_bytes=file_req.size_bytes,
                status="registering",
                indexing_status="pending",
                vector_status="pending",
                transcription=None,
            )
            kb_file.id = file_id
            await uow.knowledge_base_repository.create(kb_file)


            # 3. Signed GCS URL
            signed_url = await storage.generate_signed_url(
                path=file_path, mimetype=file_req.content_type, method="PUT"
            )

            response_files.append(
                schemas.RegisterUploadItemResponse(
                    id=file_id,
                    filename=safe_original_name,
                    signed_url=signed_url,
                )
            )

        await uow.commit()

    return schemas.RegisterUploadsResponse(files=response_files)


@router.post(
    "/files/{id}/confirm-upload",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.ConfirmUploadResponse,
)
async def confirm_upload(
    id: uuid.UUID,
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
) -> schemas.ConfirmUploadResponse:
    async with uow_builder() as uow:
        kb_file = await uow.knowledge_base_repository.get(id)
        if not kb_file:
            raise fastapi.HTTPException(status_code=404, detail="File not found")

        if kb_file.status != "registering":
            raise fastapi.HTTPException(
                status_code=400,
                detail=f"Cannot confirm upload for file in state: {kb_file.status}",
            )

        kb_file.status = "uploaded"
        await uow.commit()

        # Publish Pub/Sub message
        message = KBProcessingMessage(file_id=str(kb_file.id))
        topic_name = settings.get("kb_processing_topic", "kb_processing_topic")
        await publisher.publish(message=message, topic=topic_name)

    return schemas.ConfirmUploadResponse(
        id=kb_file.id,
        status="uploaded",
        message="Upload confirmed, processing started.",
    )


@router.get(
    "/files",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def list_files(
    page: int = fastapi.Query(1, ge=1),
    size: int = fastapi.Query(10, ge=-1),
    list_query: ports.ListKnowledgeBaseFiles = fastapi_injector.Injected(
        ports.ListKnowledgeBaseFiles
    ),
):
    items, metadata = await list_query(page_size=size, page=page)
    return {
        "items": [schemas.KnowledgeBaseFileGet.from_orm(i) for i in items],
        "total": metadata.total_items,
        "page": metadata.current_page,
        "size": metadata.page_size,
        "pages": metadata.total_pages,
    }


@router.delete(
    "/files/{id}",
    status_code=244,
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_file(
    id: uuid.UUID,
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    storage_factory: ports.StorageFactory = fastapi_injector.Injected(
        ports.StorageFactory
    ),
    gen_ai: ports.GenAI = fastapi_injector.Injected(ports.GenAI),
):
    async with uow_builder() as uow:
        kb_file = await uow.knowledge_base_repository.get(id)
        if not kb_file:
            raise fastapi.HTTPException(status_code=404, detail="File not found")

        # 1. Delete GCS Object
        try:
            storage = storage_factory(kb_file.bucket_name)
            blob = storage.client.bucket(kb_file.bucket_name).blob(kb_file.file_path)
            blob.delete()
        except Exception as e:
            logger.warning(
                f"Failed to delete GCS object {kb_file.file_path}: {str(e)}"
            )

        # 2. Delete vectors from Vector Search
        try:
            await gen_ai.delete_document(str(id))
        except Exception as e:
            logger.warning(
                f"Failed to delete document {id} from vector store: {str(e)}"
            )

        # 3. Purge document from Vertex AI Datastore if configured
        datastore_id = settings.get("vertex_datastore_id")
        project_id = settings.get("project_id")
        if datastore_id and project_id:
            try:
                from google.cloud import discoveryengine_v1 as discoveryengine
                import asyncio

                client = discoveryengine.DocumentServiceClient()
                parent = client.branch_path(
                    project=project_id,
                    location="global",
                    data_store=datastore_id,
                    branch="default_branch",
                )
                gcs_uri = f"gs://{kb_file.bucket_name}/{kb_file.file_path}"
                request = discoveryengine.PurgeDocumentsRequest(
                    parent=parent,
                    filter=f'gcs_uri="{gcs_uri}"',
                    force=True
                )
                await asyncio.to_thread(client.purge_documents, request=request)
            except Exception as e:
                logger.warning(f"Failed to purge document from Discovery Engine: {str(e)}")

        # 4. Delete database entry
        await uow.knowledge_base_repository.delete(kb_file)
        await uow.commit()

    return fastapi.Response(status_code=204)


@router.get(
    "/files/{id}/view",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def get_file_view_url(
    id: uuid.UUID,
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    storage_factory: ports.StorageFactory = fastapi_injector.Injected(
        ports.StorageFactory
    ),
) -> dict[str, str]:
    async with uow_builder() as uow:
        kb_file = await uow.knowledge_base_repository.get(id)
        if not kb_file:
            raise fastapi.HTTPException(status_code=404, detail="File not found")

        storage = storage_factory(kb_file.bucket_name)
        url = await storage.generate_signed_url(
            path=kb_file.file_path, mimetype=kb_file.content_type, method="GET"
        )
        return {"url": url}


@router.post(
    "/files/{id}/retry",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def retry_file_processing(
    id: uuid.UUID,
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    publisher: ports.MessagePublisher = fastapi_injector.Injected(
        ports.MessagePublisher
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
) -> dict[str, str]:
    async with uow_builder() as uow:
        kb_file = await uow.knowledge_base_repository.get(id)
        if not kb_file:
            raise fastapi.HTTPException(status_code=404, detail="File not found")

        kb_file.status = "processing"
        kb_file.indexing_status = "pending"
        kb_file.vector_status = "pending"
        kb_file.transcription = None
        kb_file.description = None
        await uow.commit()

        # Publish Pub/Sub message to trigger processing
        payload = {"file_id": str(kb_file.id)}
        await publisher.publish(
            topic=settings.get("pubsub_topic", ""),
            message=json.dumps(payload).encode("utf-8")
        )

        return {"message": "Processing retried successfully"}


@router.post("/process-message", response_model=None, include_in_schema=False)
async def process_message(
    body: PubsubRequest = fastapi.Body(...),
    background_tasks: fastapi.BackgroundTasks = fastapi.BackgroundTasks(),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    processor: dependencies.KBProcessorService = fastapi_injector.Injected(
        dependencies.KBProcessorService
    ),
) -> fastapi.Response:
    try:
        data = base64.b64decode(body.message.data).decode("utf-8")
        payload = json.loads(data)
        file_id_str = payload.get("file_id")
        if not file_id_str:
            logger.error("Missing file_id in Pub/Sub payload")
            return fastapi.Response(status_code=200)

        file_id = uuid.UUID(file_id_str)
    except Exception as e:
        logger.error(f"Failed to parse Pub/Sub payload: {str(e)}")
        return fastapi.Response(status_code=200)

    # Trigger async background processing
    background_tasks.add_task(processor.process_file, file_id)

    return fastapi.Response(status_code=200)

