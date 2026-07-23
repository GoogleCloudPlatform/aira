import asyncio
import logging
import os
import uuid

import ffmpeg
import pypdf

from api import dependencies, models, ports, typings

logger = logging.getLogger(__name__)


class KBProcessorService:

    def __init__(
        self,
        uow_builder: ports.UnitOfWorkBuilder,
        settings: typings.Settings,
        storage_factory: ports.StorageFactory,
        gen_ai: ports.GenAI,
    ):
        self.uow_builder = uow_builder
        self.settings = settings
        self.storage_factory = storage_factory
        self.gen_ai = gen_ai

    async def process_file(self, file_id: uuid.UUID) -> None:
        bucket_name = None
        file_path = None
        content_type = None
        filename = None

        async with self.uow_builder() as uow:
            kb_file = await uow.knowledge_base_repository.get(file_id)
            if not kb_file:
                logger.error(f"KnowledgeBaseFile {file_id} not found")
                return

            kb_file.status = "processing"
            bucket_name = kb_file.bucket_name
            file_path = kb_file.file_path
            content_type = kb_file.content_type
            filename = kb_file.filename
            await uow.commit()

        local_path = None
        local_wav_path = None
        temp_gcs_path = None

        try:
            storage = self.storage_factory(bucket_name)

            # 1. Download file from GCS
            local_file_name = f"kb_{file_id}"
            local_path = await storage.download(f"gs://{bucket_name}/{file_path}", local_file_name)


            # 2. Extract Text / Transcribe
            extracted_text = ""

            if content_type == "application/pdf":
                # PDF Text Extraction
                reader = pypdf.PdfReader(local_path)
                text_pages = []
                for page in reader.pages:
                    text_pages.append(page.extract_text() or "")
                extracted_text = "\n".join(text_pages)

            elif content_type.startswith(
                ("audio/", "video/")
            ):
                # Audio / Video Transcription
                local_wav_path = f"/tmp/kb_{file_id}.wav"

                # Extract/Convert to 16kHz mono WAV using ffmpeg
                await asyncio.to_thread(
                    ffmpeg.input(local_path)
                    .output(local_wav_path, acodec="pcm_s16le", ac=1, ar=16000)
                    .overwrite_output()
                    .run
                )

                # Upload WAV to GCS for Batch Transcription
                temp_gcs_path = f"kb-files/{file_id}/temp_audio.wav"
                await storage.upload_by_file(temp_gcs_path, local_wav_path)

                # Get audio duration using ffmpeg probe
                try:
                    probe = await asyncio.to_thread(ffmpeg.probe, local_path)
                    duration = float(probe["format"]["duration"])
                except Exception:
                    duration = 3600  # 1 hour fallback

                # Call Google Speech-to-Text v2
                speech = dependencies.get_speech_to_text(
                    "v2", self.settings, storage
                )
                gcs_uri = f"gs://{bucket_name}/{temp_gcs_path}"

                extracted_text = await speech.process(
                    phrases_id="",
                    path=gcs_uri,
                    desired=f"kb_{kb_file.id}.wav",
                    words=[],
                    duration=int(duration) + 10,
                    sample_rate=16000,
                    channels=1,
                    model_type="latest_long",
                )

            # Clean text of NUL characters to prevent database insert/update errors
            extracted_text = extracted_text.replace("\x00", "")

            # Generate description using AI
            try:
                description = await self.gen_ai.generate_description(extracted_text)
            except Exception as e:
                logger.warning(f"Failed to generate description for {file_id}: {e}")
                description = "Failed to generate AI description."

            # 3. Update DB record with transcript and description
            async with self.uow_builder() as uow:
                kb_file = await uow.knowledge_base_repository.get(file_id)
                if not kb_file:
                    logger.warning(f"KnowledgeBaseFile {file_id} was deleted concurrently. Stopping.")
                    return
                kb_file.transcription = extracted_text
                kb_file.description = description
                await uow.commit()

            # 4. Auto index in Vertex AI Datastore (if configured)
            datastore_id = self.settings.get("vertex_datastore_id")
            project_id = self.settings.get("project_id")

            if datastore_id and project_id:
                try:
                    from google.cloud import discoveryengine_v1 as discoveryengine

                    client = discoveryengine.DocumentServiceClient()
                    parent = client.branch_path(
                        project=project_id,
                        location="global",
                        data_store=datastore_id,
                        branch="default_branch",
                    )
                    request = discoveryengine.ImportDocumentsRequest(
                        parent=parent,
                        gcs_source=discoveryengine.GcsSource(
                            input_uris=[
                                f"gs://{bucket_name}/{file_path}"
                            ],
                            data_schema="custom",
                        ),
                        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
                    )
                    await asyncio.to_thread(
                        client.import_documents, request=request
                    )

                    async with self.uow_builder() as uow:
                        kb_file = await uow.knowledge_base_repository.get(file_id)
                        if not kb_file:
                            logger.warning(f"KnowledgeBaseFile {file_id} was deleted concurrently. Stopping.")
                            return
                        kb_file.indexing_status = "completed"
                        await uow.commit()
                except Exception as e:
                    logger.error(f"Failed indexing in Vertex AI Datastore: {str(e)}")
                    async with self.uow_builder() as uow:
                        kb_file = await uow.knowledge_base_repository.get(file_id)
                        if kb_file:
                            kb_file.indexing_status = "failed"
                            await uow.commit()
            else:
                logger.info("Skipping Vertex AI Datastore indexing (no datastore_id / project_id configured)")
                async with self.uow_builder() as uow:
                    kb_file = await uow.knowledge_base_repository.get(file_id)
                    if not kb_file:
                        logger.warning(f"KnowledgeBaseFile {file_id} was deleted concurrently. Stopping.")
                        return
                    kb_file.indexing_status = "completed"  # set to complete since not configured
                    await uow.commit()

            # 5. Extract vectors and save them in Vector Search
            if extracted_text:
                await self.gen_ai.index_document(
                    doc_id=str(file_id),
                    text=extracted_text,
                    metadata={
                        "filename": filename,
                        "content_type": content_type,
                    },
                )
                async with self.uow_builder() as uow:
                    kb_file = await uow.knowledge_base_repository.get(file_id)
                    if not kb_file:
                        logger.warning(f"KnowledgeBaseFile {file_id} was deleted concurrently. Stopping.")
                        return
                    kb_file.vector_status = "completed"
                    kb_file.status = "completed"
                    await uow.commit()
            else:
                async with self.uow_builder() as uow:
                    kb_file = await uow.knowledge_base_repository.get(file_id)
                    if not kb_file:
                        logger.warning(f"KnowledgeBaseFile {file_id} was deleted concurrently. Stopping.")
                        return
                    kb_file.vector_status = "completed"  # complete empty vectors
                    kb_file.status = "completed"
                    await uow.commit()

        except Exception as err:
            logger.exception(f"Error processing knowledge base file {file_id}: {err}")
            async with self.uow_builder() as uow:
                kb_file = await uow.knowledge_base_repository.get(file_id)
                if kb_file:
                    kb_file.status = "failed"
                    kb_file.indexing_status = "failed"
                    kb_file.vector_status = "failed"
                    await uow.commit()

        finally:
            # 6. Clean up GCS temp files
            if temp_gcs_path and local_wav_path and bucket_name:
                try:
                    blob = storage.client.bucket(bucket_name).blob(
                        temp_gcs_path
                    )
                    await asyncio.to_thread(blob.delete)
                except Exception:
                    pass

            # Clean up local filesystem
            for path in [local_path, local_wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
