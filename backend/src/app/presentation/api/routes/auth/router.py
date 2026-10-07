from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from app.application.auth_identity.errors import (
    AuthError,
    InvalidCodeError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.application.auth_identity.interactors.sign_in import SignInInteractor
from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.presentation.api.routes.auth.dto import (
    AuthResponse,
    EmailSignInRequest,
    EmailSignUpRequest,
    YandexSignInRequest,
    YandexSignUpRequest,
)


@post(
    path="/registration/email",
    summary="Register with email",
)
async def sign_up_email(
    data: EmailSignUpRequest,
    interactor: FromDishka[SignUpInteractor],
) -> AuthResponse:
    try:
        result = await interactor.sign_up_email(email=data.email, password=data.password)
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return AuthResponse(user_id=str(result.user_id), access_token=result.access_token)


@post(
    path="/registration/yandex",
    summary="Register with Yandex",
)
async def sign_up_yandex(
    data: YandexSignUpRequest,
    interactor: FromDishka[SignUpInteractor],
) -> AuthResponse:
    try:
        result = await interactor.sign_up_yandex(code=data.code)
    except (InvalidCodeError, AuthError) as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from error

    return AuthResponse(user_id=str(result.user_id), access_token=result.access_token)


@post(
    path="/signing/email",
    summary="Sign in (email)",
)
async def sign_in_email(
    data: EmailSignInRequest,
    interactor: FromDishka[SignInInteractor],
) -> AuthResponse:
    try:
        result = await interactor.sign_in_email(email=data.email, password=data.password)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    return AuthResponse(user_id=str(result.user_id), access_token=result.access_token)


@post(
    path="/signing/yandex",
    summary="Sign in (Yandex)",
)
async def sign_in_yandex(
    data: YandexSignInRequest,
    interactor: FromDishka[SignInInteractor],
) -> AuthResponse:
    try:
        result = await interactor.sign_in_yandex(code=data.code)
    except InvalidCodeError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization code",
        ) from error
    except AuthError as error:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from error
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return AuthResponse(user_id=str(result.user_id), access_token=result.access_token)


router = DishkaRouter(
    path="/auth",
    route_handlers=[sign_up_email, sign_up_yandex, sign_in_email, sign_in_yandex],
    tags=["auth"],
)
