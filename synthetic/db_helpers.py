from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import MetaData, Table, bindparam, delete, func, inspect, insert, or_, select, text
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import Session

from ml.infra.db.models import (
    Interaction,
    MLRecommendationGroup,
    MLRecommendationImpression,
    MLRecommendationSample,
)
from ml.infra.db.session import SessionLocal, engine
from ml.services.audit_event_types import (
    load_supported_audit_event_type_values,
    resolve_interaction_created_event_type_aliases_for_db,
    resolve_interaction_created_event_type_for_db,
)
from ml.services.interaction_action_types import (
    load_supported_interaction_action_values,
    resolve_interaction_action_map_for_db,
)

_AUDIT_EVENTS_TABLE: Table | None = None
_USERS_TABLE: Table | None = None


@dataclass(frozen=True)
class SyntheticDbCounts:
    recommendation_groups: int
    impressions: int
    audit_events: int
    interactions: int
    linked_interactions: int
    pending_audit_events: int


@dataclass(frozen=True)
class SyntheticTypeContract:
    interaction_action_map: dict[str, str]
    interaction_enum_values: tuple[str, ...]
    audit_event_enum_values: tuple[str, ...]
    interaction_created_event_type: str
    column_types: dict[str, str]


def ensure_required_tables_exist() -> None:
    inspector = inspect(engine)
    required_tables = {
        "audit_events",
        "interactions",
        "users",
        "ml_recommendation_groups",
        "ml_recommendation_impressions",
    }
    missing_tables = sorted(table_name for table_name in required_tables if not inspector.has_table(table_name))
    if missing_tables:
        raise RuntimeError(
            "Synthetic verification requires backend-compatible tables in Postgres. "
            f"Missing tables: {', '.join(missing_tables)}"
        )


def cleanup_synthetic_rows(prefix: str) -> None:
    like_patterns = _build_synthetic_like_patterns(prefix)
    inspector = inspect(engine)
    has_samples_table = inspector.has_table(MLRecommendationSample.__tablename__)
    with SessionLocal() as session:
        with session.begin():
            audit_events = _load_audit_events_table(session)
            session.execute(
                delete(audit_events).where(
                    _build_like_condition(audit_events.c.ml_recommendation_id, like_patterns)
                )
            )
            session.execute(
                delete(Interaction.__table__).where(
                    _build_like_condition(Interaction.ml_recommendation_id, like_patterns)
                )
            )
            session.execute(
                delete(MLRecommendationImpression.__table__).where(
                    _build_like_condition(MLRecommendationImpression.ml_recommendation_id, like_patterns)
                )
            )
            session.execute(
                delete(MLRecommendationGroup.__table__).where(
                    _build_like_condition(MLRecommendationGroup.ml_recommendation_id, like_patterns)
                )
            )
            if has_samples_table:
                session.execute(
                    delete(MLRecommendationSample.__table__).where(
                        _build_like_condition(MLRecommendationSample.ml_recommendation_id, like_patterns)
                    )
                )


def build_support_recommendation_prefix(prefix: str) -> str:
    return f"s4syn_support_{prefix}"


def validate_stage4_type_contract(
    *,
    required_actions: Iterable[str] = ("like", "dislike", "block", "unblock"),
) -> SyntheticTypeContract:
    ensure_required_tables_exist()
    required_action_values = sorted({str(action).strip().lower() for action in required_actions if str(action).strip()})
    if not required_action_values:
        raise RuntimeError("Type contract validation requires at least one interaction action.")

    with SessionLocal() as session:
        interaction_action_map = resolve_interaction_action_map_for_db(session, required_action_values)
        interaction_enum_values = load_supported_interaction_action_values(session)
        audit_event_enum_values = load_supported_audit_event_type_values(session)
        interaction_created_event_type = resolve_interaction_created_event_type_for_db(session)
        column_types = _load_column_types(
            session,
            columns=(
                ("interactions", "id"),
                ("interactions", "actor_user_id"),
                ("interactions", "candidate_user_id"),
                ("interactions", "action"),
                ("audit_events", "event_type"),
                ("ml_recommendation_groups", "actor_user_id"),
                ("ml_recommendation_impressions", "actor_user_id"),
                ("ml_recommendation_impressions", "candidate_user_id"),
            ),
        )

    for key in (
        "interactions.id",
        "interactions.actor_user_id",
        "interactions.candidate_user_id",
        "ml_recommendation_groups.actor_user_id",
        "ml_recommendation_impressions.actor_user_id",
        "ml_recommendation_impressions.candidate_user_id",
    ):
        raw_type = column_types.get(key, "")
        if not raw_type.startswith("uuid:"):
            raise RuntimeError(f"Type contract mismatch for {key}: expected uuid, got '{raw_type}'.")

    action_type = column_types.get("interactions.action", "")
    if action_type != "USER-DEFINED:interaction_type":
        raise RuntimeError(
            "Type contract mismatch for interactions.action: "
            f"expected USER-DEFINED:interaction_type, got '{action_type}'."
        )

    event_type = column_types.get("audit_events.event_type", "")
    if event_type != "USER-DEFINED:audit_event_type":
        raise RuntimeError(
            "Type contract mismatch for audit_events.event_type: "
            f"expected USER-DEFINED:audit_event_type, got '{event_type}'."
        )

    return SyntheticTypeContract(
        interaction_action_map=interaction_action_map,
        interaction_enum_values=interaction_enum_values,
        audit_event_enum_values=audit_event_enum_values,
        interaction_created_event_type=interaction_created_event_type,
        column_types=column_types,
    )


def ensure_users_exist(user_ids: Iterable[str]) -> int:
    user_id_set = sorted({str(user_id).strip() for user_id in user_ids if str(user_id).strip()})
    if not user_id_set:
        return 0

    with SessionLocal() as session:
        with session.begin():
            users_table = _load_users_table(session)
            existing_ids = set(
                str(raw_id)
                for raw_id in session.execute(
                    select(users_table.c.id).where(users_table.c.id.in_(user_id_set))
                ).scalars()
            )

            missing_ids = [user_id for user_id in user_id_set if user_id not in existing_ids]
            if not missing_ids:
                return 0

            now_utc = datetime.now(timezone.utc)
            session.execute(
                insert(users_table),
                [
                    {
                        "id": user_id,
                        "created_at": now_utc,
                        "deleted_at": None,
                    }
                    for user_id in missing_ids
                ],
            )
            return len(missing_ids)


def insert_audit_interaction_events(
    *,
    events: Iterable[dict[str, Any]],
) -> int:
    rows = list(events)
    payloads: list[dict[str, Any]] = []
    if not rows:
        return 0

    with SessionLocal() as session:
        with session.begin():
            interaction_event_type = resolve_interaction_created_event_type_for_db(session)
            for raw_event in rows:
                payloads.append(
                    {
                        "id": str(raw_event.get("id") or uuid4()),
                        "event_type": interaction_event_type,
                        "actor_user_id": str(raw_event["actor_user_id"]),
                        "target_user_id": str(raw_event["candidate_user_id"]),
                        "ml_recommendation_id": str(raw_event["ml_recommendation_id"]),
                        "payload": {"action": str(raw_event["action"])},
                        "sent_to_ml": False,
                        "created_at": raw_event.get("created_at") or datetime.now(timezone.utc),
                        "deleted_at": None,
                    }
                )
            audit_events = _load_audit_events_table(session)
            session.execute(insert(audit_events), payloads)
            return len(payloads)


def load_db_counts(prefix: str) -> SyntheticDbCounts:
    like_pattern = f"{prefix}%"
    with SessionLocal() as session:
        audit_events = _load_audit_events_table(session)
        interaction_event_types = resolve_interaction_created_event_type_aliases_for_db(session)
        pending_audit_events = int(
            session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM audit_events
                    WHERE ml_recommendation_id LIKE :pattern
                      AND deleted_at IS NULL
                      AND sent_to_ml = false
                      AND event_type::text IN :event_types
                    """
                ).bindparams(bindparam("event_types", expanding=True)),
                {
                    "pattern": like_pattern,
                    "event_types": list(interaction_event_types),
                },
            ).scalar_one()
        )
        audit_events_count = int(
            session.execute(
                select(func.count())
                .select_from(audit_events)
                .where(audit_events.c.ml_recommendation_id.like(like_pattern))
            ).scalar_one()
        )
        groups_count = int(
            session.execute(
                select(func.count())
                .select_from(MLRecommendationGroup)
                .where(MLRecommendationGroup.ml_recommendation_id.like(like_pattern))
            ).scalar_one()
        )
        impressions_count = int(
            session.execute(
                select(func.count())
                .select_from(MLRecommendationImpression)
                .where(MLRecommendationImpression.ml_recommendation_id.like(like_pattern))
            ).scalar_one()
        )
        interactions_count = int(
            session.execute(
                select(func.count())
                .select_from(Interaction)
                .where(
                    Interaction.ml_recommendation_id.like(like_pattern),
                    Interaction.deleted_at.is_(None),
                )
            ).scalar_one()
        )
        linked_interactions = int(
            session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM interactions i
                    INNER JOIN ml_recommendation_impressions m
                      ON m.ml_recommendation_id = i.ml_recommendation_id
                     AND m.actor_user_id = i.actor_user_id
                     AND m.candidate_user_id = i.candidate_user_id
                    WHERE i.deleted_at IS NULL
                      AND i.ml_recommendation_id LIKE :pattern
                    """
                ),
                {"pattern": like_pattern},
            ).scalar_one()
        )
        return SyntheticDbCounts(
            recommendation_groups=groups_count,
            impressions=impressions_count,
            audit_events=audit_events_count,
            interactions=interactions_count,
            linked_interactions=linked_interactions,
            pending_audit_events=pending_audit_events,
        )


def load_supported_audit_event_types() -> tuple[str, ...]:
    with SessionLocal() as session:
        return load_supported_audit_event_type_values(session)


def resolve_interaction_audit_event_type() -> str:
    with SessionLocal() as session:
        return resolve_interaction_created_event_type_for_db(session)


def load_audit_event_type_counts(prefix: str) -> dict[str, int]:
    like_pattern = f"{prefix}%"
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT event_type::text AS event_type, COUNT(*) AS row_count
                FROM audit_events
                WHERE ml_recommendation_id LIKE :pattern
                GROUP BY event_type::text
                ORDER BY event_type::text ASC
                """
            ),
            {"pattern": like_pattern},
        ).mappings()
        counts: dict[str, int] = {}
        for row in rows:
            event_type = str(row["event_type"])
            counts[event_type] = int(row["row_count"])
        return counts


def load_impressions_for_prefix(prefix: str) -> list[dict[str, Any]]:
    like_pattern = f"{prefix}%"
    with SessionLocal() as session:
        rows = session.execute(
            select(
                MLRecommendationImpression.ml_recommendation_id,
                MLRecommendationImpression.actor_user_id,
                MLRecommendationImpression.candidate_user_id,
                MLRecommendationImpression.shown_at,
            )
            .where(MLRecommendationImpression.ml_recommendation_id.like(like_pattern))
            .order_by(
                MLRecommendationImpression.ml_recommendation_id.asc(),
                MLRecommendationImpression.actor_user_id.asc(),
                MLRecommendationImpression.candidate_user_id.asc(),
            )
        ).all()
        return [
            {
                "ml_recommendation_id": str(row.ml_recommendation_id),
                "actor_user_id": str(row.actor_user_id),
                "candidate_user_id": str(row.candidate_user_id),
                "shown_at": row.shown_at,
            }
            for row in rows
        ]


def count_orphan_interactions(prefix: str) -> int:
    like_pattern = f"{prefix}%"
    with SessionLocal() as session:
        return int(
            session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM interactions i
                    LEFT JOIN ml_recommendation_impressions m
                      ON m.ml_recommendation_id = i.ml_recommendation_id
                     AND m.actor_user_id = i.actor_user_id
                     AND m.candidate_user_id = i.candidate_user_id
                    WHERE i.deleted_at IS NULL
                      AND i.ml_recommendation_id LIKE :pattern
                      AND m.ml_recommendation_id IS NULL
                    """
                ),
                {"pattern": like_pattern},
            ).scalar_one()
        )


def count_interactions_missing_recommendation_id(prefix: str) -> int:
    like_pattern = f"{prefix}%"
    with SessionLocal() as session:
        return int(
            session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM interactions
                    WHERE deleted_at IS NULL
                      AND (ml_recommendation_id IS NULL OR ml_recommendation_id = '')
                      AND (
                        actor_user_id IN (
                            SELECT actor_user_id
                            FROM ml_recommendation_groups
                            WHERE ml_recommendation_id LIKE :pattern
                        )
                      )
                    """
                ),
                {"pattern": like_pattern},
            ).scalar_one()
        )


def _load_audit_events_table(session: Session) -> Table:
    global _AUDIT_EVENTS_TABLE
    if _AUDIT_EVENTS_TABLE is not None:
        return _AUDIT_EVENTS_TABLE

    metadata = MetaData()
    try:
        _AUDIT_EVENTS_TABLE = Table("audit_events", metadata, autoload_with=session.bind)
    except NoSuchTableError as exc:
        raise RuntimeError("Required table 'audit_events' does not exist.") from exc
    return _AUDIT_EVENTS_TABLE


def _load_users_table(session: Session) -> Table:
    global _USERS_TABLE
    if _USERS_TABLE is not None:
        return _USERS_TABLE

    metadata = MetaData()
    try:
        _USERS_TABLE = Table("users", metadata, autoload_with=session.bind)
    except NoSuchTableError as exc:
        raise RuntimeError("Required table 'users' does not exist for FK-safe audit event insertion.") from exc
    return _USERS_TABLE


def write_json(path: str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as output_stream:
        json.dump(payload, output_stream, ensure_ascii=True, indent=2)


def _build_synthetic_like_patterns(prefix: str) -> tuple[str, ...]:
    patterns = [
        f"{prefix}%",
        f"{build_support_recommendation_prefix(prefix)}%",
    ]
    # Backward-compat cleanup for older synthetic runs that used match actions directly.
    if prefix.startswith("s4syn_stage4_"):
        patterns.extend(
            [
                "s4syn_stage4_%",
                "s4syn_support_s4syn_stage4_%",
            ]
        )
    return tuple(dict.fromkeys(patterns))


def _build_like_condition(column, like_patterns: Iterable[str]):
    clauses = [column.like(pattern) for pattern in like_patterns]
    if not clauses:
        raise RuntimeError("At least one pattern is required for synthetic cleanup condition.")
    return or_(*clauses)


def _load_column_types(
    session: Session,
    *,
    columns: Iterable[tuple[str, str]],
) -> dict[str, str]:
    column_type_map: dict[str, str] = {}
    for table_name, column_name in columns:
        row = session.execute(
            text(
                """
                SELECT data_type, udt_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).mappings().first()
        if row is None:
            raise RuntimeError(f"Type contract mismatch: missing column {table_name}.{column_name}.")
        data_type = str(row["data_type"])
        udt_name = str(row["udt_name"])
        column_type_map[f"{table_name}.{column_name}"] = f"{data_type}:{udt_name}"
    return column_type_map
