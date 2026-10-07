from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from ml.services.user_id import normalize_user_id

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_USER_FEATURES_PATH = PROJECT_ROOT / "data_out" / "user_features_all.csv"
USER_ID_COLUMN = "party_rk"
_NON_NUMERIC_EXCLUDE_COLUMNS = {
    USER_ID_COLUMN,
    "first_txn_dttm",
    "last_txn_dttm",
}


def load_sampled_users(
    sample_size: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    user_features_path = DEFAULT_USER_FEATURES_PATH
    if not user_features_path.exists():
        raise FileNotFoundError(
            f"Required user feature source does not exist: {user_features_path}"
        )

    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    sampled_df = pd.read_csv(user_features_path, low_memory=False)
    if USER_ID_COLUMN not in sampled_df.columns:
        raise ValueError(f"Required column '{USER_ID_COLUMN}' is missing in {user_features_path}.")

    sampled_df[USER_ID_COLUMN] = sampled_df[USER_ID_COLUMN].astype("string").str.strip()
    sampled_df = sampled_df[sampled_df[USER_ID_COLUMN].notna() & (sampled_df[USER_ID_COLUMN] != "")].copy()
    sampled_df = sampled_df.drop_duplicates(subset=[USER_ID_COLUMN], keep="first").reset_index(drop=True)

    if sampled_df.empty:
        raise ValueError("user_features_all.csv has no valid users.")

    if sample_size > len(sampled_df):
        raise ValueError(
            "sample_size is larger than available users in user_features_all.csv "
            f"({sample_size} > {len(sampled_df)})."
        )

    rng = np.random.default_rng(seed)
    sampled_indices = np.sort(rng.choice(len(sampled_df), size=sample_size, replace=False))
    result = sampled_df.iloc[sampled_indices].reset_index(drop=True)

    normalized_ids = result[USER_ID_COLUMN].map(lambda raw_id: normalize_user_id(raw_id, allow_hash=True))
    invalid_id_mask = normalized_ids.isna()
    if bool(invalid_id_mask.any()):
        invalid_count = int(invalid_id_mask.astype(int).sum())
        raise ValueError(
            f"user_features_all.csv contains {invalid_count} invalid user ids in '{USER_ID_COLUMN}'."
        )

    result[USER_ID_COLUMN] = normalized_ids.astype("string")
    return result


def resolve_transaction_feature_columns(sampled_users_df: pd.DataFrame) -> list[str]:
    columns: list[str] = []
    for column in sampled_users_df.columns:
        if column in _NON_NUMERIC_EXCLUDE_COLUMNS:
            continue
        if pd.api.types.is_numeric_dtype(sampled_users_df[column]):
            columns.append(column)
    if not columns:
        raise ValueError("No numeric transaction feature columns found in sampled users frame.")
    return columns


def build_normalized_feature_matrix(
    sampled_users_df: pd.DataFrame,
    *,
    feature_columns: list[str],
) -> np.ndarray:
    raw_matrix = (
        sampled_users_df[feature_columns]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=np.float64)
    )
    means = raw_matrix.mean(axis=0)
    stds = raw_matrix.std(axis=0)
    stds = np.where(stds < 1e-12, 1.0, stds)
    normalized = (raw_matrix - means) / stds
    normalized = np.nan_to_num(normalized, nan=0.0, posinf=0.0, neginf=0.0)
    return normalized.astype(np.float32)
