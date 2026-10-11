# Full biomedical researcher function-call sheet

**R + tidyverse is the canonical biomedical coding style; Python remains supported.** Start with the [R style contract](../R/STYLE_GUIDE.md) and [runnable R workflow](../R/README.md). R code preserves source fields, normalizes internal analysis fields to snake_case, uses `dplyr`/`tidyr` pipelines, and shows `ggplot2` aesthetics, geoms and scales explicitly.

**Author: Paul Skeffington · Prepared with OpenAI**

The **minimum complete call** is a declared study and variable dictionary. Set labels, units, data class, observation unit, and categorical ordering once; subsequent calls supply missingness, denominators, captions, colors and export metadata automatically. All examples below use invented observations.

## Install and reproduce all examples

~~~bash
python -m pip install -e '.[all]'
pytest -q
research-template demo --out artifacts/full_gallery --n 120 --seed 711 --plots --ml
research-template audit --root .
~~~

The gallery produces nine scientific chart presets (each PNG + PDF + JSON trace), numeric/stratified summaries, synthetic CSV, ML baseline metrics and execution checksum manifest.

## 0. Canonical tidyverse, dplyr, tidyr and ggplot2 calls

The complete executable path is below. Each operation remains visible and returns either a tidy tibble or an editable ggplot object:

~~~r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
source("R/example_tidy_workflow.R")

result <- run_tidy_example(n = 90L, seed = 711L)
print(result$join_audit)
print(result$site_summary)

# A direct ggplot grammar example, layered after dplyr preparation.
observed_data <- result$analysis_ready |>
  dplyr::filter(!is.na(.data$measurement_mg_dl)) |>
  dplyr::mutate(site = factor(
    .data$site, levels = c("North", "South", "West")
  ))
p <- ggplot2::ggplot(
  observed_data,
  ggplot2::aes(x = .data$site, y = .data$measurement_mg_dl,
               fill = .data$site)
) +
  ggplot2::geom_boxplot(outlier.shape = NA, alpha = 0.75) +
  ggplot2::geom_point(
    position = ggplot2::position_jitter(width = 0.10, seed = 711),
    alpha = 0.45
  ) +
  ggplot2::scale_fill_manual(values = stats::setNames(
    rt_palette()[1:3], c("North", "South", "West")
  )) +
  ggplot2::labs(
    title = "Synthetic measurement by site",
    x = "Enrollment site (category)",
    y = "Simulated measurement (mg/dL)",
    caption = "Synthetic descriptive data; no clinical claim."
  ) +
  rt_theme()
rt_save(p, "artifacts/tidy/explicit_grammar.pdf")
~~~

Documented tidy data entry points: `rename_source_columns()`, `validate_join_keys()`, `join_research_tables()`, `pivot_measurements_longer()`, `pivot_measurements_wider()`, `summarize_measurements()`, and `summarize_missingness()`. Refer to [R/README.md](../R/README.md) for complete plot and statistics calls.

---

## 1. Set complete study context once

~~~python
from pathlib import Path
import matplotlib.pyplot as plt

from research_template.synthetic import make_cohort
from research_template.biomed import FigureKit, Variable, Study

rows = make_cohort(n=120, seed=711)
dictionary = {
    "site": Variable("Enrollment site", "category", kind="categorical",
                     levels=("North", "South", "West")),
    "age_years": Variable("Age", "years"),
    "measurement_mg_dl": Variable("Simulated measurement", "mg/dL"),
    "outcome": Variable("Simulated outcome", "unitless"),
}
study = Study(
    title="Synthetic methods demonstration",
    observation_unit="simulated person",
    source="make_cohort(n=120, seed=711)",
    status="SYNTHETIC / DESCRIPTIVE ONLY",
)
kit = FigureKit(rows, variables=dictionary, study=study)
destination = Path("artifacts/functions")
destination.mkdir(parents=True, exist_ok=True)
~~~

For real, permitted data, substitute the study title, source and every measurement definition. **Never reuse invented measurement ranges as clinical reference values.** In comparative studies define categorical levels intentionally to fix color mapping across subsets and panels.

## 2. Ready-made complete figure calls

Each code block below can follow the setup above without extra imports.

~~~python
# A. Numeric distribution: median line, mean/SD subtitle, n included/excluded
fig = kit.histogram("measurement_mg_dl", bins=12)
kit.save(fig, destination / "01_histogram")
plt.close(fig)

# B. Grouped boxplot: median, quartiles, measured n/group, categorical palette
fig = kit.box("measurement_mg_dl", group="site")
kit.save(fig, destination / "02_boxplot")
plt.close(fig)

# C. Violin plot: same dictionary, median and sample-size note
fig = kit.box("measurement_mg_dl", group="site", violin=True)
kit.save(fig, destination / "03_violin")
plt.close(fig)

# D. Scatter: complete pairs only; both axes labeled with units
fig = kit.scatter("age_years", "measurement_mg_dl")
kit.save(fig, destination / "04_scatter")
plt.close(fig)

# E. Grouped scatter: redundant shapes, labels, group denominators
fig = kit.scatter("age_years", "measurement_mg_dl", group="site")
kit.save(fig, destination / "05_grouped_scatter")
plt.close(fig)

# F. Category frequency: labeled bars and denominator disclosure
fig = kit.category_bar("site")
kit.save(fig, destination / "06_category_bar")
plt.close(fig)

# G. Variable missingness (%); missing does not mean zero
fig = kit.missingness("age_years", "measurement_mg_dl", "outcome")
kit.save(fig, destination / "07_missingness")
plt.close(fig)

# H. Pearson correlation matrix with every cell's own complete-pair n
fig = kit.correlation_heatmap("age_years", "measurement_mg_dl")
kit.save(fig, destination / "08_correlation")
plt.close(fig)

# I. Sequential heatmap: magnitude, Viridis + neutral missing cells
fig = FigureKit.matrix_heatmap(
    [[1.2, 2.0, 3.2], [2.1, None, 3.6], [3.0, 5.0, 7.0]],
    row_labels=["Gene A", "Gene B", "Gene C"],
    col_labels=["Sample 1", "Sample 2", "Sample 3"],
    name="Simulated expression magnitude", unit="arbitrary units",
    mode="sequential", study=study,
)
kit.save(fig, destination / "09_sequential_heatmap")
plt.close(fig)

# J. Diverging heatmap: requires an explicit meaningful scientific midpoint
fig = FigureKit.matrix_heatmap(
    [[-1.2, 0, 1.5], [0.8, None, -1.6], [2.0, -0.5, 0]],
    row_labels=["Gene A", "Gene B", "Gene C"],
    col_labels=["Sample 1", "Sample 2", "Sample 3"],
    name="Synthetic signed deviation", unit="unitless",
    mode="diverging", center=0, study=study,
)
kit.save(fig, destination / "10_diverging_heatmap",
         formats=("png", "pdf", "svg"), dpi=300)
plt.close(fig)
~~~

**Result of `kit.save`:** extension-free stem → 300 dpi PNG (where selected), PDF or SVG vector copy, and `.figure.json` with the title, variable units, study and source notes, denominators, palette, limitations and SHA-256 hashes. Export metadata are trace records, **not** peer-review approval.

## 3. Summary statistics: one-call and stand-alone

~~~python
from research_template.summary import (
    numeric_summary, category_summary, grouped_numeric_summary,
    complete_pair_summary,
)

all_stats = kit.summary("measurement_mg_dl")
site_stats = kit.summary("measurement_mg_dl", group="site")
single = numeric_summary(rows, "age_years", unit="years")
categories = category_summary(
    rows, "site", levels=("North", "South", "West")
)
strata = grouped_numeric_summary(
    rows, "measurement_mg_dl", "site", unit="mg/dL",
    levels=("North", "South", "West"),
)
pairs = complete_pair_summary(rows, "age_years", "measurement_mg_dl")
print(all_stats, site_stats, single, categories, strata, pairs)
~~~

| Field | Meaning |
| --- | --- |
| `n_total` | Every input row in this table |
| `n_measured`, `n_missing`, `percent_missing` | Observed finite values, explicitly absent values, percent excluded |
| `mean` and `sd` | Unweighted arithmetic mean and sample SD (n−1); SD is null for n below 2 |
| `median`, `q1`, `q3`, `iqr` | Median and 25th/75th quantiles (linear interpolation), interquartile range |
| `minimum`, `maximum` | Observed range; not clinical cutoffs |
| `groups` | Per-group counts and numeric summaries; undeclared categories rejected |
| `n_complete_pairs` | Number of complete *pairs*, not the two marginal n values |

Summary functions reject strings and nonfinite numeric values rather than silently coercing them; only explicit Python `None` marks absent numeric measurements.

## 4. Older direct-function calls remain supported

These are fully specified standalone alternatives when a schema-wide study object has not been defined. Prefer `FigureKit` for multi-panel studies.

~~~python
from research_template.plots import histogram, scatter, group_box, heatmap, save_figure

fig = histogram(rows, "age_years", name="Age", unit="years", bins=10)
save_figure(fig, destination / "legacy_age.png")
plt.close(fig)

fig = scatter(rows, "age_years", "measurement_mg_dl",
              x_name="Age", x_unit="years",
              y_name="Simulated measurement", y_unit="mg/dL")
save_figure(fig, destination / "legacy_scatter.pdf")
plt.close(fig)

fig = group_box(rows, "measurement_mg_dl", "site",
                name="Simulated measurement", unit="mg/dL")
save_figure(fig, destination / "legacy_box.svg")
plt.close(fig)

fig = heatmap([[-1, 0], [None, 1]],
              row_labels=["G1", "G2"], col_labels=["S1", "S2"],
              name="Synthetic signed signal", unit="unitless",
              mode="diverging", center=0)
save_figure(fig, destination / "legacy_heatmap.pdf")
plt.close(fig)
~~~

## 5. ML, quality, manifests

~~~python
from research_template.quality import validate_cohort
from research_template.ml import run_classification
from research_template.provenance import create_manifest, save_json, sha256_file

data_audit = validate_cohort(rows)
model_report = run_classification(rows, seed=711)
path = save_json(destination / "synthetic_metrics.json", model_report)
run_manifest = create_manifest(
    destination, [path], seed=711,
    purpose="Synthetic baseline ML methods demonstration",
)
save_json(destination / "run_manifest.json", run_manifest)
print(data_audit["missing_counts"], model_report["metrics"], sha256_file(path))
~~~

The demonstration compares a dummy majority-class baseline to a logistic model with **group-preserving holdout** and **train-only preprocessing**. It does not establish external validity, calibration, clinical usefulness or causal effects.

## 6. Full R equivalent calls (ggplot2 and tidyverse are optional)

~~~r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")

cohort <- rt_make_synthetic(n = 90L, seed = 711L)
dictionary <- list(
  site = list(label = "Site", unit = "category",
              levels = c("North", "South", "West")),
  age_years = list(label = "Age", unit = "years"),
  measurement_mg_dl = list(label = "Simulated measurement", unit = "mg/dL")
)
kit <- rt_kit(cohort, dictionary, study = "Synthetic methods",
              observation_unit = "simulated person",
              source = "rt_make_synthetic(seed=711)",
              status = "SYNTHETIC / DESCRIPTIVE ONLY")

summary <- summarize_measurements(cohort, "measurement_mg_dl", "mg/dL")
by_site <- summarize_measurements(cohort, "measurement_mg_dl", "mg/dL", by = "site")

p <- rt_plot(kit, "hist", value = "age_years", bins = 12L)
rt_save(p, "artifacts/r/hist.pdf")
p <- rt_plot(kit, "box", value = "measurement_mg_dl", group = "site")
rt_save(p, "artifacts/r/box.pdf")
p <- rt_plot(kit, "violin", value = "measurement_mg_dl", group = "site")
rt_save(p, "artifacts/r/violin.png")
p <- rt_plot(kit, "scatter", x = "age_years", y = "measurement_mg_dl")
rt_save(p, "artifacts/r/scatter.pdf")
p <- rt_plot(kit, "bar", group = "site")
rt_save(p, "artifacts/r/counts.pdf")
p <- rt_corr_heatmap(cohort, c("age_years", "measurement_mg_dl"))
rt_save(p, "artifacts/r/correlation.pdf")
p <- rt_heatmap(matrix(c(-1, 0, NA, 1), nrow = 2),
                row_labels = c("G1", "G2"), col_labels = c("S1", "S2"),
                name = "Signed expression", unit = "unitless",
                mode = "diverging", center = 0)
rt_save(p, "artifacts/r/signed_heatmap.pdf")
~~~

Full R details in [R companion](../R/README.md). R returns editable ggplot2 objects; its save function currently writes **the requested one format**, not the Python export JSON.

## 7. Additional scientific methods — references, not preinstalled wrappers

| Analysis | Standard method | Scientific prerequisite |
| --- | --- | --- |
| R unpaired two-group nonparametric | `stats::wilcox.test(value ~ group, data = clean)` | Independent units and two groups |
| R matched pairs | `stats::wilcox.test(before, after, paired = TRUE)` | Pair by true identifier before vectors are aligned |
| R multi-group omnibus | `stats::kruskal.test(value ~ group, data = clean)` | Independent groups and multiple-comparison plan |
| R multiple-testing correction | `stats::p.adjust(p_values, method = "BH")` | Define the comparison family |
| R linear regression | `stats::lm(outcome ~ predictor, data = clean)` | Check design, residuals, confounding and uncertainty |
| R expression-count modeling | `edgeR::glmQLFTest(...)` | Bioconductor, count-data design and justified contrasts |
| R genomic assay container | `SummarizedExperiment::SummarizedExperiment(...)` | Assay metadata and sample IDs aligned |
| Python production ML | `sklearn.pipeline.Pipeline(...)` | Prevent leakage in every resampling split |
| PyTorch networks | `torch.nn.Module` | Independent evaluation and hardware/seed documentation |

These methods are **not built into FigureKit**, and a runnable example is not inferential authorization. Start with [statistical workflow](STATISTICAL_WORKFLOW.md) and [release gates](RELEASE_GATES.md).

## 8. Graph selection guide

| Biomedical question | Minimal complete call |
| --- | --- |
| Distribution and sample size? | `kit.histogram("measurement_mg_dl")` |
| Means, SD, medians, IQR, and missingness? | `kit.summary("measurement_mg_dl")` |
| Grouped descriptive statistics? | `kit.summary("measurement_mg_dl", group="site")` |
| Two-group or multi-group visualization? | `kit.box("measurement_mg_dl", group="site")` |
| Associations with complete pairs? | `kit.scatter("age_years", "measurement_mg_dl")` |
| A categorical distribution? | `kit.category_bar("site")` |
| Missing values? | `kit.missingness("age_years", "measurement_mg_dl")` |
| Pairwise Pearson correlations? | `kit.correlation_heatmap("age_years", "measurement_mg_dl")` |
| Continuous molecular/assay magnitude? | `FigureKit.matrix_heatmap(..., mode="sequential", study=study)` |
| Signed expression z-score / centered deviation? | `FigureKit.matrix_heatmap(..., mode="diverging", center=0, study=study)` |

Real biomedical work requires documented units, denominators, dependence, sampling methods and human interpretation. A plot with full labels can still be scientifically wrong if the design is wrong.
