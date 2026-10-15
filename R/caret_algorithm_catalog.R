# Independently authored caret model inventory; no source-time side effects.
# Official model metadata source: caret/man/models.Rd, pinned in the CSV.
# No models are trained, dependencies installed, data downloaded or files written here.

rt_validate_caret_algorithm_catalog <- function(catalog) {
  required <- c(
    "id", "method", "family", "name", "task", "implementation_packages",
    "tuning_parameters", "algorithm_mechanics", "biomedical_use_case",
    "preconditions", "limitation", "source_url", "upstream_revision",
    "bibliographic_status", "runtime_test_status"
  )
  if (!is.data.frame(catalog) || !identical(names(catalog), required) ||
      nrow(catalog) < 1L || anyDuplicated(catalog$id) ||
      anyDuplicated(catalog$method)) {
    stop("Caret algorithm catalog has invalid columns, IDs or model methods.")
  }
  needed <- setdiff(required, c("implementation_packages", "tuning_parameters"))
  if (anyNA(catalog) || any(vapply(catalog[needed], function(column) {
    any(!nzchar(trimws(as.character(column))))
  }, logical(1))) ||
      !all(catalog$task %in% c("classification", "regression", "both")) ||
      !all(catalog$bibliographic_status == "OFFICIAL_MODEL_MANUAL_CHECKED") ||
      !all(catalog$runtime_test_status == "CATALOG_ONLY_NOT_FITTED") ||
      any(!grepl("^https://github[.]com/topepo/caret/blob/", catalog$source_url)) ||
      any(!grepl("^[[:xdigit:]]{40}$", catalog$upstream_revision))) {
    stop("Caret catalog contains missing, malformed or overstated provenance.")
  }
  invisible(TRUE)
}

rt_read_caret_algorithm_catalog <- function(
    path = "references/CARET_MODEL_METHODS_2026-10-15.csv") {
  if (!is.character(path) || length(path) != 1L || is.na(path) ||
      !nzchar(path) || !file.exists(path)) {
    stop("Provide an explicitly available, local caret catalog CSV.")
  }
  catalog <- utils::read.csv(
    path, colClasses = "character", check.names = FALSE,
    stringsAsFactors = FALSE
  )
  rt_validate_caret_algorithm_catalog(catalog)
  catalog
}

rt_select_caret_algorithms <- function(catalog, task = NULL, family = NULL) {
  rt_validate_caret_algorithm_catalog(catalog)
  if (!is.null(task) && (length(task) != 1L ||
                        !task %in% c("classification", "regression"))) {
    stop("Choose a supported task or NULL.")
  }
  if (!is.null(family) && (length(family) != 1L || is.na(family) ||
                          !nzchar(family))) {
    stop("Choose a valid algorithm family or NULL.")
  }
  matching <- rep(TRUE, nrow(catalog))
  if (!is.null(task)) {
    matching <- matching & catalog$task %in% c(task, "both")
  }
  if (!is.null(family)) {
    matching <- matching & catalog$family == family
  }
  catalog[matching, , drop = FALSE]
}

rt_caret_runtime_metadata <- function(methods) {
  if (!requireNamespace("caret", quietly = TRUE)) {
    stop("Install the optional caret package to inspect its registered methods.")
  }
  if (!is.character(methods) || !length(methods) ||
      anyNA(methods) || any(!nzchar(methods)) || anyDuplicated(methods)) {
    stop("Choose unique, nonempty model method identifiers.")
  }
  records <- lapply(methods, function(method) {
    info <- tryCatch(
      caret::getModelInfo(method, regex = FALSE)[[method]],
      error = function(error) {
        stop(sprintf("Method not registered in caret: %s", method))
      }
    )
    if (is.null(info) || !is.data.frame(info$parameters) ||
        !("parameter" %in% names(info$parameters))) {
      stop(sprintf("Caret method %s lacks registered tuning metadata.", method))
    }
    tasks <- as.character(info$type)
    task <- if (all(c("Classification", "Regression") %in% tasks)) {
      "both"
    } else if ("Classification" %in% tasks) {
      "classification"
    } else if ("Regression" %in% tasks) {
      "regression"
    } else {
      stop(sprintf("Caret method %s has unexpected task type.", method))
    }
    packages <- if (is.null(info$library)) character() else as.character(info$library)
    data.frame(
      method = method, task = task,
      implementation_packages = paste(packages, collapse = ";"),
      tuning_parameters = paste(as.character(info$parameters$parameter),
                                collapse = ";"),
      supports_class_probabilities = !is.null(info$prob),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, records)
}

rt_audit_caret_algorithm_catalog <- function(catalog) {
  rt_validate_caret_algorithm_catalog(catalog)
  runtime <- rt_caret_runtime_metadata(catalog$method)
  index <- match(catalog$method, runtime$method)
  runtime <- runtime[index, , drop = FALSE]
  same_terms <- function(left, right) {
    left <- if (nzchar(left)) strsplit(left, ";", fixed = TRUE)[[1L]] else character()
    right <- if (nzchar(right)) strsplit(right, ";", fixed = TRUE)[[1L]] else character()
    setequal(left, right)
  }
  matching <- vapply(seq_len(nrow(catalog)), function(index) {
    identical(catalog$task[[index]], runtime$task[[index]]) &&
      same_terms(catalog$implementation_packages[[index]],
                 runtime$implementation_packages[[index]]) &&
      same_terms(catalog$tuning_parameters[[index]],
                 runtime$tuning_parameters[[index]])
  }, logical(1))
  # This is versioned metadata validation only; nothing has been fitted.
  list(
    status = if (all(matching)) "CATALOG_RUNTIME_METADATA_PASS" else "REVIEW_REQUIRED",
    scientific_release_status = "BLOCKED",
    caret_version = as.character(utils::packageVersion("caret")),
    inspected_methods = nrow(catalog),
    matching_methods = sum(matching),
    differences = catalog$method[!matching],
    runtime = runtime
  )
}

rt_check_caret_tuning_grid <- function(method, grid) {
  if (!is.data.frame(grid) || nrow(grid) < 1L ||
      anyNA(grid) || anyDuplicated(grid)) {
    stop("Tuning grid must be nonempty with no missing or repeated rows.")
  }
  details <- rt_caret_runtime_metadata(method)
  parameter_names <- details$tuning_parameters[[1L]]
  required <- if (nzchar(parameter_names)) {
    strsplit(parameter_names, ";", fixed = TRUE)[[1L]]
  } else {
    character()
  }
  if (!length(required) || !setequal(names(grid), required) ||
      any(vapply(grid, function(column) {
        !is.atomic(column) ||
          (is.numeric(column) && any(!is.finite(column)))
      }, logical(1)))) {
    stop("Tuning grid does not match the declared caret method parameters.")
  }
  invisible(TRUE)
}
