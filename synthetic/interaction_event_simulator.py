from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pandas as pd

from .db_helpers import (
    build_support_recommendation_prefix,
    count_orphan_interactions,
    ensure_users_exist,
    insert_audit_interaction_events,
    load_db_counts,
)
from .interaction_policy import assign_terminal_actions
from .stage4_user_sampler import (
    USER_ID_COLUMN,
    build_normalized_feature_matrix,
    resolve_transaction_feature_columns,
)


@dataclass(frozen=True)
class InteractionSimulationResult:
    interactions_generated: int
    support_interactions_generated: int
    audit_events_inserted: int
    linked_interactions: int
    orphan_interactions: int
    polling_cycles: int
    action_counts: dict[str, int]
    poller_totals: dict[str, int]


def simulate_interactions_via_polling(
    *,
    recommendation_id_prefix: str,
    impression_records: list[dict[str, Any]],
    sampled_users_df: pd.DataFrame,
    seed: int,
    poll_batch_size: int = 5000,
    max_poll_cycles: int = 1000,
) -> InteractionSimulationResult:
    if USER_ID_COLUMN not in sampled_users_df.columns:
        raise ValueError(f"sampled_users_df must contain '{USER_ID_COLUMN}'.")
    if not impression_records:
        return InteractionSimulationResult(
            interactions_generated=0,
            support_interactions_generated=0,
            audit_events_inserted=0,
            linked_interactions=0,
            orphan_interactions=0,
            polling_cycles=0,
            action_counts={},
            poller_totals={},
        )

    feature_columns = resolve_transaction_feature_columns(sampled_users_df)
    normalized_matrix = build_normalized_feature_matrix(sampled_users_df, feature_columns=feature_columns)
    user_ids = sampled_users_df[USER_ID_COLUMN].astype("string").tolist()
    user_id_to_index = {user_id: idx for idx, user_id in enumerate(user_ids)}

    actor_user_ids = [str(row["actor_user_id"]) for row in impression_records]
    candidate_user_ids = [str(row["candidate_user_id"]) for row in impression_records]
    for actor_user_id, candidate_user_id in zip(actor_user_ids, candidate_user_ids, strict=True):
        if actor_user_id == candidate_user_id:
            raise RuntimeError(
                f"Invalid self-interaction impression detected for actor={actor_user_id}."
            )
    policy_result = assign_terminal_actions(
        actor_user_ids=actor_user_ids,
        candidate_user_ids=candidate_user_ids,
        feature_matrix=normalized_matrix,
        user_id_to_index=user_id_to_index,
        seed=seed,
    )

    primary_event_rows: list[dict[str, Any]] = []
    support_event_rows: list[dict[str, Any]] = []
    action_counts: dict[str, int] = {}
    for index, (record, action) in enumerate(zip(impression_records, policy_result.actions, strict=True)):
        event_created_at = _resolve_event_created_at(record.get("shown_at"), index=index)
        actor_user_id = str(record["actor_user_id"])
        candidate_user_id = str(record["candidate_user_id"])
        recommendation_id = str(record["ml_recommendation_id"])
        primary_action = "like" if action == "match" else action

        primary_event_rows.append(
            {
                "id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"{seed}:primary:{recommendation_id}:{actor_user_id}:{candidate_user_id}",
                    )
                ),
                "actor_user_id": actor_user_id,
                "candidate_user_id": candidate_user_id,
                "ml_recommendation_id": recommendation_id,
                "action": primary_action,
                "created_at": event_created_at,
            }
        )
        if action == "match":
            support_recommendation_id = _build_support_recommendation_id(
                recommendation_id_prefix=recommendation_id_prefix,
                seed=seed,
                index=index,
                actor_user_id=actor_user_id,
                candidate_user_id=candidate_user_id,
            )
            support_event_rows.append(
                {
                    "id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"{seed}:support:{recommendation_id}:{actor_user_id}:{candidate_user_id}",
                        )
                    ),
                    "actor_user_id": candidate_user_id,
                    "candidate_user_id": actor_user_id,
                    "ml_recommendation_id": support_recommendation_id,
                    "action": "like",
                    "created_at": event_created_at + timedelta(microseconds=500),
                }
            )
        action_counts[action] = action_counts.get(action, 0) + 1

    all_event_rows = [*primary_event_rows, *support_event_rows]
    ensure_users_exist(
        [
            str(event_row["actor_user_id"])
            for event_row in all_event_rows
        ]
        + [
            str(event_row["candidate_user_id"])
            for event_row in all_event_rows
        ]
    )

    inserted_events = insert_audit_interaction_events(events=all_event_rows)
    if inserted_events != len(all_event_rows):
        raise RuntimeError(
            f"Unexpected audit event insert count: inserted={inserted_events}, expected={len(all_event_rows)}"
        )

    try:
        from ml.services.interaction_event_poller import poll_audit_events_once
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Unable to import interaction poller dependencies. "
            "Install ML runtime dependencies before running synthetic verification."
        ) from exc

    poller_totals: dict[str, int] = {}
    polling_cycles = 0
    for _ in range(max_poll_cycles):
        summary = poll_audit_events_once(batch_size=poll_batch_size)
        polling_cycles += 1
        _merge_poller_summary(poller_totals, summary)
        if int(summary.get("selected_total", 0)) == 0:
            break
    else:
        raise RuntimeError(
            f"Polling did not drain pending audit events within {max_poll_cycles} cycles."
        )

    db_counts = load_db_counts(recommendation_id_prefix)
    orphan_interactions = count_orphan_interactions(recommendation_id_prefix)
    return InteractionSimulationResult(
        interactions_generated=len(primary_event_rows),
        support_interactions_generated=len(support_event_rows),
        audit_events_inserted=len(all_event_rows),
        linked_interactions=db_counts.linked_interactions,
        orphan_interactions=orphan_interactions,
        polling_cycles=polling_cycles,
        action_counts=action_counts,
        poller_totals=poller_totals,
    )


def _resolve_event_created_at(raw_shown_at: Any, *, index: int) -> datetime:
    if isinstance(raw_shown_at, datetime):
        shown_at = raw_shown_at
    else:
        shown_at = datetime.fromisoformat(str(raw_shown_at))
    return shown_at + timedelta(milliseconds=int(index))


def _merge_poller_summary(accumulator: dict[str, int], summary: dict[str, int]) -> None:
    for key, value in summary.items():
        accumulator[key] = accumulator.get(key, 0) + int(value or 0)


def _build_support_recommendation_id(
    *,
    recommendation_id_prefix: str,
    seed: int,
    index: int,
    actor_user_id: str,
    candidate_user_id: str,
) -> str:
    support_prefix = build_support_recommendation_prefix(recommendation_id_prefix)
    pair_suffix = str(
        uuid5(
            NAMESPACE_URL,
            f"{seed}:{actor_user_id}:{candidate_user_id}:{index}",
        )
    )[:12]
    return f"{support_prefix}_{seed}_{index:08d}_{pair_suffix}"
