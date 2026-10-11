# Audit canonical R files without autoformatting or modifying them.
paths <- c(
  "R/research_tidy.R", "R/research_plots.R",
  "R/synthetic_demo.R", "R/example_tidy_workflow.R"
)
for (file in paths) {
  expression <- parse(file = file, keep.source = TRUE)
  stopifnot(length(expression) > 0L)
  source_code <- paste(readLines(file, warn = FALSE), collapse = "\n")
  banned <- c(
    "\\bsetwd\\s*\\(", "\\binstall\\.packages\\s*\\(",
    "\\battach\\s*\\(", "\\blibrary\\s*\\(", "<<-", "%>%"
  )
  for (pattern in banned) {
    stopifnot(!grepl(pattern, source_code, perl = TRUE))
  }
}
tidy_source <- paste(readLines("R/research_tidy.R"), collapse = "\n")
plot_source <- paste(readLines("R/research_plots.R"), collapse = "\n")
example_source <- paste(readLines("R/example_tidy_workflow.R"), collapse = "\n")
stopifnot(
  grepl("dplyr::group_by(", tidy_source, fixed = TRUE),
  grepl("dplyr::summarise(", tidy_source, fixed = TRUE),
  grepl("tidyr::pivot_longer(", tidy_source, fixed = TRUE),
  grepl("tidyr::pivot_wider(", tidy_source, fixed = TRUE),
  grepl("dplyr::anti_join(", tidy_source, fixed = TRUE),
  grepl("ggplot2::ggplot(", plot_source, fixed = TRUE),
  grepl("tidyr::pivot_longer(", plot_source, fixed = TRUE),
  grepl("ggplot2::ggplot(", example_source, fixed = TRUE),
  grepl("|>", example_source, fixed = TRUE)
)
cat("Style gate: parse, pipes, namespaces and no hidden side effects PASS\n")
