from __future__ import annotations

import argparse
import csv
import logging
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote_plus
from uuid import UUID, uuid4, uuid5

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from app.domain.auth_identity.value_objects import AuthMethod
from app.domain.targeting.value_objects import TargetGender
from app.domain.user.value_objects import Gender
from app.infra.config.loaders import EnvAccessTokenConfigLoader, EnvPostgresConfigLoader
from app.infra.config.sources import EnvSource
from app.infra.persistence.sqla.tables import (
    auth_identity_table,
    dating_profile_photo_table,
    dating_profile_table,
    profile_table,
    targeting_table,
    user_table,
)
from app.infra.security.password_utils import FernetPasswordService

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

CHECKPOINTS = (1_000, 5_000, 10_000, 50_000, 100_000)
BATCH_SIZE = 1_000
MAX_USERS_TO_LOAD = 1_000_000
logger = logging.getLogger(__name__)
DEFAULT_REGION = "Moscow"
DEFAULT_PROFILE_PHOTO_URL = "https://i.pinimg.com/736x/66/20/9e/66209e958f35bea74dc48b0e3c79595f.jpg"
DEFAULT_PASSWORD = "password"  # noqa: S105
EMAIL_DOMAIN = "example.com"
AUTH_IDENTITY_NAMESPACE = UUID("f80fbbf2-efc6-4a09-866f-8367f8f51352")


def _name_to_email_local(first_name: str, last_name: str | None) -> str:
    """Build email local part from name, e.g. 'Nick', 'Fury' -> 'nick_fury'."""
    parts = [first_name]
    if last_name:
        parts.append(last_name)
    raw = "_".join(parts).lower()
    sanitized = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    return sanitized or "user"


def _build_postgres_url() -> str:
    loader = EnvPostgresConfigLoader(EnvSource())
    config = loader.load()
    password = quote_plus(config.password)
    return f"postgresql+psycopg://{config.user}:{password}@{config.host}:{config.port}/{config.db}"


def _build_engine() -> Engine:
    return create_engine(_build_postgres_url(), pool_pre_ping=True)


def _build_password_hasher() -> FernetPasswordService:
    config = EnvAccessTokenConfigLoader(EnvSource()).load()
    return FernetPasswordService(Fernet(config.crypto_key.encode("utf-8")))


def _build_faker_for_user(user_id: UUID) -> Faker:
    fake = Faker()
    fake.seed_instance(user_id.int)
    return fake


def _calculate_age(birth_date: date) -> int:
    today = datetime.now(tz=UTC).date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _build_fake_profile_fields(user_id: UUID) -> tuple[str, str, date, Gender]:
    fake = _build_faker_for_user(user_id)
    first_name = fake.first_name()
    last_name = fake.last_name()
    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=45)
    gender = Gender.MALE if user_id.int % 2 == 0 else Gender.FEMALE
    return first_name, last_name, birth_date, gender


def _extract_uuid(raw_row: dict[str, str]) -> UUID | None:
    raw_value = (raw_row.get("uuid") or raw_row.get("user_id") or raw_row.get("id") or "").strip()
    if not raw_value:
        return None
    try:
        return UUID(raw_value)
    except ValueError:
        return None


def _iter_user_ids(csv_path: Path) -> Iterator[UUID]:
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            user_id = _extract_uuid(raw_row)
            if user_id is None:
                continue
            yield user_id


def _insert_users_batch(engine: Engine, user_ids: list[UUID]) -> int:
    if not user_ids:
        return 0
    now = datetime.now(tz=UTC)
    rows = [{"id": user_id, "created_at": now} for user_id in user_ids]
    stmt = (
        insert(user_table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[user_table.c.id])
        .returning(user_table.c.id)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def _insert_profiles_batch(engine: Engine, user_ids: list[UUID]) -> int:
    if not user_ids:
        return 0
    now = datetime.now(tz=UTC)
    rows: list[dict[str, object]] = []
    for user_id in user_ids:
        first_name, last_name, birth_date, gender = _build_fake_profile_fields(user_id)
        rows.append(
            {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "birth_date": birth_date,
                "gender": gender,
                "region": DEFAULT_REGION,
                "avatar_url": None,
                "created_at": now,
                "updated_at": now,
            },
        )
    stmt = (
        insert(profile_table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[profile_table.c.user_id])
        .returning(profile_table.c.user_id)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def _insert_dating_profiles_batch(engine: Engine, user_ids: list[UUID]) -> list[tuple[UUID, UUID]]:
    if not user_ids:
        return []
    now = datetime.now(tz=UTC)
    rows = [{"id": uuid4(), "user_id": user_id, "created_at": now} for user_id in user_ids]
    stmt = (
        insert(dating_profile_table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[dating_profile_table.c.user_id])
        .returning(dating_profile_table.c.user_id, dating_profile_table.c.id)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        inserted_rows = result.fetchall()
    return [
        (UUID(str(inserted_user_id)), UUID(str(inserted_profile_id)))
        for inserted_user_id, inserted_profile_id in inserted_rows
    ]


def _insert_dating_photos_batch(engine: Engine, inserted_profiles: list[tuple[UUID, UUID]]) -> int:
    if not inserted_profiles:
        return 0
    rows = [
        {
            "id": uuid4(),
            "dating_profile_id": dating_profile_id,
            "url": DEFAULT_PROFILE_PHOTO_URL,
            "position": 0,
        }
        for _, dating_profile_id in inserted_profiles
    ]
    stmt = insert(dating_profile_photo_table).values(rows).returning(dating_profile_photo_table.c.id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def _build_auth_identity_payload(user_id: UUID, password_hasher: FernetPasswordService) -> dict[str, object]:
    first_name, last_name, _, _ = _build_fake_profile_fields(user_id)
    local_part = _name_to_email_local(first_name, last_name)
    identifier = f"{local_part}@{EMAIL_DOMAIN}"
    return {
        "id": uuid5(AUTH_IDENTITY_NAMESPACE, f"email:{user_id}"),
        "user_id": user_id,
        "method": AuthMethod.EMAIL,
        "identifier": identifier,
        "secret_key": password_hasher.hash(DEFAULT_PASSWORD),
        "created_at": datetime.now(tz=UTC),
    }


def _insert_targeting_batch(engine: Engine, user_ids: list[UUID]) -> int:
    if not user_ids:
        return 0
    now = datetime.now(tz=UTC)
    rows: list[dict[str, object]] = []
    for user_id in user_ids:
        _, _, birth_date, _ = _build_fake_profile_fields(user_id)
        age = _calculate_age(birth_date)
        rows.append(
            {
                "user_id": user_id,
                "region": DEFAULT_REGION,
                "gender_target": TargetGender.BOTH,
                "age_from": max(0, age - 2),
                "age_to": age + 2,
                "created_at": now,
                "updated_at": now,
            },
        )
    stmt = (
        insert(targeting_table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[targeting_table.c.user_id])
        .returning(targeting_table.c.user_id)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def _insert_auth_identities_batch(
    engine: Engine,
    user_ids: list[UUID],
    password_hasher: FernetPasswordService,
) -> int:
    if not user_ids:
        return 0
    rows = [_build_auth_identity_payload(user_id, password_hasher) for user_id in user_ids]
    stmt = (
        insert(auth_identity_table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[auth_identity_table.c.id])
        .returning(auth_identity_table.c.id)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def _log_checkpoint(processed_total: int, inserted_total: int, skipped_total: int, next_checkpoint: int) -> None:
    logger.info(
        "checkpoint_reached checkpoint=%s processed=%s inserted=%s skipped=%s",
        next_checkpoint,
        processed_total,
        inserted_total,
        skipped_total,
    )


def run(*, input_path: Path) -> None:
    if not input_path.exists():
        msg = f"Input file does not exist: {input_path}"
        raise FileNotFoundError(msg)

    engine = _build_engine()
    password_hasher = _build_password_hasher()
    processed_total = 0
    inserted_users_total = 0
    inserted_profiles_total = 0
    inserted_dating_profiles_total = 0
    inserted_dating_photos_total = 0
    inserted_auth_identities_total = 0
    inserted_targeting_total = 0
    skipped_users_total = 0
    checkpoint_idx = 0
    batch: list[UUID] = []

    for user_id in _iter_user_ids(input_path):
        processed_total += 1
        batch.append(user_id)

        if len(batch) >= BATCH_SIZE:
            inserted_users_total += _insert_users_batch(engine, batch)
            inserted_profiles_total += _insert_profiles_batch(engine, batch)
            inserted_dating_profiles = _insert_dating_profiles_batch(engine, batch)
            inserted_dating_profiles_total += len(inserted_dating_profiles)
            inserted_dating_photos_total += _insert_dating_photos_batch(
                engine,
                inserted_dating_profiles,
            )
            inserted_auth_identities_total += _insert_auth_identities_batch(
                engine,
                batch,
                password_hasher,
            )
            inserted_targeting_total += _insert_targeting_batch(engine, batch)
            batch.clear()

        while checkpoint_idx < len(CHECKPOINTS) and processed_total >= CHECKPOINTS[checkpoint_idx]:
            skipped_users_total = processed_total - inserted_users_total
            _log_checkpoint(
                processed_total=processed_total,
                inserted_total=inserted_users_total,
                skipped_total=skipped_users_total,
                next_checkpoint=CHECKPOINTS[checkpoint_idx],
            )
            checkpoint_idx += 1

        if processed_total >= MAX_USERS_TO_LOAD:
            logger.info("limit_reached max_users=%s stopping_import=true", MAX_USERS_TO_LOAD)
            break

    if batch:
        inserted_users_total += _insert_users_batch(engine, batch)
        inserted_profiles_total += _insert_profiles_batch(engine, batch)
        inserted_dating_profiles = _insert_dating_profiles_batch(engine, batch)
        inserted_dating_profiles_total += len(inserted_dating_profiles)
        inserted_dating_photos_total += _insert_dating_photos_batch(
            engine,
            inserted_dating_profiles,
        )
        inserted_auth_identities_total += _insert_auth_identities_batch(
            engine,
            batch,
            password_hasher,
        )
        inserted_targeting_total += _insert_targeting_batch(engine, batch)

    skipped_users_total = processed_total - inserted_users_total
    logger.info(
        (
            "import_finished processed=%s inserted_users=%s skipped_users=%s "
            "inserted_profiles=%s inserted_dating_profiles=%s inserted_dating_photos=%s "
            "inserted_auth_identities=%s inserted_targeting=%s "
            "max_users=%s"
        ),
        processed_total,
        inserted_users_total,
        skipped_users_total,
        inserted_profiles_total,
        inserted_dating_profiles_total,
        inserted_dating_photos_total,
        inserted_auth_identities_total,
        inserted_targeting_total,
        MAX_USERS_TO_LOAD,
    )


def main() -> None:
    load_dotenv(".env", override=False)

    parser = argparse.ArgumentParser(description="Import ML dataset user UUIDs into backend users table.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("../ml/ids_test.csv"),
        help="Path to CSV file with uuid column (default: ../ml/ids_test.csv).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run(input_path=args.input)


if __name__ == "__main__":
    main()
