# caret for reproducible biomedical machine learning (R)

**Author:** Paul Skeffington · **Prepared with OpenAI** · **Source review:** 2026-10-15  
**Scope:** Independently written methods and a runnable, invented-data example. Neither a clinical prediction study nor a reproducibility claim about upstream models.

## Evidence and software provenance

| Evidence | Verified primary reference | Correct interpretation and adoption |
| --- | --- | --- |
| Foundational paper | [Kuhn (2008), *Building Predictive Models in R Using the caret Package*, JSS 28(5)](https://doi.org/10.18637/jss.v028.i05) | Standardizes model interfaces, preprocessing, tuning and resampling; it does **not** validate a new biomedical prediction model |
| Version / rights | [CRAN caret package](https://CRAN.R-project.org/package=caret), observed **7.0-1** | Package requires installed R dependencies; GPL-2-or-GPL-3 package terms require a separate review before distributing modified package code. We **do not** vendor caret or model weights |
| Maintenance status | [Official caret repository](https://github.com/topepo/caret/) | Maintained for bug fixes, without plans for major new features; appropriate for existing caret workflows and learning, while [tidymodels](https://www.tidymodels.org/) is a potential alternative for new pipelines |
| Group and class splitting | [Caret data splitting](https://topepo.github.io/caret/data-splitting.html) | \`createDataPartition()\` stratifies rows by the supplied class; first reduce to one row **per subject**, then split by subject ID. \`groupKFold()\` keeps repeated observations together during CV; independently audit its row indices |
| Model fit / tuning | [Caret model training](https://topepo.github.io/caret/model-training-and-tuning.html) | \`train()\`, \`trainControl()\`, custom \`index\`, \`preProcess\`, \`classProbs\`, \`twoClassSummary\`. Fit imputation/normalization inside every analysis fold, never before the split |
| Corrected confusion interpretation | [Caret performance documentation](https://topepo.github.io/caret/measuring-performance.html) | \`confusionMatrix(data=pred, reference=truth, positive=...)\`. Sensitivity and predictive values depend on class definition; PPV/NPV depend on event prevalence |
| Class imbalance | [Caret subsampling guide](https://topepo.github.io/caret/subsampling-for-class-imbalances.html) | Any over/under-sampling belongs **inside each training resample**; never sample before partitioning, and never rebalance the final holdout |
| Prediction report | [TRIPOD+AI (2024)](https://doi.org/10.1136/bmj-2023-078378) and [PROBAST+AI (2025)](https://doi.org/10.1136/bmj-2024-082505) | Model-reporting completeness and risk-of-bias appraisal apply separately from software execution and clinical utility |

Citation for R manuscript methods: Kuhn, M. (2008). Building Predictive Models in R Using the caret Package. *Journal of Statistical Software*, 28(5), 1–26. https://doi.org/10.18637/jss.v028.i05. Report \`packageVersion("caret")\`, R version, dependent-model version, seed, split identifiers stored securely and package-environment manifest for any actual study.

## Coding contract

1. **Before any split:** Define target, index/decision time, expected prevalence, analysis unit (subject/encounter/specimen), cohort criteria, permitted predictors, and missingness policy. Never assume an external field's coding or units from its name.
2. **Holdout isolation:** Split by independent subject/site/time units as the question requires. Stratify using **one record per independent unit**, not raw visit rows. Preserve the subject-level train/test separation in repeated-measure datasets.
3. **Nested resampling integrity:** Use \`groupKFold()\` or explicit group-based \`index\` lists for model selection on the training partition. Record assessment sets and confirm **zero group overlap** per fold. For more extensive tuning or model comparison, use nested resampling or a separately locked test set.
4. **Preprocessing contract:** Imputation, centering, scaling, feature selection and class sampling must fit on analysis folds only. \`caret::train(preProcess=...)\` implements specified supported transformations with fold-local training. Do not compute medians, PCA, batch corrections or resampling adjustments using the final holdout.
5. **Outcome semantics:** Set both \`factor(levels=...)\` and \`positive=\` explicitly. \`caret::twoClassSummary\` treats its **first class level** as the event. A factor class called \`Impaired\` in this synthetic example is an artificial label, not a diagnosis.
6. **Holdout measurements:** Compare predicted labels with **holdout** references using \`caret::confusionMatrix(data = predicted, reference = observed, positive = "Impaired")\`. Report the **four cell counts**, sensitivity, specificity, PPV, NPV, balanced accuracy, class prevalence, AUROC and a proper score such as Brier when probabilities are available.
7. **Independent validation:** Training/resampling AUROC and untouched holdout AUROC are distinct. One internally held-out cohort cannot establish transportability across institutions, devices, calendar periods or populations. Confidence intervals should respect grouping and the planned estimand; do not treat correlated visits as independent subjects.
8. **Safe release:** Research prediction artifacts can retain training data, feature distributions or learned private signals. Do not commit real patient records, fitted models, cached features, identities, prediction logs or restricted results to a public repository.

## Runnable invented-data example

Install **optional dependencies** into your approved R environment (separately from loading the module):

~~~r
install.packages(c("caret", "pROC"))
~~~

The module itself has **no installs, no network calls and no source-time execution**. The invented demonstration generates 80 subjects with 3 observations each, splits independent subjects before modeling, and deliberately includes missing predictor values to test training-fold imputation.

~~~r
source("R/research_caret.R")
result <- run_synthetic_caret_example(seed = 711L)

print(result$fold_audit)           # Every fold: n_group_overlap = 0
print(result$confusion_matrix$table)
print(result$cross_validated_roc)  # CV on the training partition only
print(result$holdout_metrics)      # Untouched group-heldout classification metrics
stopifnot(result$n_shared_subjects == 0L)
stopifnot(result$scientific_release_status == "BLOCKED")
~~~

~~~bash
Rscript --vanilla R/tests/test_caret_workflow.R
~~~

The implementation uses base logistic regression (\`method="glm"\`) as a **transparent synthetic baseline**, not evidence that any model is appropriate for clinical implementation. ROC on training resamples is a cross-validation estimate, not test accuracy. The \`Impaired\`/ \`Control\` names describe fabricated classes only. Split/group identifiers are deliberately excluded from predictors; the outcome is fixed per simulated subject to make group separation auditable. It is not a longitudinal prognostic model. The raw \`model\` and \`predictions\` objects are retained in memory for local review; external data must be secured before similar code is adapted.

### Interpreting different confusion matrices

A very strong apparent training or cross-validation confusion matrix can coexist with materially worse **independent test** results. Compare the sample denominators and evaluation method first; do not average such matrices or reuse the test set to tune the threshold.

| Quantity | Definition for positive class | What to report |
| --- | --- | --- |
| Sensitivity (recall) | TP / (TP + FN) | Correctly identified events |
| Specificity | TN / (TN + FP) | Correctly identified non-events |
| PPV (precision) | TP / (TP + FP) | Depends on measured population prevalence |
| NPV | TN / (TN + FN) | Depends on measured population prevalence |
| Balanced accuracy | (Sensitivity + Specificity)/2 | Useful alongside event counts under imbalance |
| AUROC | Ranking discrimination across thresholds | Not calibration or net benefit |
| Brier score | Mean squared difference of event probability and 0/1 outcome | Probability error, affected by event prevalence |

Use \`classProbs=TRUE\` and the event-first factor to obtain consistent two-class ROC scoring. For actual biomedical inference, separately plan discrimination intervals, calibration intercept/slope/curve, decision consequence and subgroup analyses. \`confusionMatrix()\` offers a binomial accuracy interval, but a row-level interval is not generally valid for correlated repeated measurements without a cluster-aware design.

## Relationship to RAG

\`caret\` is a supervised training and evaluation interface, **not** a clinical document retriever or a generative language model. It may be used for deliberately defined **downstream classifiers** in an RAG evaluation study (e.g. labeled passage relevance or evidence-grounding review) only after group/doc family splits prevent contamination. Keep retrieval metrics (Recall@k, nDCG@k) and classification metrics distinct, and do not treat a classifier score as a citation-grounding verdict without independent annotation.

## Acceptance gates

- **C0** — Paper DOI, CRAN version and official package documentation verified: **PASS, bibliographic identity only**.
- **C1** — Original synthetic R example and negative controls: **implemented; CI verdict required**.
- **C2** — Group-disjoint holdout/folds, fold-local preprocessing, positive-class and test-denominator checks: **automated tests added; CI verdict required**.
- **C3** — External dataset, missingness, prevalence shift, calibration, cluster-aware intervals: **NOT EXECUTED**.
- **C4** — Privacy, rights, clinical oversight and deployment review: **BLOCKED**.

This is a portable, independently authored methods resource, not instructional content copied from any institution.
