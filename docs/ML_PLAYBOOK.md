# Machine-learning research playbook

## Minimum gates

1. State target, prediction horizon, observation unit and allowed feature availability at prediction time. Identify potential leakage before splitting.
2. Hold participants, sites or time periods together across splits as the real design demands. The demo uses participant-group splitting; it is **not** a general guarantee of site/time transportability.
3. Fit imputation, encoding, scaling and feature selection **only** on training data, inside a pipeline. Never inspect a final holdout repeatedly while tuning.
4. Compare the candidate against a simple baseline under identical held-out samples and appropriate metrics. Examine prevalence, subgroup errors, discrimination and calibration.
5. Record software versions, seeds, preprocessing, sample counts, data rights, split IDs in secure storage and validation status. Separate cross-validation / bootstrap uncertainty from external validation.
6. Document deployment constraints, drift monitoring, model-update approval and rollback before exposing predictions to real users.

## Runnable synthetic baseline

```bash
python -m pip install -e '.[ml]'
research-template demo --out artifacts/ml --ml
```

Programmatic: `run_classification(make_cohort(n=240, seed=90), seed=90)`.

The included logistic baseline uses median imputation, standard scaling and model fitting only within training data. A `DummyClassifier` provides majority-class reference. AUROC is undefined for a holdout containing a single class, so the helper rejects that split rather than producing an invented score. This demonstration has **no clinical utility claim**.

## Algorithm discovery and R programming mechanics

Select supervised model families from the [20-method caret catalog](CARET_ALGORITHM_CATALOG.md) and use the [R programming mechanics reference](R_PROGRAMMING_MECHANICS.md) for lists, factors, formula declarations, typed iteration and safe resampling-index handling. The source-locked [method CSV](../references/CARET_MODEL_METHODS_2026-10-15.csv) distinguishes registered algorithms from tested implementations; `R/caret_algorithm_catalog.R` audits installed method metadata and tuning-grid names without fitting models. The goal is reproducible **choice and verification** of algorithms, not a claim that every model is suitable for every clinical question.

## Optional PyTorch

```bash
python -m pip install -e '.[torch,ml]'
python scripts/torch_demo.py
```

This CPU-only demonstration sets a seed and trains a tiny network with training-only preprocessing. It is optional because installing the PyTorch stack can be substantial; do not require it for every research project. Reproducibility can vary across platforms and PyTorch versions even with deterministic settings.

## Model review checklist

- [ ] Outcome/exposure definitions and index time documented
- [ ] Group/time/site dependence accounted for
- [ ] Train/validation/test purpose recorded
- [ ] No preprocessing on test observations
- [ ] Baseline compared on the same split
- [ ] Metric denominators, prevalence and uncertainty reported
- [ ] Calibration, subgroup analysis and external validation addressed
- [ ] Model artifact sensitivity and allowed publication reviewed

Relevant primary references: [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), [model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html), [TRIPOD+AI](https://doi.org/10.1136/bmj-2023-078378), [PROBAST+AI](https://doi.org/10.1136/bmj-2024-082505), [PyTorch reproducibility](https://pytorch.org/docs/stable/notes/randomness.html).

## Biomedical AI, RAG and foundation-model literature

Use the [dated biomedical AI/RAG evidence-to-code guide](BIOMEDICAL_AI_RAG_METHODS.md) with the [28-record source register](../references/BIOMEDICAL_AI_RAG_LITERATURE_2026-10-14.csv) when planning biomedical document retrieval, language-model evaluation, pathology ML, or single-cell/spatial modeling. The register labels verified publisher records separately from unverified candidate citations; no upstream implementation has been locally reproduced or licensed for redistribution in this pass. All clinical evaluation and data-release gates above remain in force.

## R caret: optional classification and regression training

Use the [caret coding and source guide](CARET_RESEARCH_WORKFLOW.md) and `R/research_caret.R` for an independently authored, synthetic repeated-subject classification example. The source review covers [Kuhn (2008)](https://doi.org/10.18637/jss.v028.i05) and official CRAN/caret references. Grouped holdout and grouped CV, fold-local preprocessing, class-level ordering, and untouched test-set confusion metrics are mandatory. `caret` is an optional maintenance-mode R package, not an RAG implementation. No clinical claim follows from the synthetic demonstration.
