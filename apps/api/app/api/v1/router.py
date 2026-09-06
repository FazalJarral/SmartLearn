import hashlib
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, File, Header, Response, UploadFile

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models.state import ProcessingStage
from app.schemas.api import (
    DocumentListItem,
    DocumentStatusResponse,
    GuestSessionResponse,
    LearningPackageResponse,
    QuizAnswerIn,
    QuizAnswerResult,
    QuizAttemptResponse,
    SignedUrlResponse,
    UsageResponse,
)
from app.services.deepseek_generation import GenerationInput, get_generator
from app.services.mock_generation import mock_study_package
from app.services.pdf_extraction import extract_text_from_pdf
from app.services.pdf_validation import validate_pdf_upload
from app.services.quota import next_utc_midnight, remaining_uploads
from app.services.scoring import is_correct_answer
from app.services.supabase_client import Actor, SupabaseService

router = APIRouter()

_DEMO_DOCUMENT_ID = uuid4()
_DEMO_PACKAGE_ID = uuid4()


def _owns_document(document: dict, actor: Actor) -> bool:
    return document["owner_user_id"] == actor.user_id and document["guest_session_id"] == actor.guest_session_id


def _progress_for_status(status: str) -> int:
    progress_by_status = {
        ProcessingStage.UPLOADED.value: 10,
        ProcessingStage.VALIDATING.value: 20,
        ProcessingStage.EXTRACTING.value: 30,
        ProcessingStage.GENERATING_CONTENT.value: 45,
        ProcessingStage.CONTENT_READY.value: 80,
        ProcessingStage.GENERATING_AUDIO.value: 85,
        ProcessingStage.RENDERING_VIDEO.value: 90,
        ProcessingStage.PARTIAL_SUCCESS.value: 90,
        ProcessingStage.COMPLETED.value: 100,
        ProcessingStage.FAILED.value: 100,
        ProcessingStage.DELETED.value: 100,
    }
    return progress_by_status.get(status, 0)


async def _authorized_document(service: SupabaseService, actor: Actor, document_id: UUID) -> dict:
    rows = await service.select("documents", {"select": "*", "id": f"eq.{document_id}", "limit": "1"})
    if not rows or not _owns_document(rows[0], actor):
        raise ApiError("document_not_found", "Document not found.", 404)
    return rows[0]


async def _authorized_package(service: SupabaseService, actor: Actor, package_id: UUID) -> tuple[dict, dict]:
    package_rows = await service.select(
        "learning_packages",
        {"select": "*", "id": f"eq.{package_id}", "limit": "1"},
    )
    if not package_rows:
        raise ApiError("package_not_found", "Learning package not found.", 404)
    package = package_rows[0]
    document = await _authorized_document(service, actor, UUID(package["document_id"]))
    return package, document


async def _authorized_attempt(service: SupabaseService, actor: Actor, attempt_id: UUID) -> dict:
    rows = await service.select("quiz_attempts", {"select": "*", "id": f"eq.{attempt_id}", "limit": "1"})
    if not rows:
        raise ApiError("quiz_attempt_not_found", "Quiz attempt not found.", 404)
    attempt = rows[0]
    if attempt["owner_user_id"] != actor.user_id or attempt["guest_session_id"] != actor.guest_session_id:
        raise ApiError("quiz_attempt_not_found", "Quiz attempt not found.", 404)
    return attempt


async def _authorized_video_asset(service: SupabaseService, actor: Actor, video_asset_id: UUID) -> dict:
    rows = await service.select(
        "video_assets",
        {"select": "*", "id": f"eq.{video_asset_id}", "limit": "1"},
    )
    if not rows:
        raise ApiError("video_asset_not_found", "Video asset not found.", 404)
    video_asset = rows[0]
    await _authorized_package(service, actor, UUID(video_asset["package_id"]))
    return video_asset


async def _quiz_score(service: SupabaseService, attempt_id: str, package_id: str) -> tuple[int, int]:
    correct_rows = await service.select(
        "quiz_answers",
        {"select": "id", "attempt_id": f"eq.{attempt_id}", "is_correct": "eq.true"},
    )
    question_rows = await service.select("quiz_questions", {"select": "id", "package_id": f"eq.{package_id}"})
    return len(correct_rows), len(question_rows)


async def _persist_study_package(
    service: SupabaseService,
    document_id: str,
    content: dict,
    generation_provider: str,
) -> dict:
    existing_packages = await service.select(
        "learning_packages",
        {"select": "id", "document_id": f"eq.{document_id}", "limit": "1"},
    )
    for existing in existing_packages:
        await service.delete("learning_packages", existing["id"])
    package = (
        await service.insert(
            "learning_packages",
            {
                "document_id": document_id,
                "title": content["title"],
                "overview": content["summary"]["overview"],
                "key_points": content["summary"]["key_points"],
                "schema_version": content["schema_version"],
                "model_version": generation_provider,
                "prompt_version": "deepseek-json-v1"
                if generation_provider.lower() == "deepseek"
                else "mock-v1",
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
    )[0]
    await service.insert(
        "flashcards",
        [
            {"package_id": package["id"], "position": index, **card}
            for index, card in enumerate(content["flashcards"], start=1)
        ],
    )
    await service.insert(
        "quiz_questions",
        [
            {
                "package_id": package["id"],
                "position": index,
                "question": question["question"],
                "options": question["options"],
                "correct_index": question["correct_option_index"],
                "explanation": question["explanation"],
                "source_pages": question["source_pages"],
            }
            for index, question in enumerate(content["quiz"], start=1)
        ],
    )
    await service.insert(
        "video_assets",
        {
            "package_id": package["id"],
            "status": ProcessingStage.CONTENT_READY.value,
            "plan_title": content["video"]["title"],
            "narration": content["video"]["narration"],
            "scenes": content["video"]["scenes"],
            "narration_available": False,
            "user_message": "Video rendering is queued.",
        },
    )
    await service.upsert(
        "processing_jobs",
        {
            "document_id": document_id,
            "stage": ProcessingStage.RENDERING_VIDEO.value,
            "progress": 70,
        },
        "document_id,stage",
    )
    return package


def _source_storage_path(actor: Actor, document_id: UUID, filename: str) -> str:
    actor_kind = "users" if actor.user_id else "guests"
    actor_id = actor.user_id or actor.guest_session_id
    safe_suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    return f"{actor_kind}/{actor_id}/documents/{document_id}/source.{safe_suffix}"


async def _generate_and_persist_document(
    document_id: str,
    filename: str,
    processed_page_count: int,
    page_aware_text: str,
    generation_job_id: str,
) -> None:
    settings = get_settings()
    service = SupabaseService(settings)
    generator = get_generator(settings)
    try:
        await service.update(
            "processing_jobs",
            generation_job_id,
            {
                "stage": ProcessingStage.GENERATING_CONTENT.value,
                "progress": 55,
                "user_message": "Generating study material from the PDF.",
            },
        )
        study_package = await generator.generate(
            GenerationInput(
                filename=filename,
                page_count=processed_page_count,
                page_aware_text=page_aware_text,
            )
        )
        await service.update(
            "processing_jobs",
            generation_job_id,
            {
                "stage": ProcessingStage.GENERATING_CONTENT.value,
                "progress": 65,
                "user_message": "Saving generated study material.",
            },
        )
        await _persist_study_package(
            service,
            document_id,
            study_package.model_dump(exclude_none=True),
            settings.generation_provider,
        )
        await service.update("documents", document_id, {"status": ProcessingStage.CONTENT_READY.value})
        await service.update(
            "processing_jobs",
            generation_job_id,
            {
                "stage": ProcessingStage.CONTENT_READY.value,
                "progress": 80,
                "error_code": None,
                "user_message": "Study material is ready. Video rendering is queued.",
                "diagnostic_detail": None,
            },
        )
    except ApiError as exc:
        await service.update("documents", document_id, {"status": ProcessingStage.FAILED.value})
        await service.update(
            "processing_jobs",
            generation_job_id,
            {
                "stage": ProcessingStage.FAILED.value,
                "progress": 100,
                "error_code": exc.code,
                "user_message": exc.message,
                "diagnostic_detail": "content generation failed after upload acceptance",
            },
        )
    except Exception:
        await service.update("documents", document_id, {"status": ProcessingStage.FAILED.value})
        await service.update(
            "processing_jobs",
            generation_job_id,
            {
                "stage": ProcessingStage.FAILED.value,
                "progress": 100,
                "error_code": "generation_failed",
                "user_message": "Study-material generation failed. Try again.",
                "diagnostic_detail": "unexpected content generation failure after upload acceptance",
            },
        )


@router.post("/guest/session", response_model=GuestSessionResponse, tags=["guest"])
async def create_guest_session() -> GuestSessionResponse:
    settings = get_settings()
    guest = await SupabaseService(settings).create_guest_session()
    return GuestSessionResponse(
        guest_session_id=guest.token,
        expires_at=guest.expires_at,
    )


@router.get("/me/usage", response_model=UsageResponse, tags=["usage"])
async def usage(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> UsageResponse:
    settings = get_settings()
    actor_type = "guest"
    accepted_today = 0
    limit = settings.guest_daily_upload_limit
    if authorization or x_guest_session:
        service = SupabaseService(settings)
        actor = await service.actor_from_headers(authorization, x_guest_session)
        actor_type = actor.actor_type
        limit = (
            settings.registered_daily_upload_limit
            if actor.actor_type == "registered"
            else settings.guest_daily_upload_limit
        )
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        usage_params = {
            "select": "id",
            "accepted": "eq.true",
            "occurred_at": f"gte.{day_start.isoformat()}",
        }
        if actor.user_id:
            usage_params["owner_user_id"] = f"eq.{actor.user_id}"
        else:
            usage_params["guest_session_id"] = f"eq.{actor.guest_session_id}"
        accepted_today = len(await service.select("usage_events", usage_params))
    return UsageResponse(
        actor_type=actor_type,
        accepted_today=accepted_today,
        daily_limit=limit,
        remaining=remaining_uploads(accepted_today, limit),
        resets_at_utc=next_utc_midnight(),
    )


@router.get("/documents", response_model=list[DocumentListItem], tags=["documents"])
async def list_documents(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> list[DocumentListItem]:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    params = {
        "select": "id,original_filename,status,created_at,deleted_at",
        "deleted_at": "is.null",
        "order": "created_at.desc",
    }
    if actor.user_id:
        params["owner_user_id"] = f"eq.{actor.user_id}"
    else:
        params["guest_session_id"] = f"eq.{actor.guest_session_id}"
    documents = await service.select("documents", params)
    if not documents:
        return []
    document_ids = ",".join(document["id"] for document in documents)
    package_rows = await service.select(
        "learning_packages",
        {"select": "id,document_id,title", "document_id": f"in.({document_ids})"},
    )
    packages_by_document_id = {row["document_id"]: row for row in package_rows}
    return [
        DocumentListItem(
            id=document["id"],
            original_filename=document["original_filename"],
            stage=ProcessingStage(document["status"]),
            progress=_progress_for_status(document["status"]),
            created_at=document["created_at"],
            deleted_at=document["deleted_at"],
            package_id=packages_by_document_id.get(document["id"], {}).get("id"),
            title=packages_by_document_id.get(document["id"], {}).get("title"),
        )
        for document in documents
    ]


@router.post("/documents", response_model=DocumentStatusResponse, tags=["documents"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> DocumentStatusResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    data = await file.read(settings.max_upload_bytes + 1)
    validation = validate_pdf_upload(
        file.filename or "upload.pdf",
        file.content_type,
        data,
        settings.max_upload_bytes,
    )
    extracted = extract_text_from_pdf(data, settings.max_pdf_pages, settings.max_extracted_chars)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    limit = (
        settings.registered_daily_upload_limit
        if actor.actor_type == "registered"
        else settings.guest_daily_upload_limit
    )
    quota_rows = await service.rpc(
        "accept_upload_event",
        {
            "actor_user_id": actor.user_id,
            "actor_guest_session_id": actor.guest_session_id,
            "upload_idempotency_key": idempotency_key,
            "daily_limit": limit,
            "event_reason": "accepted_after_validation",
        },
    )
    if not quota_rows or not quota_rows[0]["accepted"]:
        raise ApiError("upload_quota_exceeded", "You have reached today's upload limit.", 429)

    if actor.user_id:
        await service.upsert("profiles", {"id": actor.user_id}, "id")

    document_id = uuid4()
    source_storage_path = _source_storage_path(actor, document_id, validation.filename)
    document_payload = {
        "id": str(document_id),
        "owner_user_id": actor.user_id,
        "guest_session_id": actor.guest_session_id,
        "original_filename": validation.filename,
        "source_storage_path": source_storage_path,
        "size_bytes": validation.size_bytes,
        "page_count": extracted.page_count,
        "checksum_sha256": hashlib.sha256(data).hexdigest(),
        "status": ProcessingStage.GENERATING_CONTENT.value,
    }
    await service.storage_upload(source_storage_path, data, "application/pdf")
    document = (await service.insert("documents", document_payload))[0]
    generation_job = (
        await service.insert(
            "processing_jobs",
            {
                "document_id": document["id"],
                "stage": ProcessingStage.GENERATING_CONTENT.value,
                "progress": 40,
            },
        )
    )[0]

    background_tasks.add_task(
        _generate_and_persist_document,
        document["id"],
        validation.filename,
        extracted.processed_page_count,
        extracted.combined_text,
        generation_job["id"],
    )
    return DocumentStatusResponse(
        document_id=document["id"],
        stage=ProcessingStage.GENERATING_CONTENT,
        progress=45,
        message="Document accepted. SmartLearn is generating your study material.",
        warnings=[extracted.truncation_message] if extracted.truncation_message else [],
        package_id=None,
    )


@router.get("/documents/{document_id}", response_model=DocumentListItem, tags=["documents"])
async def document_detail(
    document_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> DocumentListItem:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    document = await _authorized_document(service, actor, document_id)
    package_rows = await service.select(
        "learning_packages",
        {"select": "id,title", "document_id": f"eq.{document_id}", "limit": "1"},
    )
    package = package_rows[0] if package_rows else {}
    return DocumentListItem(
        id=document["id"],
        original_filename=document["original_filename"],
        stage=ProcessingStage(document["status"]),
        progress=_progress_for_status(document["status"]),
        created_at=document["created_at"],
        deleted_at=document["deleted_at"],
        package_id=package.get("id"),
        title=package.get("title"),
    )


@router.delete("/documents/{document_id}", status_code=204, tags=["documents"])
async def delete_document(
    document_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> Response:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    document = await _authorized_document(service, actor, document_id)
    storage_paths = [document["source_storage_path"]] if document.get("source_storage_path") else []
    package_rows = await service.select(
        "learning_packages",
        {"select": "id", "document_id": f"eq.{document_id}", "limit": "1"},
    )
    if package_rows:
        video_rows = await service.select(
            "video_assets",
            {
                "select": "video_storage_path,transcript_storage_path",
                "package_id": f"eq.{package_rows[0]['id']}",
                "limit": "1",
            },
        )
        if video_rows:
            storage_paths.extend(
                path
                for path in [
                    video_rows[0].get("video_storage_path"),
                    video_rows[0].get("transcript_storage_path"),
                ]
                if path
            )
    await service.storage_delete(storage_paths)
    await service.delete("documents", str(document_id))
    return Response(status_code=204)


@router.post("/documents/{document_id}/retry", response_model=DocumentStatusResponse, tags=["documents"])
async def retry_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> DocumentStatusResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    document = await _authorized_document(service, actor, document_id)
    if document["status"] == ProcessingStage.CONTENT_READY.value:
        package_rows = await service.select(
            "learning_packages",
            {"select": "id", "document_id": f"eq.{document_id}", "limit": "1"},
        )
        return DocumentStatusResponse(
            document_id=document_id,
            stage=ProcessingStage.CONTENT_READY,
            progress=_progress_for_status(ProcessingStage.CONTENT_READY.value),
            message="Document is already ready.",
            package_id=package_rows[0]["id"] if package_rows else None,
        )
    if document["status"] not in {ProcessingStage.FAILED.value, ProcessingStage.PARTIAL_SUCCESS.value}:
        raise ApiError("retry_not_available", "Retry is only available after a failed stage.", 409)
    if not document.get("source_storage_path"):
        raise ApiError("source_pdf_unavailable", "The source PDF is not available for retry.", 409)

    data = await service.storage_download(document["source_storage_path"])
    extracted = extract_text_from_pdf(data, settings.max_pdf_pages, settings.max_extracted_chars)
    await service.update("documents", str(document_id), {"status": ProcessingStage.GENERATING_CONTENT.value})
    generation_job = (
        await service.upsert(
            "processing_jobs",
            {
                "document_id": str(document_id),
                "stage": ProcessingStage.GENERATING_CONTENT.value,
                "progress": 45,
                "attempts": 1,
                "error_code": None,
                "user_message": None,
                "diagnostic_detail": None,
            },
            "document_id,stage",
        )
    )[0]

    background_tasks.add_task(
        _generate_and_persist_document,
        str(document_id),
        document["original_filename"],
        extracted.processed_page_count,
        extracted.combined_text,
        generation_job["id"],
    )
    return DocumentStatusResponse(
        document_id=document_id,
        stage=ProcessingStage.GENERATING_CONTENT,
        progress=_progress_for_status(ProcessingStage.GENERATING_CONTENT.value),
        message="Retry started. SmartLearn is regenerating your study material.",
        package_id=None,
    )


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse, tags=["documents"])
async def document_status(
    document_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> DocumentStatusResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    document = await _authorized_document(service, actor, document_id)
    package_rows = await service.select(
        "learning_packages",
        {"select": "id", "document_id": f"eq.{document_id}", "limit": "1"},
    )
    job_rows = await service.select(
        "processing_jobs",
        {
            "select": "progress,user_message,error_code",
            "document_id": f"eq.{document_id}",
            "order": "updated_at.desc",
            "limit": "1",
        },
    )
    job = job_rows[0] if job_rows else {}
    return DocumentStatusResponse(
        document_id=document_id,
        stage=ProcessingStage(document["status"]),
        progress=job.get("progress") or _progress_for_status(document["status"]),
        message=job.get("user_message") or "Status loaded from Supabase.",
        error_code=job.get("error_code"),
        package_id=package_rows[0]["id"] if package_rows else None,
    )


@router.get("/learning-packages/{package_id}", response_model=LearningPackageResponse, tags=["learning"])
async def learning_package(
    package_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> LearningPackageResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    package, _document = await _authorized_package(service, actor, package_id)

    flashcards = await service.select(
        "flashcards",
        {"select": "id,front,back,source_pages", "package_id": f"eq.{package_id}", "order": "position.asc"},
    )
    quiz_rows = await service.select(
        "quiz_questions",
        {
            "select": "id,question,options,correct_index,explanation,source_pages",
            "package_id": f"eq.{package_id}",
            "order": "position.asc",
        },
    )
    video_rows = await service.select(
        "video_assets",
        {
            "select": "id,status,user_message,narration_available,plan_title,narration,scenes",
            "package_id": f"eq.{package_id}",
            "limit": "1",
        },
    )
    content = mock_study_package(package["title"]).model_dump()
    content["summary"]["overview"] = package["overview"]
    content["summary"]["key_points"] = package["key_points"]
    content["flashcards"] = flashcards
    content["quiz"] = [
        {
            "id": row["id"],
            "question": row["question"],
            "options": row["options"],
            "correct_option_index": row["correct_index"],
            "explanation": row["explanation"],
            "source_pages": row["source_pages"],
        }
        for row in quiz_rows
    ]
    if video_rows:
        video = video_rows[0]
        if video.get("plan_title"):
            content["video"]["title"] = video["plan_title"]
        if video.get("narration"):
            content["video"]["narration"] = video["narration"]
        if video.get("scenes"):
            content["video"]["scenes"] = video["scenes"]
    return LearningPackageResponse(
        id=package_id,
        document_id=package["document_id"],
        content=content,
        video_asset_id=video_rows[0]["id"] if video_rows else None,
    )


@router.get(
    "/video-assets/{video_asset_id}/playback-url",
    response_model=SignedUrlResponse,
    tags=["learning"],
)
async def video_playback_url(
    video_asset_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> SignedUrlResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    video_asset = await _authorized_video_asset(service, actor, video_asset_id)
    if not video_asset.get("video_storage_path"):
        raise ApiError("video_not_available", "The rendered video is not available yet.", 404)
    expires_in = 300
    return SignedUrlResponse(
        url=await service.storage_signed_url(video_asset["video_storage_path"], expires_in=expires_in),
        expires_in=expires_in,
    )


@router.get(
    "/video-assets/{video_asset_id}/download-url",
    response_model=SignedUrlResponse,
    tags=["learning"],
)
async def video_download_url(
    video_asset_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> SignedUrlResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    video_asset = await _authorized_video_asset(service, actor, video_asset_id)
    if not video_asset.get("video_storage_path"):
        raise ApiError("video_not_available", "The rendered video is not available yet.", 404)
    expires_in = 300
    return SignedUrlResponse(
        url=await service.storage_signed_url(
            video_asset["video_storage_path"], expires_in=expires_in, download=True
        ),
        expires_in=expires_in,
    )


@router.get(
    "/video-assets/{video_asset_id}/transcript-url",
    response_model=SignedUrlResponse,
    tags=["learning"],
)
async def video_transcript_url(
    video_asset_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> SignedUrlResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    video_asset = await _authorized_video_asset(service, actor, video_asset_id)
    if not video_asset.get("transcript_storage_path"):
        raise ApiError("transcript_not_available", "The video transcript is not available yet.", 404)
    expires_in = 300
    return SignedUrlResponse(
        url=await service.storage_signed_url(
            video_asset["transcript_storage_path"], expires_in=expires_in, download=True
        ),
        expires_in=expires_in,
    )


@router.post(
    "/learning-packages/{package_id}/quiz-attempts",
    response_model=QuizAttemptResponse,
    tags=["learning"],
)
async def create_quiz_attempt(
    package_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> QuizAttemptResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    await _authorized_package(service, actor, package_id)
    question_rows = await service.select("quiz_questions", {"select": "id", "package_id": f"eq.{package_id}"})
    attempt = (
        await service.insert(
            "quiz_attempts",
            {
                "package_id": str(package_id),
                "owner_user_id": actor.user_id,
                "guest_session_id": actor.guest_session_id,
                "score": 0,
                "total": len(question_rows),
            },
        )
    )[0]
    return QuizAttemptResponse(**attempt)


@router.patch(
    "/quiz-attempts/{attempt_id}/answers",
    response_model=QuizAnswerResult,
    tags=["learning"],
)
async def answer_quiz_question(
    attempt_id: UUID,
    answer: QuizAnswerIn,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> QuizAnswerResult:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    attempt = await _authorized_attempt(service, actor, attempt_id)
    question_rows = await service.select(
        "quiz_questions",
        {
            "select": "id,package_id,correct_index,explanation",
            "id": f"eq.{answer.question_id}",
            "limit": "1",
        },
    )
    if not question_rows or question_rows[0]["package_id"] != attempt["package_id"]:
        raise ApiError("quiz_question_not_found", "Quiz question not found.", 404)
    question = question_rows[0]
    correct = is_correct_answer(answer.selected_index, question["correct_index"])
    await service.upsert(
        "quiz_answers",
        {
            "attempt_id": str(attempt_id),
            "question_id": str(answer.question_id),
            "selected_index": answer.selected_index,
            "is_correct": correct,
            "answered_at": datetime.now(UTC).isoformat(),
        },
        "attempt_id,question_id",
    )
    score, total = await _quiz_score(service, str(attempt_id), attempt["package_id"])
    await service.update("quiz_attempts", str(attempt_id), {"score": score, "total": total})
    return QuizAnswerResult(
        attempt_id=attempt_id,
        question_id=answer.question_id,
        selected_index=answer.selected_index,
        correct_index=question["correct_index"],
        is_correct=correct,
        explanation=question["explanation"],
        score=score,
        total=total,
    )


@router.post(
    "/quiz-attempts/{attempt_id}/complete",
    response_model=QuizAttemptResponse,
    tags=["learning"],
)
async def complete_quiz_attempt(
    attempt_id: UUID,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_guest_session: Annotated[str | None, Header(alias="X-Guest-Session")] = None,
) -> QuizAttemptResponse:
    settings = get_settings()
    service = SupabaseService(settings)
    actor = await service.actor_from_headers(authorization, x_guest_session)
    attempt = await _authorized_attempt(service, actor, attempt_id)
    score, total = await _quiz_score(service, str(attempt_id), attempt["package_id"])
    updated = (
        await service.update(
            "quiz_attempts",
            str(attempt_id),
            {"score": score, "total": total, "completed_at": datetime.now(UTC).isoformat()},
        )
    )[0]
    return QuizAttemptResponse(**updated)
