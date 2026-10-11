# Function calls — reusable Python and R quick reference

**Python:** install `python -m pip install -e '.[all]'` and run from repository root. Optional extras are `[plot]`, `[ml]`, `[torch]`, `[dev]`. Install `[torch,ml]` for the optional neural example. No dependency is automatically fetched on library import.

```python
from pathlib import Path
from research_template.synthetic import make_cohort
from research_template.quality import validate_cohort
from research_template.plots import histogram, scatter, group_box, heatmap, save_figure
from research_template.ml import run_classification
from research_template.provenance import sha256_file, create_manifest, save_json

rows = make_cohort(n=120, seed=711)                  # fabricated unique IDs
report = validate_cohort(rows)                       # key/type/missing/units
print(report["missing_counts"], report["units"])

p1 = histogram(rows, "age_years", name="Age", unit="years")
p2 = scatter(rows, "age_years", "measurement_mg_dl",
             x_name="Age", x_unit="years",
             y_name="Simulated measurement", y_unit="mg/dL")
p3 = group_box(rows, "measurement_mg_dl", "site",
               name="Simulated measurement", unit="mg/dL")
p4 = heatmap([[1, 2], [3, 4]], row_labels=["G1", "G2"],
             col_labels=["S1", "S2"], name="Synthetic abundance",
             unit="unitless", mode="sequential")
save_figure(p1, "artifacts/figures/age.png", dpi=300) # PDF/SVG also supported
metrics = run_classification(rows, seed=711)        # leakage-aware example
print(metrics["metrics"]["dummy_majority"])
print(metrics["metrics"]["logistic"])
```

| Function | Input contract | Output / side effect | Safeguard |
| --- | --- | --- | --- |
| `make_cohort(n, seed)` | n ≥40, integer seed | Synthetic list of dictionaries | Never real observations |
| `validate_cohort(rows)` | Unique participant IDs, declared five columns | Counts and missingness report | Rejects duplicate keys, invalid measurements and outcome codes |
| `axis_label(name, unit)` | Nonempty strings | Human-readable labeled unit | Never guesses a scale |
| `histogram(rows, value, name=..., unit=...)` | Numeric column and unit | Matplotlib figure | Caption states n and exclusions |
| `scatter(rows, x, y, x_name=..., x_unit=..., y_name=..., y_unit=...)` | Two numeric columns | Figure of complete pairs | No implied causal fit |
| `group_box(rows, value, group, name=..., unit=...)` | 2–8 categories, ≥2 values each | Colored boxplot | Group denominators shown |
| `heatmap(matrix, row_labels=..., col_labels=..., name=..., unit=..., mode=...)` | Finite matrix with matching labels | Sequential or diverging figure | Signed scale only when meaningful |
| `save_figure(fig, path, dpi=300)` | png/pdf/svg path | Writes graphic intentionally | No implicit publication |
| `run_classification(rows, seed=...)` | Binary label, participant IDs, numeric predictors | Baseline and logistic holdout metrics | Preprocessing trained only on training partition |
| `sha256_file(path)` | Existing file | SHA-256 string | Detects output changes, not clinical correctness |
| `create_manifest(root, files, seed=..., purpose=...)` | Synthetic output files within root | Provenance dictionary | Refuses external file paths |
| `research-template demo --plots --ml` | Installed optional extras | Complete synthetic artifact suite | Manifest indicates publication BLOCKED |
| `research-template audit --require-release` | Project scaffold | Nonzero exit until review | Prevents template default from posing as approved evidence |

**R:** install R and ggplot2 separately, then `source("R/research_plots.R")` and consult [R companion](../R/README.md). Use `rt_scatter()`, `rt_box()`, `rt_heatmap()`, `rt_save()` with explicit columns, labels and units.

Do not reuse the synthetic feature ranges, score thresholds or simulated labels as clinical reference values.
