from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from ml.infra.db.session import SessionLocal
from ml.services.recommendation_feature_snapshot import attach_feature_snapshots
from ml.services.recommendation_scoring import RecommendationStage
from ml.services.recommendation_store import save_recommendation_group_in_session

from .stage4_user_sampler import (
    USER_ID_COLUMN,
    build_normalized_feature_matrix,
    resolve_transaction_feature_columns,
)


@dataclass(frozen=True)
class RecommendationLifecycleResult:
    recommendation_id_prefix: str
    users_sampled: int
    recommendation_groups_created: int
    impressions_created: int
    recommendation_ids: list[str]
    impression_records: list[dict[str, Any]]


def simulate_recommendation_lifecycle(
    *,
    sampled_users_df: pd.DataFrame,
    groups_per_actor: int,
    candidates_per_group: int,
    seed: int,
    recommendation_id_prefix: str,
) -> RecommendationLifecycleResult:
    if groups_per_actor <= 0:
        raise ValueError("groups_per_actor must be positive.")
    if candidates_per_group <= 0:
        raise ValueError("candidates_per_group must be positive.")
    if USER_ID_COLUMN not in sampled_users_df.columns:
        raise ValueError(f"sampled_users_df must contain '{USER_ID_COLUMN}'.")

    actor_user_ids = sampled_users_df[USER_ID_COLUMN].astype("string").tolist()
    if len(actor_user_ids) <= 1:
        raise ValueError("Need at least two users for recommendation simulation.")

    total_candidates_per_actor = groups_per_actor * candidates_per_group
    if total_candidates_per_actor >= len(actor_user_ids):
        raise ValueError(
            "groups_per_actor * candidates_per_group must be < sampled user count "
            f"({total_candidates_per_actor} >= {len(actor_user_ids)})."
        )

    feature_columns = resolve_transaction_feature_columns(sampled_users_df)
    normalized_matrix = build_normalized_feature_matrix(sampled_users_df, feature_columns=feature_columns)
    unit_matrix = _normalize_rows(normalized_matrix)

    rng = np.random.default_rng(seed)
    base_shown_at = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=int(seed))
    all_recommendation_ids: list[str] = []
    all_impression_records: list[dict[str, Any]] = []
    running_group_index = 0

    with SessionLocal() as session:
        with session.begin():
            for actor_index, actor_user_id in enumerate(actor_user_ids):
                candidate_indices = _select_candidate_indices_for_actor(
                    actor_index=actor_index,
                    unit_matrix=unit_matrix,
                    total_candidates=total_candidates_per_actor,
                    rng=rng,
                )
                if np.any(candidate_indices == actor_index):
                    raise RuntimeError(
                        f"Self-candidate index detected for actor={actor_user_id}. "
                        "Synthetic lifecycle must exclude actor from candidates."
                    )
                actor_similarity_scores = np.dot(unit_matrix[candidate_indices], unit_matrix[actor_index])
                actor_candidates_df = pd.DataFrame(
                    {
                        "candidate_id": [actor_user_ids[idx] for idx in candidate_indices],
                        "distance_euclidean": (1.0 - actor_similarity_scores).astype(float),
                        "retrieval_primary_source": "synthetic_similarity",
                        "retrieval_sources_count": 1,
                        "retrieval_sources": [["synthetic_similarity"] for _ in candidate_indices],
                        "rank": list(range(1, len(candidate_indices) + 1)),
                        "impactful_features": [{} for _ in candidate_indices],
                        "impactful_features_origin": "synthetic_similarity",
                        "impactful_features_seed_basis": [f"{seed}:{actor_user_id}" for _ in candidate_indices],
                    }
                )
                actor_candidates_df = attach_feature_snapshots(
                    actor_candidates_df,
                    actor_user_id=actor_user_id,
                    stage=RecommendationStage.STAGE_4,
                    session=session,
                )
                source_rows_by_candidate = _build_source_rows(
                    actor_user_id=actor_user_id,
                    candidate_frame=actor_candidates_df,
                    similarity_scores=actor_similarity_scores,
                )

                for group_number in range(groups_per_actor):
                    offset = group_number * candidates_per_group
                    group_candidate_ids = [
                        actor_user_ids[idx]
                        for idx in candidate_indices[offset: offset + candidates_per_group]
                    ]
                    if any(candidate_user_id == actor_user_id for candidate_user_id in group_candidate_ids):
                        raise RuntimeError(
                            f"Self-candidate detected in recommendation group for actor={actor_user_id}."
                        )
                    recommendation_rows = [
                        {
                            "candidate_user_id": candidate_user_id,
                            "source_row": source_rows_by_candidate[candidate_user_id],
                        }
                        for candidate_user_id in group_candidate_ids
                    ]
                    recommendation_id = (
                        f"{recommendation_id_prefix}_{seed}_{actor_index:04d}_{group_number:03d}"
                    )
                    shown_at = base_shown_at + timedelta(seconds=running_group_index)
                    running_group_index += 1

                    save_recommendation_group_in_session(
                        session,
                        recommendation_id=recommendation_id,
                        actor_user_id=actor_user_id,
                        recommendation_rows=recommendation_rows,
                        shown_at=shown_at,
                        served_stage="stage_4",
                    )
                    all_recommendation_ids.append(recommendation_id)
                    for candidate_user_id in group_candidate_ids:
                        all_impression_records.append(
                            {
                                "ml_recommendation_id": recommendation_id,
                                "actor_user_id": actor_user_id,
                                "candidate_user_id": candidate_user_id,
                                "shown_at": shown_at,
                            }
                        )

    return RecommendationLifecycleResult(
        recommendation_id_prefix=recommendation_id_prefix,
        users_sampled=len(actor_user_ids),
        recommendation_groups_created=len(all_recommendation_ids),
        impressions_created=len(all_impression_records),
        recommendation_ids=all_recommendation_ids,
        impression_records=all_impression_records,
    )


def _select_candidate_indices_for_actor(
    *,
    actor_index: int,
    unit_matrix: np.ndarray,
    total_candidates: int,
    rng: np.random.Generator,
) -> np.ndarray:
    similarity = np.dot(unit_matrix, unit_matrix[actor_index]).astype(float)
    similarity[actor_index] = -np.inf
    ordered_indices = np.argsort(similarity)[::-1]

    base_positions = np.linspace(0, len(ordered_indices) - 1, total_candidates, dtype=int)
    jitter = rng.integers(-3, 4, size=total_candidates)
    candidate_positions = np.clip(base_positions + jitter, 0, len(ordered_indices) - 1)

    selected_indices: list[int] = []
    seen_indices: set[int] = set()
    for position in candidate_positions:
        candidate_idx = int(ordered_indices[int(position)])
        if candidate_idx == actor_index:
            continue
        if candidate_idx in seen_indices:
            continue
        selected_indices.append(candidate_idx)
        seen_indices.add(candidate_idx)

    if len(selected_indices) < total_candidates:
        for candidate_idx in ordered_indices:
            candidate_idx = int(candidate_idx)
            if candidate_idx == actor_index:
                continue
            if candidate_idx in seen_indices:
                continue
            selected_indices.append(candidate_idx)
            seen_indices.add(candidate_idx)
            if len(selected_indices) == total_candidates:
                break

    if len(selected_indices) < total_candidates:
        raise RuntimeError(
            f"Unable to build non-self candidate pool: requested={total_candidates}, built={len(selected_indices)}."
        )

    return np.asarray(selected_indices[:total_candidates], dtype=int)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms <= 1e-12, 1.0, norms)
    return (matrix / norms).astype(np.float32)


def _build_source_rows(
    *,
    actor_user_id: str,
    candidate_frame: pd.DataFrame,
    similarity_scores: np.ndarray,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row, score in zip(candidate_frame.to_dict(orient="records"), similarity_scores, strict=True):
        candidate_user_id = str(row["candidate_id"])
        score_01 = float(np.clip((float(score) + 1.0) / 2.0, 0.0, 1.0))
        source_row = dict(row)
        source_row["candidate_id"] = candidate_user_id
        source_row["query_party_rk"] = actor_user_id
        source_row["y_pred_like"] = score_01
        source_row["y_pred_match"] = float(np.clip((score_01 - 0.6) / 0.4, 0.0, 1.0))
        source_row["y_pred_dislike"] = float(np.clip(1.0 - score_01, 0.0, 1.0))
        source_row["y_pred_block"] = float(np.clip((0.35 - score_01) / 0.35, 0.0, 1.0))
        result[candidate_user_id] = source_row
    return result
