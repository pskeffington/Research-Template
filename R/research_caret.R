# Independently authored, synthetic-first caret training reference.
# No data read, package install, model fit, or artifact write occurs on source().
# Primary references:
# https://doi.org/10.18637/jss.v028.i05
# https://topepo.github.io/caret/data-splitting.html
# https://topepo.github.io/caret/measuring-performance.html

make_synthetic_caret_cohort <- function(n_subjects = 80L, visits = 3L,
                                        seed = 711L) {
  if (length(n_subjects) != 1L || is.na(n_subjects) ||
      n_subjects < 40L || n_subjects != as.integer(n_subjects) ||
      length(visits) != 1L || is.na(visits) ||
      visits < 2L || visits != as.integer(visits)) {
    stop("Use at least 40 subjects and at least 2 visits per subject.")
  }
  set.seed(seed)
  subjects <- sprintf("SIM-%04d", seq_len(n_subjects))
  # Group outcomes are fictional and intentionally balanced at the subject level.
  group_outcome <- rep(c("Impaired", "Control"), length.out = n_subjects)
  subject_shift <- stats::rnorm(n_subjects, mean = 0, sd = 0.35)
  rows <- rep(seq_len(n_subjects), each = visits)
  n <- length(rows)
  data <- data.frame(
    subject_id = subjects[rows],
    visit_index = rep(seq_len(visits), times = n_subjects),
    outcome = factor(group_outcome[rows], levels = c("Impaired", "Control")),
    marker_alpha = ifelse(group_outcome[rows] == "Impaired", 0.65, -0.65) +
      subject_shift[rows] + stats::rnorm(n, sd = 0.95),
    marker_beta = ifelse(group_outcome[rows] == "Impaired", 0.25, -0.25) +
      stats::rnorm(n, sd = 1.1)
  )
  # Missingness is deliberately simulated to exercise fold-local imputation.
  data$marker_beta[seq(13L, n, by = 23L)] <- NA_real_
  data
}

validate_caret_research_data <- function(data, group_col = "subject_id",
                                         outcome_col = "outcome",
                                         predictors = c("marker_alpha", "marker_beta"),
                                         positive_class = "Impaired") {
  if (!is.data.frame(data) || nrow(data) == 0L ||
      length(predictors) < 1L || anyDuplicated(predictors)) {
    stop("Expected nonempty data frame and unique predictors.")
  }
  all_fields <- c(group_col, outcome_col, predictors)
  if (anyDuplicated(all_fields) || !all(all_fields %in% names(data))) {
    stop("Group, outcome and predictor fields must be present and distinct.")
  }
  group_id <- as.character(data[[group_col]])
  if (anyNA(group_id) || any(!nzchar(trimws(group_id)))) {
    stop("Group identifiers must be present and nonblank.")
  }
  outcome <- data[[outcome_col]]
  if (!is.factor(outcome) || nlevels(outcome) != 2L || anyNA(outcome) ||
      !identical(levels(outcome)[1L], positive_class) ||
      !identical(make.names(levels(outcome)), levels(outcome))) {
    stop("Outcome must be a nonmissing two-class factor with positive class first.")
  }
  group_labels <- split(as.character(outcome), group_id)
  if (any(vapply(group_labels, function(values) {
    length(unique(values)) != 1L
  }, logical(1)))) {
    stop("The same subject has contradictory class labels across visits.")
  }
  group_classes <- vapply(group_labels, function(values) values[1L], character(1))
  if (any(table(factor(group_classes, levels = levels(outcome))) < 12L)) {
    stop("At least 12 distinct subjects per outcome class are needed.")
  }
  for (field in predictors) {
    values <- data[[field]]
    if (!is.numeric(values) || all(is.na(values)) ||
        any(!is.finite(values[!is.na(values)]))) {
      stop(sprintf("Predictor %s must be numeric with finite observed values.", field))
    }
  }
  invisible(TRUE)
}

run_grouped_caret_classifier <- function(data, group_col = "subject_id",
                                          outcome_col = "outcome",
                                          predictors = c("marker_alpha", "marker_beta"),
                                          positive_class = "Impaired",
                                          holdout_fraction = 0.25,
                                          n_folds = 5L, seed = 711L) {
  if (!requireNamespace("caret", quietly = TRUE) ||
      !requireNamespace("pROC", quietly = TRUE)) {
    stop("The optional caret and pROC packages are required for this example.")
  }
  validate_caret_research_data(
    data, group_col, outcome_col, predictors, positive_class
  )
  if (length(holdout_fraction) != 1L || is.na(holdout_fraction) ||
      holdout_fraction <= 0 || holdout_fraction >= 0.5 ||
      length(n_folds) != 1L || is.na(n_folds) ||
      n_folds < 2L || n_folds != as.integer(n_folds)) {
    stop("Holdout fraction or cross-validation fold count is invalid.")
  }

  # Split unique subjects, not visits; preserve class prevalence across subjects.
  groups <- unique(data[, c(group_col, outcome_col), drop = FALSE])
  set.seed(seed)
  training_group_rows <- caret::createDataPartition(
    y = groups[[outcome_col]], p = 1 - holdout_fraction, list = TRUE
  )[[1L]]
  training_ids <- as.character(groups[[group_col]][training_group_rows])
  testing_ids <- setdiff(as.character(groups[[group_col]]), training_ids)
  train_data <- data[as.character(data[[group_col]]) %in% training_ids, ,
                     drop = FALSE]
  test_data <- data[as.character(data[[group_col]]) %in% testing_ids, ,
                    drop = FALSE]

  if (length(intersect(unique(train_data[[group_col]]),
                       unique(test_data[[group_col]]))) ||
      nrow(test_data) == 0L ||
      length(unique(test_data[[outcome_col]])) != 2L) {
    stop("Grouped holdout is empty, overlaps training or lacks an outcome class.")
  }

  # The caret groupKFold index contains TRAINING rows for each fold.
  # Index positions refer only to train_data; the final holdout is never tuned.
  set.seed(seed + 1L)
  indices <- caret::groupKFold(train_data[[group_col]], k = n_folds)
  fold_audit <- lapply(seq_along(indices), function(fold) {
    analysis_rows <- indices[[fold]]
    assessment_rows <- setdiff(seq_len(nrow(train_data)), analysis_rows)
    overlap <- intersect(
      unique(as.character(train_data[[group_col]][analysis_rows])),
      unique(as.character(train_data[[group_col]][assessment_rows]))
    )
    if (length(overlap) ||
        length(unique(train_data[[outcome_col]][analysis_rows])) != 2L ||
        length(unique(train_data[[outcome_col]][assessment_rows])) != 2L) {
      stop("Grouped cross-validation overlap or single-class fold detected.")
    }
    data.frame(
      fold = fold,
      n_analysis_rows = length(analysis_rows),
      n_assessment_rows = length(assessment_rows),
      n_group_overlap = length(overlap)
    )
  })
  fold_audit <- do.call(rbind, fold_audit)

  control <- caret::trainControl(
    method = "cv",
    number = n_folds,
    index = indices,
    classProbs = TRUE,
    summaryFunction = caret::twoClassSummary,
    savePredictions = "final",
    returnResamp = "final",
    allowParallel = FALSE
  )

  # All learned preprocessing occurs INSIDE train() and each training fold.
  # The subject ID and visit index are explicitly excluded as predictors.
  set.seed(seed + 2L)
  model <- caret::train(
    x = train_data[, predictors, drop = FALSE],
    y = train_data[[outcome_col]],
    method = "glm",
    family = stats::binomial(),
    preProcess = c("medianImpute", "center", "scale"),
    metric = "ROC",
    trControl = control
  )

  heldout_features <- test_data[, predictors, drop = FALSE]
  predicted <- predict(model, newdata = heldout_features, type = "raw")
  probabilities <- predict(model, newdata = heldout_features,
                           type = "prob")[[positive_class]]
  reference <- test_data[[outcome_col]]
  confusion <- caret::confusionMatrix(
    data = predicted, reference = reference, positive = positive_class
  )
  # pROC expects control class first, then positive case class.
  roc <- pROC::roc(
    response = reference,
    predictor = probabilities,
    levels = rev(levels(reference)),
    direction = "<",
    quiet = TRUE
  )
  by_class <- confusion$byClass
  scores <- c(
    accuracy = unname(confusion$overall["Accuracy"]),
    sensitivity = unname(by_class["Sensitivity"]),
    specificity = unname(by_class["Specificity"]),
    ppv = unname(by_class["Pos Pred Value"]),
    npv = unname(by_class["Neg Pred Value"]),
    balanced_accuracy = unname(by_class["Balanced Accuracy"]),
    prevalence = unname(by_class["Prevalence"]),
    auroc = as.numeric(pROC::auc(roc)),
    brier = mean((probabilities - as.numeric(reference == positive_class))^2)
  )

  list(
    status = "SYNTHETIC_DEMONSTRATION_ONLY",
    scientific_release_status = "BLOCKED",
    positive_class = positive_class,
    caret_version = as.character(utils::packageVersion("caret")),
    seed = seed,
    predictor_names = predictors,
    n_training_rows = nrow(train_data),
    n_holdout_rows = nrow(test_data),
    n_training_subjects = length(training_ids),
    n_holdout_subjects = length(testing_ids),
    n_shared_subjects = length(intersect(training_ids, testing_ids)),
    fold_audit = fold_audit,
    cross_validated_roc = mean(model$resample$ROC),
    holdout_metrics = scores,
    confusion_matrix = confusion,
    predictions = data.frame(
      reference = reference, predicted = predicted,
      positive_probability = probabilities
    ),
    model = model
  )
}

run_synthetic_caret_example <- function(seed = 711L) {
  data <- make_synthetic_caret_cohort(seed = seed)
  run_grouped_caret_classifier(data, seed = seed)
}
