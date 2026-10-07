from app.application.access_token.cryptographer import AccessTokenCryptographer
from app.application.access_token.entity_factory import AccessTokenFactory
from app.application.auth_identity.data_gateway import AuthIdentityDataGateway
from app.application.auth_identity.errors import (
    AuthError,
    InvalidCodeError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.application.common.dto import dto
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.oauth.protocol import OAuthClient, OAuthExchangeCodeError, OAuthLoadUserInfoError
from app.application.user.password_utils import PasswordVerifier
from app.domain.auth_identity.value_objects import AuthMethod
from app.domain.user.entity import UserId


@dto
class SignInResponse:
    user_id: UserId
    access_token: str


@interactor
class SignInInteractor:
    unit_of_work: UnitOfWork
    password_verifier: PasswordVerifier
    auth_identity_data_gateway: AuthIdentityDataGateway
    access_token_factory: AccessTokenFactory
    access_token_cryptographer: AccessTokenCryptographer
    yandex_oauth_client: OAuthClient

    async def sign_in_email(
        self,
        email: str,
        password: str,
    ) -> SignInResponse:
        normalized_email = email.strip().lower()

        auth_identity = await self.auth_identity_data_gateway.load_by_method_and_identifier(
            method=AuthMethod.EMAIL,
            identifier=normalized_email,
        )
        if not auth_identity:
            raise UserNotFoundError(identifier=normalized_email)

        if not auth_identity.secret_key:
            raise InvalidCredentialsError

        if not self.password_verifier.verify(password, auth_identity.secret_key):
            raise InvalidCredentialsError

        access_token = self.access_token_factory.execute(auth_identity.user_id)
        crypted_access_token = self.access_token_cryptographer.crypto(access_token.id)

        await self.unit_of_work.add(access_token)
        await self.unit_of_work.commit()

        return SignInResponse(user_id=auth_identity.user_id, access_token=crypted_access_token)

    async def sign_in_yandex(self, code: str) -> SignInResponse:
        try:
            token_response = await self.yandex_oauth_client.exchange_code(code)
            access_token_yandex = token_response.access_token
        except OAuthExchangeCodeError:
            raise InvalidCodeError from None

        try:
            user_info = await self.yandex_oauth_client.load_user_info(access_token_yandex)
        except OAuthLoadUserInfoError:
            raise AuthError from None

        auth_identity = await self.auth_identity_data_gateway.load_by_method_and_identifier(
            method=AuthMethod.YANDEX,
            identifier=user_info.user_id,
        )
        if not auth_identity:
            raise UserNotFoundError(identifier=user_info.user_id)

        access_token = self.access_token_factory.execute(auth_identity.user_id)
        crypted_access_token = self.access_token_cryptographer.crypto(access_token.id)

        await self.unit_of_work.add(access_token)
        await self.unit_of_work.commit()

        return SignInResponse(user_id=auth_identity.user_id, access_token=crypted_access_token)
