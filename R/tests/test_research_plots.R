# Synthetic only; executable R plotting and negative-input checks.
source("R/research_plots.R")
source("R/synthetic_demo.R")
stopifnot(requireNamespace("ggplot2", quietly = TRUE))
d <- rt_make_synthetic(n = 90L, seed = 711L)
s <- rt_summary(d, "measurement_mg_dl", "mg/dL")
stopifnot(nrow(s) == 1L, s$n_total == 90L, s$n_missing > 0L)
g <- rt_summary_by(d, "measurement_mg_dl", "site", "mg/dL")
stopifnot(length(g) == 3L)

dict <- list(
  site = list(label = "Site", unit = "category",
              levels = c("North", "South", "West")),
  age_years = list(label = "Age", unit = "years"),
  measurement_mg_dl = list(label = "Synthetic measurement", unit = "mg/dL")
)
kit <- rt_kit(
  d, dict, study = "Synthetic", observation_unit = "simulated person",
  source = "rt_make_synthetic", status = "SYNTHETIC / DESCRIPTIVE ONLY"
)
plots <- list(
  rt_plot(kit, "hist", value = "age_years", bins = 10L),
  rt_plot(kit, "box", value = "measurement_mg_dl", group = "site"),
  rt_plot(kit, "violin", value = "measurement_mg_dl", group = "site"),
  rt_plot(kit, "scatter", x = "age_years", y = "measurement_mg_dl"),
  rt_plot(kit, "bar", group = "site"),
  rt_corr_heatmap(d, c("age_years", "measurement_mg_dl")),
  rt_heatmap(matrix(c(1, NA, 3, 4), nrow = 2),
             row_labels = c("g1", "g2"), col_labels = c("s1", "s2"),
             name = "Magnitude", unit = "unitless"),
  rt_heatmap(matrix(c(-1, NA, 1, 0), nrow = 2),
             row_labels = c("g1", "g2"), col_labels = c("s1", "s2"),
             name = "Signed", unit = "unitless", mode = "diverging", center = 0)
)
for (p in plots) {
  stopifnot(inherits(p, "ggplot"))
  stopifnot(length(ggplot2::ggplot_build(p)$data) >= 1L)
}
rt_save(plots[[1]], "artifacts/r_ci/test_plot.pdf")
stopifnot(file.exists("artifacts/r_ci/test_plot.pdf"))
fail <- try(rt_heatmap(
  matrix(c(-1, 0, 0, 1), nrow = 2),
  row_labels = c("g1", "g2"), col_labels = c("s1", "s2"),
  name = "Signed", unit = "unitless", mode = "diverging"
), silent = TRUE)
stopifnot(inherits(fail, "try-error"))
fail <- try(rt_axis_label("Measurement", ""), silent = TRUE)
stopifnot(inherits(fail, "try-error"))
cat("R figure gate: 8 chart calls, numeric summaries and negative tests PASS\n")
