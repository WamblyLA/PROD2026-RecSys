from app.application.access_token.cryptographer import AccessTokenCryptographer
from app.application.access_token.entity_factory import AccessTokenFactory
from app.application.auth_identity.data_gateway import AuthIdentityDataGateway
from app.application.auth_identity.errors import AuthError, InvalidCodeError, UserAlreadyExistsError
from app.application.common.dto import dto
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.oauth.protocol import OAuthClient, OAuthExchangeCodeError, OAuthLoadUserInfoError
from app.application.user.password_utils import PasswordHasher
from app.domain.auth_identity.entity import AuthIdentity
from app.domain.auth_identity.value_objects import AuthMethod
from app.domain.user.entity import User, UserId


@dto
class SignUpResponse:
    user_id: UserId
    access_token: str


@interactor
class SignUpInteractor:
    unit_of_work: UnitOfWork
    password_hasher: PasswordHasher
    auth_identity_data_gateway: AuthIdentityDataGateway
    access_token_factory: AccessTokenFactory
    access_token_cryptographer: AccessTokenCryptographer
    yandex_oauth_client: OAuthClient

    async def sign_up_email(
        self,
        email: str,
        password: str,
    ) -> SignUpResponse:
        normalized_email = email.strip().lower()

        existing = await self.auth_identity_data_gateway.load_by_method_and_identifier(
            method=AuthMethod.EMAIL,
            identifier=normalized_email,
        )
        if existing:
            raise UserAlreadyExistsError(identifier=normalized_email, auth_method=AuthMethod.EMAIL)

        user = User.factory()
        auth_identity = AuthIdentity.factory(
            user_id=user.id,
            method=AuthMethod.EMAIL,
            identifier=normalized_email,
            secret_key=self.password_hasher.hash(password),
        )
        access_token = self.access_token_factory.execute(user.id)
        crypted_access_token = self.access_token_cryptographer.crypto(access_token.id)

        for entity in (user, auth_identity, access_token):
            await self.unit_of_work.add(entity)
        await self.unit_of_work.commit()

        return SignUpResponse(user_id=user.id, access_token=crypted_access_token)

    async def sign_up_yandex(self, code: str) -> SignUpResponse:
        try:
            token_response = await self.yandex_oauth_client.exchange_code(code)
            access_token_yandex = token_response.access_token
        except OAuthExchangeCodeError:
            raise InvalidCodeError from None

        try:
            user_info = await self.yandex_oauth_client.load_user_info(access_token_yandex)
        except OAuthLoadUserInfoError:
            raise AuthError from None

        existing = await self.auth_identity_data_gateway.load_by_method_and_identifier(
            method=AuthMethod.YANDEX,
            identifier=user_info.user_id,
        )
        if existing:
            user_id = existing.user_id
        else:
            user = User.factory()
            user_id = user.id
            auth_identity = AuthIdentity.factory(
                user_id=user_id,
                method=AuthMethod.YANDEX,
                identifier=user_info.user_id,
                secret_key=None,
            )
            await self.unit_of_work.add(user)
            await self.unit_of_work.add(auth_identity)

        access_token = self.access_token_factory.execute(user_id)
        crypted_access_token = self.access_token_cryptographer.crypto(access_token.id)

        await self.unit_of_work.add(access_token)
        await self.unit_of_work.commit()

        return SignUpResponse(user_id=user_id, access_token=crypted_access_token)
