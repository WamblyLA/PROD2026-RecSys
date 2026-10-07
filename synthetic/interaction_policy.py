from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

import numpy as np

TARGET_ACTIONS: tuple[str, ...] = ("like", "dislike", "match", "block")


@dataclass(frozen=True)
class InteractionPolicyResult:
    scores: np.ndarray
    actions: list[str]
    quantiles: dict[str, float]


def assign_terminal_actions(
    *,
    actor_user_ids: Sequence[str],
    candidate_user_ids: Sequence[str],
    feature_matrix: np.ndarray,
    user_id_to_index: dict[str, int],
    seed: int,
) -> InteractionPolicyResult:
    if len(actor_user_ids) != len(candidate_user_ids):
        raise ValueError("actor_user_ids and candidate_user_ids must have equal length.")
    if not actor_user_ids:
        return InteractionPolicyResult(scores=np.asarray([], dtype=float), actions=[], quantiles={})

    scores = np.asarray(
        [
            _pairwise_affinity_score(
                actor_user_id=actor_id,
                candidate_user_id=candidate_id,
                actor_vector=feature_matrix[user_id_to_index[actor_id]],
                candidate_vector=feature_matrix[user_id_to_index[candidate_id]],
                seed=seed,
            )
            for actor_id, candidate_id in zip(actor_user_ids, candidate_user_ids, strict=True)
        ],
        dtype=float,
    )

    q20, q60, q90 = np.quantile(scores, [0.20, 0.60, 0.90])
    quantiles = {"q20": float(q20), "q60": float(q60), "q90": float(q90)}

    actions = [_score_to_action(score, quantiles=quantiles) for score in scores]
    _ensure_target_coverage(actions=actions, scores=scores)
    return InteractionPolicyResult(scores=scores, actions=actions, quantiles=quantiles)


def _pairwise_affinity_score(
    *,
    actor_user_id: str,
    candidate_user_id: str,
    actor_vector: np.ndarray,
    candidate_vector: np.ndarray,
    seed: int,
) -> float:
    numerator = float(np.dot(actor_vector, candidate_vector))
    denominator = float(np.linalg.norm(actor_vector) * np.linalg.norm(candidate_vector))
    cosine_similarity = 0.0 if denominator <= 1e-12 else numerator / denominator
    deterministic_noise = _stable_pair_noise(
        actor_user_id=actor_user_id,
        candidate_user_id=candidate_user_id,
        seed=seed,
    )
    return float(cosine_similarity + deterministic_noise)


def _score_to_action(score: float, *, quantiles: dict[str, float]) -> str:
    if score >= quantiles["q90"]:
        return "match"
    if score >= quantiles["q60"]:
        return "like"
    if score >= quantiles["q20"]:
        return "dislike"
    return "block"


def _ensure_target_coverage(*, actions: list[str], scores: np.ndarray) -> None:
    if not actions:
        return

    ranked_indices = np.argsort(scores)
    preferred_indices = {
        "block": int(ranked_indices[0]),
        "dislike": int(ranked_indices[min(len(ranked_indices) // 3, len(ranked_indices) - 1)]),
        "like": int(ranked_indices[max((2 * len(ranked_indices)) // 3, 0)]),
        "match": int(ranked_indices[-1]),
    }
    for action_name in TARGET_ACTIONS:
        if action_name in actions:
            continue
        actions[preferred_indices[action_name]] = action_name


def _stable_pair_noise(*, actor_user_id: str, candidate_user_id: str, seed: int) -> float:
    digest = hashlib.blake2b(
        f"{seed}:{actor_user_id}:{candidate_user_id}".encode("utf-8"),
        digest_size=8,
    ).digest()
    as_int = int.from_bytes(digest, byteorder="big", signed=False)
    scaled = (as_int / float(2**64 - 1)) * 2.0 - 1.0
    return float(scaled * 0.05)

