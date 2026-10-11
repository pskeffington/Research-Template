# Independent synthetic dataset; no real observations.
rt_make_synthetic <- function(n = 90L, seed = 711L) {
  if (length(n) != 1L || !is.finite(n) || n < 40 ||
      n != as.integer(n)) stop("n must be an integer >= 40.")
  set.seed(seed)
  age <- stats::runif(n, 22, 79)
  measurement <- 0.5 + stats::runif(n, 0, 1.2) + (age - 50) * 0.002
  age[seq(1, n, by = 29)] <- NA_real_
  measurement[seq(1, n, by = 17)] <- NA_real_
  data.frame(participant_id = sprintf("SIM-R-%05d", seq_len(n)),
             site = rep(c("North", "South", "West"), length.out = n),
             age_years = age, measurement_mg_dl = measurement)
}
