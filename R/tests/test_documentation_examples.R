# Parse every complete R fenced snippet in the primary guides without executing
# study operations or invoking the internet. No new packages required.

documents <- c(
  "README.md",
  "R/README.md",
  "R/STYLE_GUIDE.md",
  "docs/FUNCTION_CALL_SHEET.md",
  "docs/CODING_CONVENTIONS.md",
  "docs/CARET_ALGORITHM_CATALOG.md",
  "docs/R_PROGRAMMING_MECHANICS.md"
)
n_blocks <- 0L
for (file in documents) {
  lines <- readLines(file, warn = FALSE)
  in_r_block <- FALSE
  script_lines <- character()
  for (line in lines) {
    if (!in_r_block && grepl("^(~{3}|\\x60{3})r[[:space:]]*$", line, perl = TRUE)) {
      in_r_block <- TRUE
      script_lines <- character()
      next
    }
    if (in_r_block && grepl("^(~{3}|\\x60{3})[[:space:]]*$", line, perl = TRUE)) {
      tryCatch(
        parse(text = paste(script_lines, collapse = "\n")),
        error = function(error) {
          stop(sprintf("Invalid R code in %s: %s", file, conditionMessage(error)))
        }
      )
      n_blocks <- n_blocks + 1L
      in_r_block <- FALSE
      next
    }
    if (in_r_block) script_lines <- c(script_lines, line)
  }
  stopifnot(!in_r_block)
}
stopifnot(n_blocks >= 5L)
cat(sprintf("R documentation syntax PASS: %d code blocks\n", n_blocks))
