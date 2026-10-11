# Audit every R file including newly added modules, not a fixed selection.
# Author: Paul Skeffington. Prepared with OpenAI.

r_files <- list.files("R", pattern = "\\.R$", recursive = TRUE, full.names = TRUE)
stopifnot(length(r_files) >= 7L)

# Reusable production modules must declare functions, never execute workflows,
# install packages, download data or write outputs when sourced.
is_safe_top_level <- function(expression, file) {
  if (!is.call(expression) || !identical(expression[[1L]], as.name("<-")) ||
      !is.symbol(expression[[2L]])) {
    return(FALSE)
  }
  if (is.call(expression[[3L]]) &&
      identical(expression[[3L]][[1L]], as.name("function"))) {
    return(TRUE)
  }
  identical(file, "R/synthetic_demo.R") &&
    identical(as.character(expression[[2L]]), "rt_make_synthetic") &&
    identical(as.character(expression[[3L]]), "make_synthetic_cohort")
}

for (file in r_files) {
  parsed <- parse(file = file, keep.source = TRUE)
  stopifnot(length(parsed) > 0L)
  code <- paste(readLines(file, warn = FALSE), collapse = "\n")

  if (!identical(file, "R/tests/test_style_contract.R")) {
    forbidden_syntax <- c(
      "%>%", "<<-", "\\bsetwd\\s*\\(", "\\binstall\\.packages\\s*\\(",
      "\\battach\\s*\\(", "\\blibrary\\s*\\(", "\\brequire\\s*\\(",
      "\\baes_string\\s*\\("
    )
    for (pattern in forbidden_syntax) {
      stopifnot(!grepl(pattern, code, perl = TRUE))
    }

    # Package verbs are always explicitly namespaced; do not implicitly attach
    # tidyverse symbols in scripts, tests or reusable plotting wrappers.
    unqualified_calls <- c(
      "ggplot", "aes", "geom_point", "geom_boxplot", "geom_histogram",
      "filter", "mutate", "select", "rename", "group_by", "summarise",
      "summarize", "pivot_longer", "pivot_wider", "left_join",
      "inner_join", "anti_join", "tibble"
    )
    for (function_name in unqualified_calls) {
      pattern <- paste0("(?<!:)(?<![[:alnum:]_])", function_name, "\\s*\\(")
      stopifnot(!grepl(pattern, code, perl = TRUE))
    }
  }

  function_lines <- grep(
    "^[[:space:]]*[[:alpha:]_][[:alnum:]_]*[[:space:]]*<-[[:space:]]*function\\s*\\(",
    readLines(file, warn = FALSE), value = TRUE, perl = TRUE
  )
  for (line in function_lines) {
    function_name <- sub(
      "^[[:space:]]*([[:alpha:]_][[:alnum:]_]*)[[:space:]]*<-.*$",
      "\\1", line
    )
    stopifnot(grepl("^[a-z][a-z0-9]*(_[a-z0-9]+)*$", function_name))
  }

  if (!grepl("^R/tests/", file)) {
    stopifnot(all(vapply(parsed, is_safe_top_level, logical(1), file = file)))
  }
}

tidy_source <- paste(readLines("R/research_tidy.R"), collapse = "\n")
plot_source <- paste(readLines("R/research_plots.R"), collapse = "\n")
example_source <- paste(readLines("R/example_tidy_workflow.R"), collapse = "\n")
for (call in c(
  "dplyr::group_by(", "dplyr::summarise(", "dplyr::anti_join(",
  "dplyr::left_join(", "tidyr::pivot_longer(", "tidyr::pivot_wider("
)) {
  stopifnot(grepl(call, tidy_source, fixed = TRUE))
}
stopifnot(
  grepl("ggplot2::ggplot(", plot_source, fixed = TRUE),
  grepl("tidyr::pivot_longer(", plot_source, fixed = TRUE),
  grepl("ggplot2::ggplot(", example_source, fixed = TRUE),
  grepl("|>", example_source, fixed = TRUE)
)
cat(sprintf(
  "R style PASS: %d files checked; namespaces, pipes and source-time boundaries\n",
  length(r_files)
))
