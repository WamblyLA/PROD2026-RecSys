# Stage 4 Synthetic Verification Harness

## What it verifies

End-to-end stage_4 lifecycle using real project flows:

1. real users sampled from `ml/data_out/user_features_all.csv`
2. recommendation groups + impressions persisted into DB
3. synthetic interactions inserted as `audit_events`
4. prod-like polling path `poll_audit_events_once` runs ingestion + finalization
5. finalized train rows loaded with `served_stage == "stage_4"`
6. stage_4 family trains 4 CatBoost models (`like`, `dislike`, `match`, `block`)
7. inference smoke runs with trained artifacts
8. quality metrics and visual report are produced
9. train dataset artifact is exported for inspection (`train_dataset.csv`)

Runtime safety guards:

- resolves `audit_events.event_type` from backend/DB enum labels (`audit_event_type`) instead of hardcoded string
- resolves `interactions.action` to backend `interaction_type` enum labels before DB write
- enforces `actor_user_id != candidate_user_id` for every synthetic impression
- cleans up previous synthetic rows by deterministic recommendation-id prefix before each run
- validates key DB column/enums contract before run (`UUID`, `interaction_type`, `audit_event_type`)

Labeling rule for `match`:

- synthetic policy action `match` is persisted as `like` + reciprocal support-like event
- finalized label `match` is inferred via backend-style rule: mutual latest `like`
- for matched rows, labels are multi-label: `label_true_like=1` and `label_true_match=1`

## Run

From workspace root:

```bash
python ml/synthetic/run_stage4_synthetic_all_in_one.py --sample-size 1000 --groups-per-actor 5 --candidates-per-group 10 --seed 42
```

Defaults:

- `sample_size=1000`
- `groups_per_actor=5`
- `candidates_per_group=10`
- `seed=42`
- `smoke_rows=20`
- `db_timeout_seconds=180`
- auto-start DB/schema bootstrap if needed
- auto-stop only services started by this run (`postgres` by default, use `--keep-postgres` to keep it running)

## Output

Report folder:

- `ml/data_out/synthetic_reports/<run_id>/verification_overview.png`
- `ml/data_out/synthetic_reports/<run_id>/train_dataset.csv`
- `ml/data_out/synthetic_reports/<run_id>/metrics.json`
- `ml/data_out/synthetic_reports/<run_id>/runtime_summary.json`
- `ml/data_out/synthetic_reports/<run_id>/summary.txt`
- `ml/data_out/synthetic_reports/<run_id>/final_summary.json`

Console summary includes:

- sampled users/groups/impressions/interactions
- linkage/finalization counts
- strict type-contract snapshot (enum labels + key column types)
- per-target positives
- model train/save status
- inference smoke status
- per-target quality metrics (ROC-AUC, PR-AUC, LogLoss, Brier)

## Tests

Run:

```bash
pytest ml/tests/test_stage4_synthetic_pipeline.py ml/tests/test_stage4_training_smoke.py
```

If required DB tables are missing, tests are skipped with a clear precondition message.
