# R biomedical graph and summary calls

**Author: Paul Skeffington · Prepared with OpenAI**

R/ggplot2 are optional and installed separately. The scripts do not read identifiable records, install packages, or write artifacts on source. Source files from the repository root.

~~~r
source("R/research_plots.R")
source("R/synthetic_demo.R")
d <- rt_make_synthetic(n = 90L, seed = 711L)
dict <- list(
  site = list(label = "Site", unit = "category",
              levels = c("North", "South", "West")),
  age_years = list(label = "Age", unit = "years"),
  measurement_mg_dl = list(label = "Simulated measurement", unit = "mg/dL")
)
kit <- rt_kit(
  d, dict, study = "Synthetic cohort",
  observation_unit = "simulated person", source = "rt_make_synthetic()",
  status = "SYNTHETIC / DESCRIPTIVE ONLY"
)
numeric <- rt_summary(d, "measurement_mg_dl", "mg/dL")
grouped <- rt_summary_by(d, "measurement_mg_dl", "site", "mg/dL")
p <- rt_plot(kit, "hist", value = "measurement_mg_dl", bins = 12L)
rt_save(p, "artifacts/r/histogram.pdf")
p <- rt_plot(kit, "box", value = "measurement_mg_dl", group = "site")
rt_save(p, "artifacts/r/box.pdf")
p <- rt_plot(kit, "violin", value = "measurement_mg_dl", group = "site")
rt_save(p, "artifacts/r/violin.png")
p <- rt_plot(kit, "scatter", x = "age_years", y = "measurement_mg_dl")
rt_save(p, "artifacts/r/scatter.pdf")
p <- rt_plot(kit, "bar", group = "site")
rt_save(p, "artifacts/r/counts.pdf")
p <- rt_corr_heatmap(d, c("age_years", "measurement_mg_dl"))
rt_save(p, "artifacts/r/correlation.pdf")
p <- rt_heatmap(
  matrix(c(-1, 0, NA, 1), nrow = 2), c("G1", "G2"), c("S1", "S2"),
  name = "Synthetic signed measurement", unit = "unitless",
  mode = "diverging", center = 0
)
rt_save(p, "artifacts/r/heatmap.pdf")
~~~

All R figures use named axes and units, sample-size captions, Okabe–Ito categories, Viridis magnitude or explicitly centered diverging colors, and neutral gray for missing cells. `rt_summary` reports n measured/missing, mean, sample SD, median, quartiles, IQR and observed range. Statistical inference must separately follow a study-appropriate protocol.

Consult [the complete function-call sheet](../docs/FUNCTION_CALL_SHEET.md) and [figure standard](../docs/FIGURE_STANDARD.md) for Python equivalents, interpretations and export limits.
