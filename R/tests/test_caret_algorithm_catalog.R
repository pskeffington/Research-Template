# Synthetic/source-qualified caret method inventory and essential R list contracts.
# No actual classification model is fit here.
source("R/caret_algorithm_catalog.R")

catalog <- rt_read_caret_algorithm_catalog()
stopifnot(
  nrow(catalog) == 20L,
  identical(names(catalog), c(
    "id", "method", "family", "name", "task", "implementation_packages",
    "tuning_parameters", "algorithm_mechanics", "biomedical_use_case",
    "preconditions", "limitation", "source_url", "upstream_revision",
    "bibliographic_status", "runtime_test_status"
  )),
  !anyDuplicated(catalog$method),
  all(c("glm", "glmnet", "rf", "ranger", "xgbTree", "svmRadial",
        "naive_bayes", "qrf") %in% catalog$method),
  all(catalog$runtime_test_status == "CATALOG_ONLY_NOT_FITTED"),
  isTRUE(rt_validate_caret_algorithm_catalog(catalog))
)

class_models <- rt_select_caret_algorithms(catalog, task = "classification")
regression_models <- rt_select_caret_algorithms(catalog, task = "regression")
tree_models <- rt_select_caret_algorithms(catalog, family = "decision-tree")
stopifnot(
  nrow(class_models) >= 12L,
  nrow(regression_models) >= 12L,
  nrow(tree_models) == 2L,
  !("qrf" %in% class_models$method),
  "qrf" %in% regression_models$method,
  "glm" %in% class_models$method,
  "glm" %in% regression_models$method,
  nrow(rt_select_caret_algorithms(catalog, family = "unknown-family")) == 0L
)

audit <- rt_audit_caret_algorithm_catalog(catalog)
if (audit$status != "CATALOG_RUNTIME_METADATA_PASS") {
  for (method in audit$differences) {
    source_row <- catalog[catalog$method == method, , drop = FALSE]
    live_row <- audit$runtime[audit$runtime$method == method, , drop = FALSE]
    cat(sprintf(
      "METADATA_DIFFERENCE %s\n  task: %s / %s\n  packages: %s / %s\n  tuning: %s / %s\n",
      method, source_row$task, live_row$task,
      source_row$implementation_packages, live_row$implementation_packages,
      source_row$tuning_parameters, live_row$tuning_parameters
    ))
  }
}
stopifnot(
  is.list(audit),
  audit[["status"]] == "CATALOG_RUNTIME_METADATA_PASS",
  audit$scientific_release_status == "BLOCKED",
  audit$inspected_methods == 20L,
  audit$matching_methods == 20L,
  length(audit$differences) == 0L,
  is.data.frame(audit$runtime),
  identical(audit[["runtime"]]$method, catalog$method)
)

# Exact list extraction returns an element, not a one-member list.
stopifnot(is.character(audit[["status"]]), is.list(audit["status"]))
stopifnot(identical(audit[["status"]], audit$status))

# caret internally registers a non-tunable placeholder named "parameter"
# for a few legacy wrappers. Normalization must not invent hyperparameters.
untuned <- rt_caret_runtime_metadata(c("null", "glm", "lda", "qda"))
stopifnot(all(!nzchar(untuned$tuning_parameters)))

# Validate tuning names against the caret-registered model, with no model fitting.
grid <- data.frame(alpha = c(0.1, 0.5), lambda = c(0.01, 0.1))
stopifnot(isTRUE(rt_check_caret_tuning_grid("glmnet", grid)))
stopifnot(inherits(
  try(rt_check_caret_tuning_grid("glmnet", data.frame(alpha = 0.1)), silent = TRUE),
  "try-error"
))
stopifnot(inherits(
  try(rt_check_caret_tuning_grid("glmnet", data.frame(
    alpha = c(0.1, 0.1), lambda = c(0.1, 0.1)
  )), silent = TRUE), "try-error"
))
stopifnot(inherits(
  try(rt_check_caret_tuning_grid("glm", data.frame(random = 0.1)),
      silent = TRUE), "try-error"
))
stopifnot(inherits(
  try(rt_caret_runtime_metadata("unknown_method"), silent = TRUE), "try-error"
))
stopifnot(inherits(
  try(rt_select_caret_algorithms(catalog, task = "survival"), silent = TRUE),
  "try-error"
))
bad <- catalog
bad$method[2L] <- bad$method[1L]
stopifnot(inherits(
  try(rt_validate_caret_algorithm_catalog(bad), silent = TRUE), "try-error"
))
bad <- catalog
bad$runtime_test_status[1L] <- "CLINICALLY_VALIDATED"
stopifnot(inherits(
  try(rt_validate_caret_algorithm_catalog(bad), silent = TRUE), "try-error"
))
bad <- catalog
bad$id[1L] <- NA_character_
stopifnot(inherits(
  try(rt_validate_caret_algorithm_catalog(bad), silent = TRUE), "try-error"
))

cat(sprintf(
  "caret model catalog PASS: %d pinned entries, %d runtime matches, no model fits\n",
  nrow(catalog), audit$matching_methods
))
