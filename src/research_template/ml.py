"""Leakage-aware synthetic ML demonstration; never treat metrics as clinical evidence."""

from __future__ import annotations


def run_classification(rows: list[dict], *, seed: int = 711) -> dict:
    """Compare majority dummy baseline and logistic pipeline on a held-out group split.

    Any repeated records sharing participant_id must stay in the same partition.
    The imputer and scaler are fitted on training rows only, inside the pipeline.
    """
    import numpy as np
    from sklearn.dummy import DummyClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    required = {"participant_id", "age_years", "measurement_mg_dl", "outcome"}
    if not rows or any(not required.issubset(r) for r in rows):
        raise ValueError("Missing required ML columns")
    x = np.array(
        [[np.nan if r[f] is None else float(r[f]) for f in ("age_years", "measurement_mg_dl")] for r in rows],
        dtype=float,
    )
    y = np.asarray([r["outcome"] for r in rows], dtype=int)
    groups = np.asarray([r["participant_id"] for r in rows])
    if not np.isin(y, [0, 1]).all() or len(set(y)) != 2:
        raise ValueError("Binary outcome with both classes required")
    train, test = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(x, y, groups=groups))
    if set(groups[train]).intersection(groups[test]):
        raise RuntimeError("Group leakage detected")
    if len(set(y[train])) != 2 or len(set(y[test])) != 2:
        raise ValueError("Split missing a class; revise design or sample")
    candidate = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=seed)),
    ])
    baseline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", DummyClassifier(strategy="prior")),
    ])
    metrics = {}
    for name, pipeline in (("dummy_majority", baseline), ("logistic", candidate)):
        pipeline.fit(x[train], y[train])
        proba = pipeline.predict_proba(x[test])[:, 1]
        metrics[name] = {
            "balanced_accuracy": float(balanced_accuracy_score(y[test], pipeline.predict(x[test]))),
            "auroc": float(roc_auc_score(y[test], proba)),
            "brier_score": float(brier_score_loss(y[test], proba)),
        }
    return {
        "status": "SYNTHETIC_METHOD_DEMO_NOT_CLINICALLY_VALIDATED",
        "split": "GroupShuffleSplit(participant_id), 75% train / 25% holdout",
        "n_train_rows": len(train),
        "n_test_rows": len(test),
        "train_unique_participants": len(set(groups[train])),
        "test_unique_participants": len(set(groups[test])),
        "test_outcome_counts": {str(k): int(sum(y[test] == k)) for k in (0, 1)},
        "metrics": metrics,
        "warning": "No tuning on holdout. External validation, uncertainty, calibration and bias review are pending.",
    }
