from typing import Any

from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import Request, get, patch, post, put
from litestar.exceptions import HTTPException
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.dating_profile.errors import (
    DatingProfileNotFoundError,
    DatingProfileValidationError,
    PhotoStorageUnavailableError,
    PhotoValidationError,
    ProfileRequiredError,
)
from app.application.dating_profile.interactors.get_dating_profile import (
    GetDatingProfileInteractor,
)
from app.application.dating_profile.interactors.set_trait_visibility import (
    SetTraitVisibilityInteractor,
)
from app.application.dating_profile.interactors.upload_dating_profile_photo import (
    MAX_PHOTO_SIZE_BYTES,
    UploadDatingProfilePhotoInteractor,
)
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.presentation.api.routes.dating_profile.dto import (
    DatingProfileResponse,
    SetTraitVisibilityRequest,
    TraitItemResponse,
    UploadDatingPhotoResponse,
    UpsertDatingProfileRequest,
)


@get(
    path="/me",
    summary="Get own dating profile",
    security=[{"BearerToken": []}],
)
async def get_dating_profile(
    interactor: FromDishka[GetDatingProfileInteractor],
) -> DatingProfileResponse:
    try:
        result = await interactor.execute()
    except UserUnauthorizedError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
    except DatingProfileNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Dating profile not found",
        ) from error
    p = result.dating_profile
    return DatingProfileResponse(
        user_id=p.user_id,
        photos=p.photos,
        traits=[
            TraitItemResponse(
                trait_code=t.trait_code,
                score=t.score,
                is_hidden=t.is_hidden,
            )
            for t in p.traits
        ],
    )


@put(
    path="/me",
    summary="Create or update own dating profile",
    security=[{"BearerToken": []}],
)
async def upsert_dating_profile(
    data: UpsertDatingProfileRequest,
    interactor: FromDishka[UpsertDatingProfileInteractor],
) -> DatingProfileResponse:
    try:
        result = await interactor.execute(photos=data.photos)
    except UserUnauthorizedError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
    except ProfileRequiredError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Profile required to create dating profile",
        ) from error
    except DatingProfileValidationError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="At least one photo required",
        ) from error
    p = result.dating_profile
    return DatingProfileResponse(
        user_id=p.user_id,
        photos=p.photos,
        traits=[
            TraitItemResponse(
                trait_code=t.trait_code,
                score=t.score,
                is_hidden=t.is_hidden,
            )
            for t in p.traits
        ],
    )


@patch(
    path="/me/traits/visibility",
    summary="Set trait visibility (hide/show)",
    security=[{"BearerToken": []}],
    status_code=204,
)
async def set_trait_visibility(
    data: SetTraitVisibilityRequest,
    interactor: FromDishka[SetTraitVisibilityInteractor],
) -> None:
    try:
        await interactor.execute(
            trait_code=data.trait_code,
            is_hidden=data.is_hidden,
        )
    except UserUnauthorizedError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
    except DatingProfileNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Dating profile or trait not found",
        ) from error


@post(
    path="/me/photos",
    summary="Upload dating profile photo",
    security=[{"BearerToken": []}],
)
async def upload_dating_profile_photo(
    request: Request[Any, Any, Any],
    interactor: FromDishka[UploadDatingProfilePhotoInteractor],
) -> UploadDatingPhotoResponse:
    content_type = request.headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()
    if not content_type:
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type is required",
        )

    photo_bytes = await request.body()
    try:
        result = await interactor.execute(
            content=photo_bytes,
            content_type=content_type,
        )
    except UserUnauthorizedError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
    except ProfileRequiredError as error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Profile required to upload dating photo",
        ) from error
    except PhotoValidationError as error:
        status_code = (
            HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if len(photo_bytes) > MAX_PHOTO_SIZE_BYTES
            else HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        raise HTTPException(
            status_code=status_code,
            detail="Invalid photo payload",
        ) from error
    except PhotoStorageUnavailableError as error:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Photo upload unavailable",
        ) from error
    return UploadDatingPhotoResponse(photo_url=result.photo_url)


router = DishkaRouter(
    path="/dating-profile",
    route_handlers=[
        get_dating_profile,
        upsert_dating_profile,
        upload_dating_profile_photo,
        set_trait_visibility,
    ],
    tags=["dating-profile"],
)
