# Deterministic, fully synthetic reference figures for automated CI review.
# Author: Paul Skeffington. Prepared with OpenAI.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_inference_plots.R")
source("R/research_complex_heatmap.R")
source("R/manuscript_delivery.R")
source("R/research_figure_audit.R")
source("R/synthetic_demo.R")

out <- "artifacts/ci_figure_review"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
stopifnot(requireNamespace("jsonlite", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE),
          requireNamespace("ComplexHeatmap", quietly = TRUE),
          requireNamespace("circlize", quietly = TRUE))
cohort <- make_synthetic_cohort(n = 90L, seed = 711L)
figure <- rt_violin(cohort, "site", "measurement_mg_dl",
                    y_name = "Synthetic measurement", y_unit = "mg/dL",
                    levels = c("North", "South", "West"))
violin_stem <- file.path(out, "violin_with_box")
rt_manuscript_export(
  figure, violin_stem, figure_id = "Synthetic_Violin",
  legend = "Synthetic measurements by site; violin with internal box.",
  study = "Synthetic reference", data_status = "SYNTHETIC",
  analysis_unit = "simulated individual",
  source = "make_synthetic_cohort(n=90, seed=711)",
  n_analyzed = sum(!is.na(cohort$measurement_mg_dl)),
  n_missing = sum(is.na(cohort$measurement_mg_dl)),
  width = 7, height = 5, dpi = 300L
)

synthetic_de <- data.frame(
  gene = c("G1", "G2", "G3", "G4", "G5"),
  log2_fc = c(-2.1, -0.3, 1.7, 2.4, 0.15),
  adjusted_p = c(0.001, 0.8, 0.03, 0.0001, 0.99))
volcano <- rt_verified_volcano(
  synthetic_de, feature = "gene", log2_effect = "log2_fc",
  adjusted_p = "adjusted_p", contrast = "Synthetic groups",
  method = "Synthetic precomputed test outputs", adjustment = "BH")
volcano_stem <- file.path(out, "gated_volcano")
rt_manuscript_export(
  volcano, volcano_stem, figure_id = "Synthetic_Volcano",
  legend = "Synthetic effect and adjusted p values; no clinical inference.",
  study = "Synthetic reference", data_status = "SYNTHETIC",
  analysis_unit = "synthetic feature",
  source = "fixed illustrative model outputs, not observed data",
  n_analyzed = nrow(synthetic_de), n_missing = 0L,
  inference = "VERIFIED_INFERENTIAL_SYNTHETIC_ONLY",
  width = 7, height = 5, dpi = 300L
)

values <- matrix(c(-1, 2, NA, 4, 3, -3), nrow = 2,
                 dimnames = list(c("G1", "G2"), c("T1", "N1", "T2")))
samples <- data.frame(sample_id = c("T2", "T1", "N1"),
                      condition = c("Tumor", "Tumor", "Normal"),
                      subtype = c("LumA", "Basal", NA_character_))
ht <- rt_complex_heatmap(
  values, samples, condition_levels = c("Normal", "Tumor"),
  measurement = "Synthetic signed effect", unit = "log2 units",
  value_transform = "No further transformation",
  mode = "diverging", center = 0, annotations = "subtype")
heatmap_stem <- file.path(out, "condition_heatmap")
rt_export_complex_heatmap(
  ht, heatmap_stem, figure_id = "Synthetic_Heatmap",
  legend = "Synthetic features and condition-ordered sample annotations.",
  source = "small fixed synthetic matrix",
  data_status = "SYNTHETIC", width = 7, height = 5, dpi = 300L)

stems <- c(violin_stem, volcano_stem, heatmap_stem)
qa <- lapply(stems, rt_figure_audit)
names(qa) <- basename(stems)
stopifnot(all(vapply(qa, function(x)
  identical(x$automated_checks, "PASS") &&
  identical(x$visual_review, "PENDING") &&
  identical(x$scientific_review, "PENDING"), logical(1))))
jsonlite::write_json(qa, file.path(out, "automated_review.json"),
                     auto_unbox = TRUE, pretty = TRUE)
cat("Synthetic manuscript QA PASS: 3 PDF/PNG pairs, image content, fonts, dimensions and provenance\n")
