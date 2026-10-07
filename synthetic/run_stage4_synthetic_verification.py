from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
    roc_curve,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.data_config import Paths
from ml.infra.db.init_db import init_db
from ml.services.model_training import TARGETS, train_model_family
from ml.services.recommendation_ranking import MODEL_FAMILY_STAGE_4, score_candidate_frame
from ml.services.recommendation_scoring import DEFAULT_ENSEMBLE_WEIGHTS, SERVING_PREDICTION_COLUMN_BY_TARGET
from ml.services.recommendation_store import get_train_rows

from synthetic.db_helpers import (
    SyntheticTypeContract,
    cleanup_synthetic_rows,
    ensure_required_tables_exist,
    load_db_counts,
    validate_stage4_type_contract,
    write_json,
)
from synthetic.interaction_event_simulator import simulate_interactions_via_polling
from synthetic.recommendation_lifecycle_simulator import simulate_recommendation_lifecycle
from synthetic.stage4_user_sampler import load_sampled_users

DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_GROUPS_PER_ACTOR = 5
DEFAULT_CANDIDATES_PER_GROUP = 10
DEFAULT_SEED = 42
DEFAULT_SMOKE_ROWS = 20
REPORTS_ROOT = Paths.out_data_path / "synthetic_reports"


@dataclass(frozen=True)
class TargetMetricSnapshot:
    positive_rate: float
    roc_auc: float | None
    pr_auc: float | None
    log_loss: float | None
    brier_score: float | None


@dataclass(frozen=True)
class InferenceSmokeSummary:
    rows_tested: int
    status: str
    min_scores: dict[str, float]
    mean_scores: dict[str, float]
    max_scores: dict[str, float]
    std_scores: dict[str, float]
    non_constant_targets: list[str]


@dataclass(frozen=True)
class ReportBundlePaths:
    report_dir: str
    train_dataset_path: str
    verification_overview_path: str


@dataclass(frozen=True)
class Stage4VerificationSummary:
    recommendation_id_prefix: str
    users_sampled: int
    recommendation_groups_created: int
    impressions_created: int
    interactions_generated: int
    support_interactions_generated: int
    audit_events_inserted: int
    linked_interactions: int
    finalized_groups: int
    finalized_training_rows: int
    target_label_counts: dict[str, int]
    trained_models: dict[str, str]
    target_metrics: dict[str, TargetMetricSnapshot]
    inference_smoke: InferenceSmokeSummary
    type_contract: SyntheticTypeContract
    train_dataset_path: str
    verification_overview_path: str
    report_dir: str


def run_stage4_synthetic_verification(
    *,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    groups_per_actor: int = DEFAULT_GROUPS_PER_ACTOR,
    candidates_per_group: int = DEFAULT_CANDIDATES_PER_GROUP,
    seed: int = DEFAULT_SEED,
    smoke_rows: int = DEFAULT_SMOKE_ROWS,
) -> Stage4VerificationSummary:
    ensure_required_tables_exist()
    init_db()
    type_contract = validate_stage4_type_contract()

    recommendation_id_prefix = _build_recommendation_prefix(
        sample_size=sample_size,
        groups_per_actor=groups_per_actor,
        candidates_per_group=candidates_per_group,
        seed=seed,
    )
    cleanup_synthetic_rows(recommendation_id_prefix)

    sampled_users_df = load_sampled_users(sample_size=sample_size, seed=seed)
    lifecycle_result = simulate_recommendation_lifecycle(
        sampled_users_df=sampled_users_df,
        groups_per_actor=groups_per_actor,
        candidates_per_group=candidates_per_group,
        seed=seed,
        recommendation_id_prefix=recommendation_id_prefix,
    )
    ingestion_result = simulate_interactions_via_polling(
        recommendation_id_prefix=recommendation_id_prefix,
        impression_records=lifecycle_result.impression_records,
        sampled_users_df=sampled_users_df,
        seed=seed,
    )

    db_counts = load_db_counts(recommendation_id_prefix)
    if db_counts.pending_audit_events != 0:
        raise RuntimeError(
            f"Pending synthetic audit events are not fully drained: {db_counts.pending_audit_events}"
        )
    if ingestion_result.orphan_interactions != 0:
        raise RuntimeError(
            f"Found orphan interactions without recommendation linkage: {ingestion_result.orphan_interactions}"
        )

    stage4_rows = _load_stage4_rows_for_prefix(recommendation_id_prefix)
    if not stage4_rows:
        raise RuntimeError("No finalized stage_4 train rows were produced for synthetic verification run.")
    if not all(row.get("served_stage") == "stage_4" for row in stage4_rows):
        raise RuntimeError("Non-stage_4 rows were found in synthetic train dataset.")

    target_label_counts = {
        target: int(sum(bool(row.get(f"label_true_{target}")) for row in stage4_rows))
        for target in TARGETS
    }
    for target, positives in target_label_counts.items():
        if positives <= 0:
            raise RuntimeError(f"Target '{target}' has zero positive rows.")

    training_result = train_model_family(MODEL_FAMILY_STAGE_4)
    trained_models = _resolve_trained_models(training_result=training_result)

    scored_rows_df = _score_rows(stage4_rows)
    target_metrics = _compute_target_metrics(stage4_rows=stage4_rows, scored_rows_df=scored_rows_df)

    smoke_df = scored_rows_df.head(max(int(smoke_rows), 1)).copy()
    inference_smoke = _build_inference_smoke_summary(smoke_df)

    report_paths = _create_report_bundle(
        recommendation_id_prefix=recommendation_id_prefix,
        action_counts=ingestion_result.action_counts,
        target_label_counts=target_label_counts,
        scored_rows_df=scored_rows_df,
        stage4_rows=stage4_rows,
        target_metrics=target_metrics,
        inference_smoke=inference_smoke,
        type_contract=type_contract,
        summary_payload={
            "poller_totals": ingestion_result.poller_totals,
            "training_result": training_result,
        },
    )

    summary = Stage4VerificationSummary(
        recommendation_id_prefix=recommendation_id_prefix,
        users_sampled=int(sampled_users_df.shape[0]),
        recommendation_groups_created=lifecycle_result.recommendation_groups_created,
        impressions_created=lifecycle_result.impressions_created,
        interactions_generated=ingestion_result.interactions_generated,
        support_interactions_generated=ingestion_result.support_interactions_generated,
        audit_events_inserted=ingestion_result.audit_events_inserted,
        linked_interactions=db_counts.linked_interactions,
        finalized_groups=_count_finalized_groups(recommendation_id_prefix),
        finalized_training_rows=len(stage4_rows),
        target_label_counts=target_label_counts,
        trained_models=trained_models,
        target_metrics=target_metrics,
        inference_smoke=inference_smoke,
        type_contract=type_contract,
        train_dataset_path=report_paths.train_dataset_path,
        verification_overview_path=report_paths.verification_overview_path,
        report_dir=report_paths.report_dir,
    )
    _print_summary(summary)
    return summary


def _build_recommendation_prefix(
    *,
    sample_size: int,
    groups_per_actor: int,
    candidates_per_group: int,
    seed: int,
) -> str:
    return f"s4syn_stage4_s{sample_size}_g{groups_per_actor}_c{candidates_per_group}_seed{seed}"


def _load_stage4_rows_for_prefix(prefix: str) -> list[dict[str, Any]]:
    rows = get_train_rows(served_stages=("stage_4",))
    return [row for row in rows if str(row.get("ml_recommendation_id", "")).startswith(prefix)]


def _resolve_trained_models(*, training_result: dict[str, Any]) -> dict[str, str]:
    stage4_model_dir = Paths.stage_4_model_dir
    statuses: dict[str, str] = {}
    for target in TARGETS:
        model_path = stage4_model_dir / f"{target}.cbm"
        was_trained = target in training_result.get("trained_targets", [])
        statuses[target] = "OK" if was_trained and model_path.exists() else "FAIL"
    return statuses


def _score_rows(stage4_rows: list[dict[str, Any]]) -> pd.DataFrame:
    candidate_df = pd.DataFrame(
        {
            "candidate_id": [row["candidate_user_id"] for row in stage4_rows],
            "feature_snapshot": [row["features_json"] for row in stage4_rows],
        }
    )
    return score_candidate_frame(
        candidate_df,
        family=MODEL_FAMILY_STAGE_4,
        weights=DEFAULT_ENSEMBLE_WEIGHTS,
    )


def _compute_target_metrics(
    *,
    stage4_rows: list[dict[str, Any]],
    scored_rows_df: pd.DataFrame,
) -> dict[str, TargetMetricSnapshot]:
    metrics: dict[str, TargetMetricSnapshot] = {}
    for target in TARGETS:
        label_column = f"label_true_{target}"
        prediction_column = SERVING_PREDICTION_COLUMN_BY_TARGET[target]
        y_true = pd.Series([bool(row.get(label_column)) for row in stage4_rows], dtype=bool).astype(int).to_numpy()
        y_score = pd.to_numeric(scored_rows_df[prediction_column], errors="coerce").fillna(0.0).to_numpy()
        y_score = np.clip(y_score, 1e-6, 1.0 - 1e-6)
        positive_rate = float(np.mean(y_true))

        if np.unique(y_true).size < 2:
            metrics[target] = TargetMetricSnapshot(
                positive_rate=positive_rate,
                roc_auc=None,
                pr_auc=None,
                log_loss=None,
                brier_score=None,
            )
            continue

        metrics[target] = TargetMetricSnapshot(
            positive_rate=positive_rate,
            roc_auc=float(roc_auc_score(y_true, y_score)),
            pr_auc=float(average_precision_score(y_true, y_score)),
            log_loss=float(log_loss(y_true, y_score, labels=[0, 1])),
            brier_score=float(brier_score_loss(y_true, y_score)),
        )
    return metrics


def _build_inference_smoke_summary(smoke_df: pd.DataFrame) -> InferenceSmokeSummary:
    score_columns = [SERVING_PREDICTION_COLUMN_BY_TARGET[target] for target in TARGETS]
    if smoke_df.empty:
        return InferenceSmokeSummary(
            rows_tested=0,
            status="FAIL",
            min_scores={},
            mean_scores={},
            max_scores={},
            std_scores={},
            non_constant_targets=[],
        )

    min_scores: dict[str, float] = {}
    mean_scores: dict[str, float] = {}
    max_scores: dict[str, float] = {}
    std_scores: dict[str, float] = {}
    non_constant_targets: list[str] = []
    for target in TARGETS:
        column = SERVING_PREDICTION_COLUMN_BY_TARGET[target]
        series = pd.to_numeric(smoke_df[column], errors="coerce").fillna(0.0)
        min_scores[target] = float(series.min())
        mean_scores[target] = float(series.mean())
        max_scores[target] = float(series.max())
        std_scores[target] = float(series.std(ddof=0))
        if float(series.nunique(dropna=True)) > 1:
            non_constant_targets.append(target)

    status = (
        "OK"
        if all(column in smoke_df.columns for column in score_columns)
        and set(non_constant_targets) == set(TARGETS)
        else "FAIL"
    )
    return InferenceSmokeSummary(
        rows_tested=int(smoke_df.shape[0]),
        status=status,
        min_scores=min_scores,
        mean_scores=mean_scores,
        max_scores=max_scores,
        std_scores=std_scores,
        non_constant_targets=non_constant_targets,
    )


def _create_report_bundle(
    *,
    recommendation_id_prefix: str,
    action_counts: dict[str, int],
    target_label_counts: dict[str, int],
    scored_rows_df: pd.DataFrame,
    stage4_rows: list[dict[str, Any]],
    target_metrics: dict[str, TargetMetricSnapshot],
    inference_smoke: InferenceSmokeSummary,
    type_contract: SyntheticTypeContract,
    summary_payload: dict[str, Any],
) -> ReportBundlePaths:
    report_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_dir = REPORTS_ROOT / f"{recommendation_id_prefix}_{report_timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)

    metrics_payload = {
        target: asdict(metric_snapshot)
        for target, metric_snapshot in target_metrics.items()
    }
    train_dataset_df = _build_train_dataset(stage4_rows=stage4_rows, scored_rows_df=scored_rows_df)
    train_dataset_path = report_dir / "train_dataset.csv"
    train_dataset_df.to_csv(train_dataset_path, index=False)

    write_json(str(report_dir / "metrics.json"), metrics_payload)
    write_json(str(report_dir / "inference_smoke.json"), asdict(inference_smoke))
    write_json(
        str(report_dir / "runtime_summary.json"),
        {
            **summary_payload,
            "type_contract": asdict(type_contract),
            "train_dataset_path": str(train_dataset_path),
        },
    )
    scored_rows_df.to_csv(report_dir / "scored_rows.csv", index=False)

    overview_path = report_dir / "verification_overview.png"
    _build_visual_report(
        report_path=overview_path,
        action_counts=action_counts,
        target_label_counts=target_label_counts,
        scored_rows_df=scored_rows_df,
        stage4_rows=stage4_rows,
    )

    summary_txt_path = report_dir / "summary.txt"
    summary_lines = [
        f"recommendation_id_prefix={recommendation_id_prefix}",
        f"finalized_rows={len(stage4_rows)}",
        f"train_dataset_path={train_dataset_path}",
        "type_contract:",
        f"  interaction_event_type={type_contract.interaction_created_event_type}",
        f"  interaction_action_map={type_contract.interaction_action_map}",
        f"  interaction_enum_values={list(type_contract.interaction_enum_values)}",
        f"  audit_event_enum_values={list(type_contract.audit_event_enum_values)}",
        "target_metrics:",
    ]
    for target in TARGETS:
        metric = target_metrics[target]
        summary_lines.append(
            f"  {target}: positive_rate={metric.positive_rate:.6f}, "
            f"roc_auc={_fmt(metric.roc_auc)}, pr_auc={_fmt(metric.pr_auc)}, "
            f"log_loss={_fmt(metric.log_loss)}, brier={_fmt(metric.brier_score)}"
        )
    summary_txt_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return ReportBundlePaths(
        report_dir=str(report_dir),
        train_dataset_path=str(train_dataset_path),
        verification_overview_path=str(overview_path),
    )


def _build_train_dataset(
    *,
    stage4_rows: list[dict[str, Any]],
    scored_rows_df: pd.DataFrame,
) -> pd.DataFrame:
    base_columns = [
        "ml_recommendation_id",
        "actor_user_id",
        "candidate_user_id",
        "served_stage",
        "group_status",
        "row_status",
        "shown_at",
        "last_interaction_at",
        "final_action",
        "label_true_like",
        "label_true_dislike",
        "label_true_match",
        "label_true_block",
        "label_pred_like",
        "label_pred_dislike",
        "label_pred_match",
        "label_pred_block",
    ]
    base_df = pd.DataFrame(
        [{column_name: row.get(column_name) for column_name in base_columns} for row in stage4_rows]
    )
    features_df = (
        pd.json_normalize(
            [
                row.get("features_json", {})
                if isinstance(row.get("features_json"), dict)
                else {}
                for row in stage4_rows
            ],
            sep="__",
        )
        .add_prefix("feature__")
        .reset_index(drop=True)
    )
    score_df = scored_rows_df.reset_index(drop=True).add_prefix("score__")
    return pd.concat(
        [
            base_df.reset_index(drop=True),
            features_df,
            score_df,
        ],
        axis=1,
    )


def _build_visual_report(
    *,
    report_path: Path,
    action_counts: dict[str, int],
    target_label_counts: dict[str, int],
    scored_rows_df: pd.DataFrame,
    stage4_rows: list[dict[str, Any]],
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(16, 11))

    action_labels = list(action_counts.keys())
    action_values = [action_counts[label] for label in action_labels]
    axes[0, 0].bar(action_labels, action_values, color=["#4e79a7", "#f28e2b", "#59a14f", "#e15759"])
    axes[0, 0].set_title("Action Distribution")
    axes[0, 0].set_ylabel("Count")

    target_labels = list(target_label_counts.keys())
    target_values = [target_label_counts[label] for label in target_labels]
    axes[0, 1].bar(target_labels, target_values, color=["#76b7b2", "#edc948", "#b07aa1", "#ff9da7"])
    axes[0, 1].set_title("Target Positive Counts")
    axes[0, 1].set_ylabel("Count")

    for target in TARGETS:
        column = SERVING_PREDICTION_COLUMN_BY_TARGET[target]
        values = pd.to_numeric(scored_rows_df[column], errors="coerce").fillna(0.0).to_numpy()
        axes[1, 0].hist(values, bins=30, alpha=0.5, label=target)
    axes[1, 0].set_title("Prediction Score Histogram")
    axes[1, 0].set_xlabel("Predicted probability")
    axes[1, 0].set_ylabel("Frequency")
    axes[1, 0].legend()

    for target in TARGETS:
        y_true = pd.Series([bool(row.get(f"label_true_{target}")) for row in stage4_rows], dtype=bool).astype(int)
        if y_true.nunique(dropna=True) < 2:
            continue
        column = SERVING_PREDICTION_COLUMN_BY_TARGET[target]
        y_score = pd.to_numeric(scored_rows_df[column], errors="coerce").fillna(0.0).to_numpy()
        fpr, tpr, _ = roc_curve(y_true, y_score)
        axes[1, 1].plot(fpr, tpr, linewidth=2, label=target)
    axes[1, 1].plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    axes[1, 1].set_title("ROC Curves")
    axes[1, 1].set_xlabel("False Positive Rate")
    axes[1, 1].set_ylabel("True Positive Rate")
    axes[1, 1].legend()

    figure.tight_layout()
    figure.savefig(report_path, dpi=150)
    plt.close(figure)


def _count_finalized_groups(prefix: str) -> int:
    stage4_rows = get_train_rows(served_stages=("stage_4",))
    recommendation_ids = {
        str(row["ml_recommendation_id"])
        for row in stage4_rows
        if str(row.get("ml_recommendation_id", "")).startswith(prefix)
    }
    return len(recommendation_ids)


def _fmt(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.6f}"


def _print_summary(summary: Stage4VerificationSummary) -> None:
    print(f"users sampled: {summary.users_sampled}")
    print(f"recommendation groups created: {summary.recommendation_groups_created}")
    print(f"impressions created: {summary.impressions_created}")
    print(f"interactions generated (primary): {summary.interactions_generated}")
    print(f"interactions generated (support): {summary.support_interactions_generated}")
    print(f"audit events inserted: {summary.audit_events_inserted}")
    print(f"linked interactions: {summary.linked_interactions}")
    print(f"finalized groups: {summary.finalized_groups}")
    print(f"finalized training rows: {summary.finalized_training_rows}")
    print("type contract:")
    print(f"  - interaction event type: {summary.type_contract.interaction_created_event_type}")
    print(f"  - interaction action map: {summary.type_contract.interaction_action_map}")
    print("target label counts:")
    for target in TARGETS:
        print(f"  - {target} positives: {summary.target_label_counts[target]}")
    print("trained models:")
    for target in TARGETS:
        print(f"  - {target}: {summary.trained_models[target]}")
    print("target quality metrics:")
    for target in TARGETS:
        metric = summary.target_metrics[target]
        print(
            f"  - {target}: positive_rate={metric.positive_rate:.6f}, "
            f"roc_auc={_fmt(metric.roc_auc)}, pr_auc={_fmt(metric.pr_auc)}, "
            f"log_loss={_fmt(metric.log_loss)}, brier={_fmt(metric.brier_score)}"
        )
    print("inference smoke:")
    print(f"  - rows tested: {summary.inference_smoke.rows_tested}")
    print(f"  - status: {summary.inference_smoke.status}")
    print(f"  - non-constant targets: {', '.join(summary.inference_smoke.non_constant_targets) or 'none'}")
    print(f"train_dataset path: {summary.train_dataset_path}")
    print(f"overview plot: {summary.verification_overview_path}")
    print(f"report dir: {summary.report_dir}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run stage_4 synthetic end-to-end verification harness.")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--groups-per-actor", type=int, default=DEFAULT_GROUPS_PER_ACTOR)
    parser.add_argument("--candidates-per-group", type=int, default=DEFAULT_CANDIDATES_PER_GROUP)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--smoke-rows", type=int, default=DEFAULT_SMOKE_ROWS)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_stage4_synthetic_verification(
        sample_size=args.sample_size,
        groups_per_actor=args.groups_per_actor,
        candidates_per_group=args.candidates_per_group,
        seed=args.seed,
        smoke_rows=args.smoke_rows,
    )
    summary_path = Path(summary.report_dir) / "final_summary.json"
    summary_payload = asdict(summary)
    summary_payload["target_metrics"] = {
        target: asdict(metric) for target, metric in summary.target_metrics.items()
    }
    summary_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary_payload["final_summary_path"] = str(summary_path)
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
