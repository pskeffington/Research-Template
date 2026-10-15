# Algorithm reference: caret models, biomedical applicability and code gates

**Author:** Paul Skeffington · **Prepared with OpenAI**  
**Selective review:** 2026-10-15 · **Status:** verified software metadata, not a systematic review and not clinical-model reproduction.

## Scope and primary documentation

This catalog is an **independently authored, selective 20-method index** drawn from the official [caret Available Models index](https://topepo.github.io/caret/available-models.html) and the [package's versioned model manual](https://github.com/topepo/caret/blob/cf7bf44c27c66b88618f8050d3b112df40f48ef1/man/models.Rd) (source revision `cf7bf44c27c66b88618f8050d3b112df40f48ef1`). These methods are **options available through caret**, not 20 fitted or reproduced models. Exact installed package version and method definitions must be checked before a new study. The dated [machine-readable catalog](../references/CARET_MODEL_METHODS_2026-10-15.csv) retains families, task compatibility, upstream implementation packages, tuneable arguments, mathematical ideas, biomedical examples and limitations.

References: [Kuhn (2008), *Journal of Statistical Software*](https://doi.org/10.18637/jss.v028.i05), [CRAN caret package](https://CRAN.R-project.org/package=caret), [official training and tuning guide](https://topepo.github.io/caret/model-training-and-tuning.html), [data-splitting guide](https://topepo.github.io/caret/data-splitting.html), and [performance guidance](https://topepo.github.io/caret/measuring-performance.html). *caret* remains maintained for compatibility/bug fixes rather than new major features, so use the current version and consider [tidymodels](https://www.tidymodels.org/) for future-facing work rather than treating caret as the only R framework.

## Algorithm choice matrix

| Family / research purpose | Exact `train(method=...)` | Supported target | Key tuning arguments | Main gate |
| --- | --- | --- | --- | --- |
| Noninformative baseline | `null` | Classification + regression | None | Report majority/prevalence baseline, not clinical performance |
| Linear regression | `lm` | Regression | `intercept` | Continuous outcome; residual/model assumptions |
| Generalized linear / logistic baseline | `glm` | Classification + regression | None | Explicit `family=binomial()` for event classification |
| Ridge/LASSO/elastic-net | `glmnet` | Classification + regression | `alpha`, `lambda` | Training-fold standardization and correlated predictors |
| Linear/quadratic discriminant analysis | `lda`, `qda` | Classification | None | Class covariance rank and distribution assumptions |
| Interpretable tree | `rpart` | Classification + regression | `cp` | Pruning and tiny-leaf instability |
| Rule/tree learner | `C5.0` | Classification | `trials`, `model`, `winnow` | Rule and feature selection within training folds |
| Random forests | `rf`, `ranger` | Classification + regression | `mtry`; plus `splitrule`, `min.node.size` for ranger | Patient/site overlap and uncalibrated probabilities |
| Gradient boosting | `gbm`, `xgbTree` | Classification + regression | Iterations, depth, learning rate; see full matrix | Many tuning decisions increase overfit risk |
| Kernel SVM | `svmRadial` | Classification + regression | `sigma`, `C` | Scaling, probability-calibration review |
| Nearest neighbors | `knn` | Classification + regression | `k` | Distance units, scaling and dimensionality |
| Partial least squares | `pls` | Classification + regression | `ncomp` | Component count tuned without leakage |
| Principal component regression | `pcr` | Regression | `ncomp` | PCA fit inside each training fold |
| Shallow neural network | `nnet` | Classification + regression | `size`, `decay` | Model stochasticity, shrinkage and sample size |
| Naive Bayes | `naive_bayes` | Classification | `laplace`, `usekernel`, `adjust` | Correlated predictors and class priors |
| Adaptive regression splines | `earth` | Classification + regression | `nprune`, `degree` | Flexible knots/interactions require CV |
| Quantile random forest | `qrf` | Regression | `mtry` | Nominal prediction quantiles are not automatically calibrated intervals |

The pinned model manual explicitly identifies the extra implementation packages needed for each method. Some wrappers require optional libraries beyond `caret` itself (e.g., `glmnet`, `randomForest`, `ranger`, `xgboost`, `kernlab`, `naivebayes`, `quantregForest`). **Registering a method is not the same as installing that method's dependency**. Do not make the public template install or execute all implementations on import.

## Why algorithms differ

| Algorithm idea | Working concept | Researcher should inspect |
| --- | --- | --- |
| Logistic/generalized linear | Link a linear predictor to outcome expectation, e.g. binary event probability via logit | Label definition, linearity on link scale, separation, coefficient units |
| Penalized regression | Add L1/L2 penalties to reduce unstable coefficients in high-dimensional input | Penalty strength, standardization, feature stability, heldout calibration |
| Trees and ensembles | Recursive threshold partitions; forests aggregate trees; boosting updates learners sequentially | Resampling integrity, complexity, group dependence, variable-importance bias |
| SVM/kNN | Similarity or kernel-distance decision geometry | Covariate scales, distance drift, probability calibration |
| PCA/PLS | Reduce correlated variables into components; PLS also uses response association | Component meaning, train-only component selection |
| Neural models | Learn nonlinear weights and activations | Tuning scope, repeat seeds, runtime nondeterminism, external transfer |
| Probabilistic generative classifier | Combine class prior and feature conditional probabilities | Independence approximation, base rate, poorly calibrated scores |
| Quantile forest | Estimate conditional outcome distribution/quantiles rather than only the mean | Validated interval coverage, dependence, distribution shift |

Classification metrics describe event detection under a chosen threshold. Regression models require appropriately scaled MAE/RMSE/R² and uncertainty. Quantile estimates require coverage checks. **Never put clinically censored time-to-event outcomes into a naive binary classifier without explicitly redefining the scientific estimand and follow-up**; survival models and competing-risk designs require domain-appropriate methods.

## Discover model lists and inspect installed code

Use `getModelInfo()` for the registered implementation **list** (including libraries and tuning metadata), and `modelLookup()` for the public tuning/task table. See [modelLookup source and documentation](https://github.com/topepo/caret/blob/cf7bf44c27c66b88618f8050d3b112df40f48ef1/R/modelLookup.R). This is metadata inspection, **not training**.

~~~r
source("R/caret_algorithm_catalog.R")
registry <- rt_read_caret_algorithm_catalog()
classification <- rt_select_caret_algorithms(registry, task = "classification")
regularized <- rt_select_caret_algorithms(registry, family = "regularized-model")
metadata <- rt_caret_runtime_metadata(c("glm", "glmnet", "rpart"))
audit <- rt_audit_caret_algorithm_catalog(registry)

stopifnot(audit[["status"]] == "CATALOG_RUNTIME_METADATA_PASS")
stopifnot(audit[["scientific_release_status"]] == "BLOCKED")
print(metadata)
print(regularized[, c("method", "tuning_parameters", "implementation_packages")])
~~~

The helper will refuse to inspect a method if `caret` is absent, but **never installs anything**. The source catalog may still contain method wrappers whose optional implementation dependencies are unavailable. A successful metadata audit means the pinned method declarations match the installed `caret` registry, **not** that 20 models were fitted or could train without installing more packages.

For direct primary-package introspection:

~~~r
caret::modelLookup("glmnet")
method_spec <- caret::getModelInfo("glmnet", regex = FALSE)[["glmnet"]]
print(method_spec$parameters)
print(method_spec$library)
~~~

The registered model specification is a named **R list**. `[["glmnet"]]` extracts that specific component, while `["glmnet"]` would keep a one-element list. For the full explanation of vectors, lists, factor levels, formulas, indexing and predictable iteration, see [Essential R coding mechanics](R_PROGRAMMING_MECHANICS.md).

## Explicit hyperparameter grids

Never guess exact tuning field names: they vary by model and package version. Read `caret::modelLookup(method)` and compare against the source-locked matrix. This helper validates **argument structure** without fitting a model:

~~~r
source("R/caret_algorithm_catalog.R")
grid <- expand.grid(alpha = c(0, 0.5, 1),
                    lambda = c(0.001, 0.01, 0.1))
stopifnot(rt_check_caret_tuning_grid("glmnet", grid))
~~~

If an algorithm has no tuning parameters (e.g., `glm`), pass no artificial grid. The `expand.grid()` output is the Cartesian product of declared values; use it only when the training sample size and repeated-validation design support that workload. A broader grid does not constitute independent scientific replication.

## End-to-end machine-learning execution mechanics

```text
Define question / time / subject unit / outcome
  -> Record permitted predictor provenance and source dictionary
  -> Freeze independent subject/site/time holdout
  -> Select one or more interpretable baselines
  -> Make training-only grouped folds
  -> For each fold: fit imputation, transforms, feature selection and model
  -> Tune on CV / nested resamples, not on final holdout
  -> Refit on permitted training partition
  -> Evaluate only once on the locked test set
  -> Report confusion counts, class prevalence, discrimination,
     calibration, uncertainty and deployment limitations
  -> Preserve seed, R/package versions, code SHA and allowed output manifest
  -> GATE: requires human review before scientific or public use
```

For the **implemented** example, use [the grouped `caret` research workflow](CARET_RESEARCH_WORKFLOW.md), `R/research_caret.R`, and its regression tests. The 20-method registry is a separate **discovery layer**; it does not fit alternatives or make performance comparisons.

### Practical diagnostics

| Symptom | Likely checks |
| --- | --- |
| "Model is not in the set of existing models" | Exact `method` string and installed `caret` version; never silently substitute a different method |
| Model method recognized but fitting fails | The method's optional library, input types, missingness, and factors |
| CV AUROC strong but holdout sensitivity weak | Subject/site/time leakage, class prevalence, shift, untuned threshold, denominator |
| Train errors from `tuneGrid` | Expected names/types from `modelLookup()` and distinct configurations |
| Degenerate predictions or ROC missing | Single-class fold/holdout, wrong positive-class ordering, zero variance or separation |
| Numeric results vary across runs | Seeds, parallelism, RNG kind, package/BLAS/OS versions, resampling indices |
| "Importance" values appear causal | `varImp()` is often scaled or univariate and is not causal evidence |
| RAG question-accuracy substituted for clinical diagnosis | Separate retrieval/citation/answer scoring, human review, and clinical validation |

## Relation to biomedical AI/RAG

This model catalog covers **tabular supervised learning in R**, not biomedical document ingestion or LLM generation. [The separate biomedical RAG guide](BIOMEDICAL_AI_RAG_METHODS.md) catalogs lexical BM25, biomedical embeddings, reranking and citation-grounded answer evaluation. For RAG relevance classification, use a subject/document-family split; never tune a `caret` relevance model on the same families used for final retrieval evaluation.

## Release gate

- **A0 source identity:** 20 exact `train(method=...)` values and tuning names checked against pinned upstream manual.
- **A1 callable mechanics:** read, filter and inspect methods with explicit list/data-frame contracts. No model fitting.
- **A2 runtime metadata check:** CI must compare all 20 entries against installed `caret` model definitions.
- **A3 independent synthetic model comparison:** **NOT IMPLEMENTED** for these 20 alternatives; existing single-`glm` synthetic training example is separate.
- **A4 external cohort, subgroup and clinical appraisal:** **BLOCKED** pending approvals.

This index preserves the article/package's metadata as cited facts, while algorithms and explanatory text are written independently. Open source availability does not imply permission to redistribute a model's code, trained weights, or patient data.
