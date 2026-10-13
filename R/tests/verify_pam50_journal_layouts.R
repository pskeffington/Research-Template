# PRIVATE-only read-only preflight. Reads frozen export sidecars, not patient data.
# Author: Paul Skeffington. Prepared with OpenAI.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L || !dir.exists(args[[1L]]))
  stop("Pass exactly one validated private manuscript output directory.")
if (!requireNamespace("jsonlite", quietly = TRUE))
  stop("jsonlite required for journal plan provenance.")
root <- Sys.getenv("PAM50_TEMPLATE_ROOT", unset = ".")
source(file.path(root, "R", "research_pam50_journal_layouts.R"))
folder <- normalizePath(args[[1L]], mustWork = TRUE)
read_panel <- function(kind) {
  path <- file.path(folder, paste0("PAM50_", kind, ".metadata.json"))
  if (!file.exists(path)) stop("Missing frozen metadata sidecar.")
  jsonlite::fromJSON(path, simplifyVector = TRUE)
}
paired <- read_panel("paired_effects")
contrasts <- read_panel("six_contrasts")
ids_before <- paired$gene_order
breaks_before <- paired$color_breaks
plans <- lapply(names(rt_pam50_journal_presets()), function(id)
  rt_pam50_journal_layout(paired, contrasts, id))
names(plans) <- names(rt_pam50_journal_presets())
if (!identical(paired$gene_order, ids_before) ||
    !identical(paired$color_breaks, breaks_before) ||
    !all(vapply(plans, function(p)
      identical(p$status, "R_LAYOUT_PLAN_ONLY_NOT_RENDERED") &&
      identical(p$public_release, "BLOCKED") &&
      identical(p$scientific_estimates_recomputed, FALSE) &&
      identical(p$original_files_modified, FALSE) &&
      identical(p$total_review_pages, 4L) &&
      identical(p$shared_color_breaks, as.numeric(breaks_before)),
      logical(1))))
  stop("Frozen identifiers or scale changed during layout planning.")
out <- file.path(folder, "PAM50_JOURNAL_R_LAYOUT_PLANS.json")
if (file.exists(out)) stop("Refusing to overwrite a prior layout plan.")
report <- list(
  status = "REVIEW_ONLY_R_LAYOUT_SCENARIOS_VALIDATED",
  journal_selected = FALSE,
  figure_values_exported = FALSE,
  requires_proof_and_label_geometry_audit = TRUE,
  plans = plans,
  scientific_review = "PENDING",
  public_release = "BLOCKED")
jsonlite::write_json(report, out, auto_unbox = TRUE,
                     pretty = TRUE, null = "null")
cat("PRIVATE FROZEN R JOURNAL LAYOUT PLANS PASS; 4 scenarios, zero submission figures\n")
