# Synthetic-only caret research benchmark; no patient data and no file writes.
source("R/research_caret.R")

synthetic <- make_synthetic_caret_cohort(n_subjects = 80L, visits = 3L,
                                          seed = 711L)
stopifnot(
  nrow(synthetic) == 240L,
  length(unique(synthetic$subject_id)) == 80L,
  identical(levels(synthetic$outcome), c("Impaired", "Control")),
  anyNA(synthetic$marker_beta),
  isTRUE(validate_caret_research_data(synthetic))
)

result <- run_grouped_caret_classifier(synthetic, seed = 711L)
stopifnot(
  result$status == "SYNTHETIC_DEMONSTRATION_ONLY",
  result$scientific_release_status == "BLOCKED",
  result$positive_class == "Impaired",
  result$n_shared_subjects == 0L,
  result$n_training_subjects + result$n_holdout_subjects == 80L,
  result$n_training_rows + result$n_holdout_rows == 240L,
  result$nrow == NULL,
  nrow(result$predictions) == result$n_holdout_rows,
  all(result$fold_audit$n_group_overlap == 0L),
  nrow(result$fold_audit) == 5L,
  length(result$predictor_names) == 2L,
  !("subject_id" %in% result$predictor_names),
  !("visit_index" %in% result$predictor_names),
  inherits(result$model, "train"),
  identical(result$confusion_matrix$positive, "Impaired"),
  all(names(result$holdout_metrics) == c(
    "accuracy", "sensitivity", "specificity", "ppv", "npv",
    "balanced_accuracy", "prevalence", "auroc", "brier"
  )),
  all(is.finite(result$holdout_metrics)),
  all(result$holdout_metrics >= 0),
  all(result$holdout_metrics <= 1),
  is.finite(result$cross_validated_roc)
)

# Holdout accuracy is not a resampling or training-set confusion matrix.
actual <- result$predictions$reference
forecast <- result$predictions$predicted
stopifnot(
  isTRUE(all.equal(
    unname(result$holdout_metrics["accuracy"]),
    mean(actual == forecast)
  )),
  sum(result$confusion_matrix$table) == result$n_holdout_rows,
  all(result$predictions$positive_probability >= 0),
  all(result$predictions$positive_probability <= 1)
)
rerun <- run_synthetic_caret_example(seed = 711L)
stopifnot(
  identical(result$fold_audit, rerun$fold_audit),
  isTRUE(all.equal(result$holdout_metrics, rerun$holdout_metrics)),
  isTRUE(all.equal(
    result$predictions$positive_probability,
    rerun$predictions$positive_probability
  ))
)

# Patient-level labels must be consistent across repeated visits.
conflicting <- synthetic
conflicting$outcome[2L] <- "Control"
stopifnot(inherits(
  try(validate_caret_research_data(conflicting), silent = TRUE),
  "try-error"
))

# Identifiers, outcome, and visits can never become unreviewed predictors.
stopifnot(inherits(
  try(validate_caret_research_data(
    synthetic, predictors = c("subject_id", "marker_alpha")
  ), silent = TRUE), "try-error"
))
stopifnot(inherits(
  try(validate_caret_research_data(
    synthetic, predictors = c("visit_index", "outcome")
  ), silent = TRUE), "try-error"
))

missing_group <- synthetic
missing_group$subject_id[1L] <- NA_character_
stopifnot(inherits(
  try(validate_caret_research_data(missing_group), silent = TRUE),
  "try-error"
))

all_missing <- synthetic
all_missing$marker_beta <- NA_real_
stopifnot(inherits(
  try(validate_caret_research_data(all_missing), silent = TRUE),
  "try-error"
))

wrong_order <- synthetic
wrong_order$outcome <- factor(wrong_order$outcome, levels = c("Control", "Impaired"))
stopifnot(inherits(
  try(validate_caret_research_data(wrong_order), silent = TRUE),
  "try-error"
))
stopifnot(inherits(
  try(run_grouped_caret_classifier(
    synthetic, holdout_fraction = 0
  ), silent = TRUE), "try-error"
))
stopifnot(inherits(
  try(run_grouped_caret_classifier(synthetic, n_folds = 1L),
      silent = TRUE), "try-error"
))

cat(sprintf(
  "caret PASS: 80 synthetic subjects, 5 group-disjoint CV folds, %d holdout rows, AUROC %.3f\n",
  result$n_holdout_rows, result$holdout_metrics["auroc"]
))
