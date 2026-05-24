import uuid

import fastapi
import fastapi_injector
from api import models, ports, typings
from api.adapters import google
from api.helpers import auth

from . import schemas

router = fastapi.APIRouter(tags=["tutorials"])


@router.post(
    "",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.TutorialGet,
)
async def create_tutorial(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
    audience: str = fastapi.Form(...),
    source_type: str = fastapi.Form(...),
    url: str | None = fastapi.Form(None),
    file: fastapi.UploadFile | None = fastapi.File(None),
) -> schemas.TutorialGet:
    if audience not in {"educator", "admin"}:
        raise fastapi.HTTPException(status_code=400, detail="Invalid audience")

    if source_type not in {"upload", "link"}:
        raise fastapi.HTTPException(status_code=400, detail="Invalid source type")

    resolved_url = ""
    filename = None
    file_path = None
    bucket_name = None

    if source_type == "upload":
        if not file:
            raise fastapi.HTTPException(
                status_code=400, detail="File is required for upload"
            )
        if not file.filename.endswith(".pdf"):
            raise fastapi.HTTPException(
                status_code=400, detail="Only PDF files are allowed"
            )

        content = await file.read()

        # Public files bucket configuration
        bucket_name = (
            settings.get("public_bucket_path")
            or f"{settings.get('project_id')}-store-public-files"
        )

        file_id = uuid.uuid4()
        file_path = f"tutorial/tutorial_{audience}_{file_id}.pdf"
        filename = file.filename

        public_storage = google.CloudStorage(
            project_id=settings.get("project_id", ""),
            storage_path=bucket_name,
            creds_path=settings.get("gcp_storage_credentials", ""),
        )

        await public_storage.upload_by_text(
            file_path, content, content_type="application/pdf"
        )
        resolved_url = f"https://storage.googleapis.com/{bucket_name}/{file_path}"

    elif source_type == "link":
        if not url:
            raise fastapi.HTTPException(
                status_code=400, detail="URL is required for link"
            )
        resolved_url = url

    tutorial = models.Tutorial(
        audience=audience,
        source_type=source_type,
        filename=filename,
        file_path=file_path,
        bucket_name=bucket_name,
        url=resolved_url,
    )

    async with uow_builder() as uow:
        tutorial_model = await uow.tutorial_repository.create(tutorial)
        await uow.commit()
        return schemas.TutorialGet.from_orm(tutorial_model)


@router.get(
    "/latest/{audience}",
    dependencies=[
        fastapi.Security(auth.get_token, scopes=["user", "user.impersonate", "admin"])
    ],
)
async def get_latest_tutorial(
    audience: str = fastapi.Path(...),
    locale: str = fastapi.Query("pt-BR"),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    settings: typings.Settings = fastapi_injector.Injected(typings.Settings),
):
    if audience not in {"educator", "admin"}:
        raise fastapi.HTTPException(status_code=400, detail="Invalid audience")

    async with uow_builder() as uow:
        tutorial = await uow.tutorial_repository.get_latest_by_audience(audience)
        if tutorial:
            if tutorial.source_type == "upload" and tutorial.file_path:
                bucket_name = (
                    tutorial.bucket_name
                    or settings.get("public_bucket_path")
                    or f"{settings.get('project_id')}-store-public-files"
                )
                public_storage = google.CloudStorage(
                    project_id=settings.get("project_id", ""),
                    storage_path=bucket_name,
                    creds_path=settings.get("gcp_storage_credentials", ""),
                )
                signed_download_url = await public_storage.generate_signed_url(
                    path=tutorial.file_path, mimetype="application/pdf", method="GET"
                )
                return {"url": signed_download_url}
            return {"url": tutorial.url}

        # Fallback to standard public GCS bucket url
        bucket_name = (
            settings.get("public_bucket_path")
            or f"{settings.get('project_id')}-store-public-files"
        )

        if audience == "educator":
            default_url = f"https://storage.googleapis.com/{bucket_name}/tutorial/tutorialprofessor_{locale}.pdf"
        else:
            default_url = f"https://storage.googleapis.com/{bucket_name}/tutorial/tutorialadministrador_{locale}.pdf"

        return {"url": default_url}
