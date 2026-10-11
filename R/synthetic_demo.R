# Synthetic, non-clinical cohort. Original source, no external records.
# Author: Paul Skeffington. Prepared with OpenAI.
# Only sets RNG seed when called (no source-time state changes).

make_synthetic_cohort <- function(n = 90L, seed = 711L) {
  if (!is.numeric(n) || length(n) != 1L || !is.finite(n) ||
      n < 40L || n != floor(n)) {
    stop("n must be a whole number >= 40.", call. = FALSE)
  }
  if (!is.numeric(seed) || length(seed) != 1L || !is.finite(seed) ||
      seed < 0 || seed != floor(seed)) {
    stop("seed must be a nonnegative whole number.", call. = FALSE)
  }
  if (!requireNamespace("tibble", quietly = TRUE)) {
    stop("Install or restore tibble for the R research starter.", call. = FALSE)
  }
  set.seed(seed)
  age <- stats::runif(n, 22, 79)
  measurement <- 0.5 + stats::runif(n, 0, 1.2) + (age - 50) * 0.002
  age[seq(1L, n, by = 29L)] <- NA_real_
  measurement[seq(1L, n, by = 17L)] <- NA_real_
  tibble::tibble(
    participant_id = sprintf("SIM-R-%05d", seq_len(n)),
    site = rep(c("North", "South", "West"), length.out = n),
    age_years = age,
    measurement_mg_dl = measurement
  )
}

# Compatibility entry point for existing callers.
rt_make_synthetic <- make_synthetic_cohort
