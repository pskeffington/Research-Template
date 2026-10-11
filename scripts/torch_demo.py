"""Optional toy CPU MLP with group-isolated holdout and training-only transforms.

Synthetic method illustration only; not an approved clinical or research model.
"""

import json

import numpy as np
import torch
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research_template.synthetic import make_cohort


def main():
    seed = 711
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    rows = make_cohort(n=300, seed=seed)
    x = np.asarray([
        [np.nan if r["age_years"] is None else r["age_years"],
         np.nan if r["measurement_mg_dl"] is None else r["measurement_mg_dl"]]
        for r in rows
    ], dtype=float)
    y = np.asarray([r["outcome"] for r in rows], dtype=np.float32)
    groups = np.asarray([r["participant_id"] for r in rows])
    tr, te = next(GroupShuffleSplit(test_size=0.25, random_state=seed).split(x, y, groups))
    assert not set(groups[tr]).intersection(groups[te])
    transform = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    xtr = torch.tensor(transform.fit_transform(x[tr]), dtype=torch.float32)
    xte = torch.tensor(transform.transform(x[te]), dtype=torch.float32)
    ytr = torch.tensor(y[tr].reshape(-1, 1), dtype=torch.float32)
    model = torch.nn.Sequential(torch.nn.Linear(2, 8), torch.nn.ReLU(), torch.nn.Linear(8, 1))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    for _ in range(30):
        optimizer.zero_grad()
        loss = loss_fn(model(xtr), ytr)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        pred = (torch.sigmoid(model(xte)).numpy().reshape(-1) >= 0.5).astype(int)
    print(json.dumps({
        "status": "SYNTHETIC_EXPLORATION_ONLY",
        "n_train": len(tr), "n_test": len(te),
        "holdout_balanced_accuracy": balanced_accuracy_score(y[te], pred),
        "note": "No clinical validity; no automated model persistence or deployment.",
    }, indent=2))


if __name__ == "__main__":
    main()
