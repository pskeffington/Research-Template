# Essential R coding mechanics for biomedical modeling

**Author:** Paul Skeffington · **Prepared with OpenAI**  
**Primary-documentation review:** 2026-10-15. Independently written educational reference; examples use invented labels and values, not patient data.

## Primary language references and mechanical guarantees

- [Official R Language Definition](https://cran.r-project.org/doc/manuals/r-release/R-lang.html), [An Introduction to R](https://cran.r-project.org/doc/manuals/r-release/R-intro.html): lexical syntax, objects, factors, control flow, functions, and modeling.
- [Base R `list()` reference](https://stat.ethz.ch/R-manual/R-patched/RHOME/library/base/html/list.html): constructing heterogeneous recursive objects.
- [Base R extraction reference](https://stat.ethz.ch/R-manual/R-devel/library/base/html/Extract.html): `[`, `[[`, `$`, and `drop = FALSE` distinctions.
- [Base R `lapply()`/`vapply()`](https://www.stat.math.ethz.ch/R-manual/R-devel/library/base/html/lapply.html): iteration with list or type-checked output.
- [Base R factors](https://search.r-project.org/R/refmans/base/html/factor.html): explicit category levels and ordered categorical representations.
- [Caret available models and training rules](https://topepo.github.io/caret/available-models.html) and [training/tuning reference](https://topepo.github.io/caret/model-training-and-tuning.html).
- [Tidyverse coding style](https://style.tidyverse.org/) is an **engineering convention**, not R's language specification.

The project [R style contract](../R/STYLE_GUIDE.md), [coding conventions](CODING_CONVENTIONS.md), and [caret algorithm catalog](CARET_ALGORITHM_CATALOG.md) govern how these mechanics are used in research. R is case-sensitive, generally uses **one-based indexing**, and performs implicit coercion/recycling in some vector operations. Biomedical code must verify sizes, units and indices before inference.

## Object and algorithm primitives

| R object / operation | Minimal idiom | Meaning for scientific research | Typical failure to prevent |
| --- | --- | --- | --- |
| Atomic vector | `c(1.5, 2.5)` | Values of one common atomic type | Implicit numeric/character coercion |
| Integer / logical / missing | `1L`, `TRUE`, `NA_real_` | Typed counts, flags, unavailable continuous values | Treating `NA` as zero or as `NULL` |
| Factor | `factor(c("Case","Control"), levels=c("Case","Control"))` | Outcome class meaning and order | Wrong positive class after alphabetical sorting |
| Matrix | `matrix(1:6, nrow=2L)` | Homogeneous arrays, e.g. feature-by-sample assays | Accidental dimensions flipped or dropped |
| Data frame | `data.frame(subject_id=..., result=...)` | Named columns and row observations | Duplicate subject IDs or hidden unit-of-analysis changes |
| Named list | `list(method="glm", settings=list(seed=711L))` | Model specification, fold indices, audit report | Confusing list element with sublist |
| List subset | `plan["settings"]` | A **list** containing the named component | Passing a list where a scalar is required |
| Exact element | `plan[["settings"]]` | The stored component itself | Partial-matching ambiguity or wrong type |
| Fixed field | `plan$method` | Convenience extraction for a known literal name | Assuming dynamic `$` names are safe |
| Exact dynamic name | `plan[[key, exact=TRUE]]` | Variable-driven, exact match on an R list | Silent partial match/missing field |
| Explicit data frame shape | `x[, predictors, drop=FALSE]` | Preserve a data frame even with one selected predictor | Vector conversion breaks model interfaces |
| Named arguments | `mean(x, na.rm=TRUE)` | Explicit choice for missing values | Unintended NAs ignored without documentation |
| Typed iteration | `vapply(models, f, character(1))` | Stable type/length for each element | `sapply()` silently changing output shape |
| Index safety | `seq_len(nrow(x))` | Safe zero-length sequence and one-based row indices | `1:nrow(x)` creates `c(1,0)` for zero rows |
| Key checks | `anyDuplicated(ids)`, `setdiff()` | Stable one-to-one IDs and disjoint split sets | Repeated-person leakage across folds |
| Model formula | `outcome ~ marker_alpha + marker_beta` | Declares response and predictors | Including post-outcome, identity, or future features |
| Reproducibility | `set.seed(711L)`, `sessionInfo()` | Random sequence and environment documentation | Assuming a seed guarantees identical CPU/GPU outputs |
| Program error | `stop("Invalid input")` | Fail closed on invalid scientific data | Returning silently truncated or altered datasets |
| Unit test | `stopifnot(identical(actual, expected))` | Independent computational contract | Claiming a passing test proves clinical validity |

**Lists versus data frames:** a data frame is itself list-like, with equal-length columns. A model object returned by `caret::train()` is a more complex list/classed object; do not flatten it using `unlist()` and assume its heterogeneous components retain structure. Use narrow, named extraction, checks, and typed reporting interfaces.

## Runnable list and type mechanics (base R only)

~~~r
model_plan <- list(
  method = "glm",
  positive_class = "Impaired",
  predictors = c("marker_alpha", "marker_beta"),
  resampling = list(k = 5L, seed = 711L, unit = "subject")
)
stopifnot(is.list(model_plan["resampling"]))
stopifnot(is.list(model_plan[["resampling"]]))
stopifnot(identical(model_plan[["resampling"]][["k"]], 5L))
stopifnot(is.character(model_plan[["method"]]))
stopifnot(is.null(model_plan[["missing_key", exact = TRUE]]))

names(model_plan)                # Audit stored fields
str(model_plan)                  # Inspect data types and nested structure
vapply(model_plan[c("method", "positive_class")],
       is.character, logical(1)) # Guaranteed logical output
~~~

Do not use `if (x == NA)`; use `is.na(x)`. Distinguish `NULL` (absent object), `NA` (missing observation), `NaN` (undefined numeric result), and `Inf` (non-finite numeric value). Use `anyNA()`, `is.finite()`, and explicit categories in source dictionaries. Avoid `na.omit()` without an audited exclusion record.

## Numerical, factor and formula mechanics

~~~r
outcome <- factor(
  c("Impaired", "Control", "Impaired", "Control"),
  levels = c("Impaired", "Control")
)
stopifnot(identical(levels(outcome)[1L], "Impaired"))
x <- data.frame(
  marker_alpha = c(1.0, 0.4, 0.9, 0.1),
  marker_beta = c(2.1, NA_real_, 2.8, 0.6)
)
predictors <- c("marker_alpha", "marker_beta")
features <- x[, predictors, drop = FALSE]
stopifnot(is.data.frame(features), identical(ncol(features), 2L))
stopifnot(sum(is.na(features$marker_beta)) == 1L)

formula <- stats::as.formula("outcome ~ marker_alpha + marker_beta")
stopifnot(identical(all.vars(formula), c("outcome", predictors)))
~~~

*Study applicability:* `formula` objects can include transformations; if those transformations depend on learned statistics (such as imputation, centering, PCA, variable selection or batch harmonization), fit them **inside each training fold**. The factor's **first level** is the positive class for caret's two-class ROC summary; `confusionMatrix(positive=...)` must use the same label. Never infer whether an external binary variable means case/control, patient/encounter, or sex/gender solely from its name.

## Lists of subjects and group-aware fold indices

Caret's [data-splitting manual](https://topepo.github.io/caret/data-splitting.html) distinguishes rows from groups. Its `groupKFold()` returns a *named list of training-row index vectors*; each fold's validation indices must be the complement of that training set **inside the already separated training partition**. Subject IDs and outcomes must not leak via features.

~~~r
source("R/research_caret.R")
invented <- make_synthetic_caret_cohort(n_subjects = 80L, visits = 3L)
subject_ids <- unique(invented$subject_id)
stopifnot(length(subject_ids) == 80L)

# Minimal independent list mechanics, not the final caret fit:
fold_indices <- split(seq_along(subject_ids),
                      rep(1:5, length.out = length(subject_ids)))
stopifnot(is.list(fold_indices), length(fold_indices) == 5L)
for (fold in seq_along(fold_indices)) {
  testing_subjects <- subject_ids[fold_indices[[fold]]]
  training_subjects <- setdiff(subject_ids, testing_subjects)
  stopifnot(length(intersect(testing_subjects, training_subjects)) == 0L)
}
~~~

This illustrative index list is **not a randomized, class-stratified model CV plan**. Actual implemented grouping and class checks are in `run_grouped_caret_classifier()`; never substitute a list created by repeated *row* indices in place of independent subjects, or use the final test partition inside CV.

## Loops, functions, output type and error handling

~~~r
summarize_allowed <- function(values) {
  if (!is.numeric(values) || !length(values) ||
      any(!is.finite(values[!is.na(values)]))) {
    stop("Expected a numeric vector with finite observed values.")
  }
  c(observed = sum(!is.na(values)),
    missing = sum(is.na(values)),
    average = mean(values, na.rm = TRUE))
}
parts <- list(site_a = c(1, 2, NA_real_),
              site_b = c(3, 4, 5))
result <- lapply(parts, summarize_allowed)
observed <- vapply(result, function(item) item[["observed"]], numeric(1))
stopifnot(identical(as.numeric(observed), c(2, 3)))
~~~

`lapply()` preserves the list's length and named element structure; `vapply()` requires a declared return type and length. Use `for` loops for explicit stateful iteration when needed, but never rely on a hidden global working directory or implicitly captured mutable research context. Raise errors for wrong dimensions, nonnumeric laboratory values, identity mismatches, unsupported units and model configurations rather than dropping rows without documenting them.

## Model-discovery objects and algorithm mechanics in caret

The authoritative model registry is a **list of model specifications**, distinct from a fitted model. The algorithm names in the [20-method matrix](../references/CARET_MODEL_METHODS_2026-10-15.csv) are verified from the upstream model manual; they are **not** 20 reproduced models.

~~~r
source("R/caret_algorithm_catalog.R")
catalog <- rt_read_caret_algorithm_catalog()
linear <- rt_select_caret_algorithms(catalog, family = "linear-model")
info <- rt_caret_runtime_metadata(c("glm", "glmnet", "rpart"))
stopifnot(nrow(info) == 3L, linear$method[[1L]] == "lm")
audit <- rt_audit_caret_algorithm_catalog(catalog)
stopifnot(audit[["scientific_release_status"]] == "BLOCKED")
~~~

The package's `modelLookup()` enumerates parameters, classification/regression compatibility and whether class probabilities are supported. `getModelInfo()` gives the underlying named list, packages, tuning metadata and implementation functions. Neither invocation trains a model. If a model method exists but `train()` cannot run, inspect optional package dependencies and data types; do not automatically install packages from a script run or change the training method.

## Reproducibility and benchmark mechanics

| Stage | Required code-level behavior | Test |
| --- | --- | --- |
| Input | Verify schema, units, factor levels, predictor availability at index time | Reject unknown or duplicated keys |
| Time/identity split | Partition by patient, specimen, site or date *as design requires* | Zero overlap of independent units |
| Resampling | Use explicitly audited `trainControl(index = list(...))` | No overlap between fold analysis/assessment units |
| Preprocessing | Train-only scaling, imputation, feature selection and normalization | Corrupted holdout values cannot alter fitted preprocessing |
| Tuning | Model-specific named `tuneGrid`, deterministic seed and selected scoring rule | Reject missing, duplicated or wrong tuning columns |
| Outputs | Holdout confusion matrix, accuracy, sensitivity, specificity, PPV, NPV, balanced accuracy, AUROC and calibration | Denominators match untouched holdout |
| Provenance | Code commit SHA, R/package versions, seed, split and permissions manifest | No secrets or restricted identifiers in public logs |
| Release | Reviewer and separate scientific, source-license, privacy approvals | Fail closed by default |

### ML versus RAG algorithm boundaries

- **Supervised algorithms (`caret`):** learn from labeled target outcomes and quantify error against untouched labels.
- **Retrieval algorithms (BM25, dense nearest-neighbor search):** rank documents/passages against queries; evaluate source families, relevance judgments, Recall@k, MRR, nDCG, and evidence coverage.
- **Generative models (LLM/RAG):** produce candidate answers; independently test citation support, hallucinations, response abstention, clinical safety, and provenance.
- **Graph and multimodal pipelines:** add adjacency/tissue/image/clinical metadata contracts, graph edge leakage and data restrictions. Do not conflate good retrieval ranking with clinical answer safety.

Code for the synthetic BM25 retrieval baseline is in `src/research_template/retrieval_eval.py`; the grouped `caret` classifier is in `R/research_caret.R`. They test **different metrics** and are not claims about a real medical dataset.

## Source-integrity and usage boundary

No proprietary teaching material or upstream implementation has been copied into this page. Primary manuals are linked; example variable names are invented and have no real patient-level observations. Availability of an algorithm or package, or a successful synthetic CI fixture, does not establish statistical validity, clinical utility, model-weight rights, regulatory clearance or permission to move PHI to external services.
