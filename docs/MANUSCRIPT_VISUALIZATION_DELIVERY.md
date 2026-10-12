# Manuscript visualization delivery contract

**Author:** Paul Skeffington · **Prepared with OpenAI**

Literature basis: [the public biomedical visualization evidence matrix](https://github.com/pskeffington/Dartmouth.HSE.Public/blob/main/06_RESOURCES/Literature/BIOSTAT_R_VISUALIZATION_EVIDENCE_MATRIX.md). Core principles: raw data visibility (Weissgerber 2015, 2019), uncertainty and estimation (Ho 2019; Kay 2024), defensible color encodings (Crameri 2020), heatmap annotations (Gu 2016, 2022), and transparent scientific-figure preparation (Jambor 2025). These are methodological references, **not** validation of a specific scientific result.

## Figure review and delivery

1. Preserve supplied variable names and letter case; never silently capitalize input.
2. State analysis unit (participant, specimen, cell), N included/excluded, missingness, transforms, units, group/order and figure legend.
3. Use accessible perceptually meaningful sequential scales for magnitudes, zero-centered diverging scales for signed data. Do not turn row-z scores into absolute gene-expression claims.
4. Violin plots include an internal median/quartile box. Whiskers are not confidence intervals. Keep sample size and independence explicit.
5. For heatmaps, freeze row/sample IDs and normalization orientation. For large matrices, consider ComplexHeatmap with documented clinical sample annotations, grouping by condition, separate annotation legends and missing-value color. Never cluster samples across conditions unless the method and interpretation justify it.
6. Do not generate p values, CIs, adjusted p values, ROC, PR, calibration or volcano significance annotations from descriptive-only effect data. Require an approved inferential result and independently verified model contract.
7. Export vector PDF for manuscript and 600 dpi PNG for previews. Check actual exported images at publication print size, labels, legend clipping, color accessibility, device/font embedding, scaling, and journal specifications. The exporter cannot certify those visually.
8. Private, restricted or PHI-bearing data cannot be approved for public release by the helper. Redact and perform independent human release approval.
9. Interactive Plotly can accompany the paper as a separate exploratory HTML artifact only; redact hover fields and apply deployment content security/privacy review. Never substitute interactive HTML for a vector manuscript panel.

## Runnable example (synthetic)

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/manuscript_delivery.R")
source("R/synthetic_demo.R")
cohort <- make_synthetic_cohort(n = 90L, seed = 711L)
p <- rt_violin(cohort, "site", "measurement_mg_dl",
               y_name = "Synthetic measurement", y_unit = "mg/dL",
               levels = c("North", "South", "West"))
rt_manuscript_export(
  p, "artifacts/manuscript/figure_01", figure_id = "Figure_01",
  legend = "Synthetic participant measurement by site; violin and internal box.",
  study = "Synthetic demonstration", data_status = "SYNTHETIC",
  analysis_unit = "simulated participant", source = "make_synthetic_cohort(seed=711)",
  n_analyzed = nrow(cohort), n_missing = 0L
)
```

The exporter writes a PDF, PNG, RDS sidecar and (when jsonlite is available) JSON sidecar. A PENDING review field remains until a human confirms image appearance, statistical validity and disclosure eligibility. No automatic publication, network traffic or package installation occurs.

## Optional packages

`plotly`/ `htmlwidgets` for an interactive *separate* deliverable; `ComplexHeatmap` and `circlize` for large genomic heatmaps; `ggdist` for uncertainty; `patchwork` for assembled panels; `ragg` for device consistency; `svglite` for editable vectors; `jsonlite` and `digest` for machine-readable sidecars and checksums. Declare exact installed versions in the analysis environment. Do not auto-install these packages.

## Interactive and condition-sorted examples

```r
source("R/research_interactive.R")
mat <- matrix(c(2, 1, 4, 3, 6, 5), nrow = 2)
p <- rt_heatmap_by_condition(
  mat, row_labels = c("Gene A", "Gene B"),
  col_labels = c("Sample A", "Sample B", "Sample C"),
  condition = c("Tumor", "Normal", "Tumor"),
  name = "Synthetic signed deviation", unit = "unitless",
  condition_levels = c("Normal", "Tumor"),
  mode = "diverging", center = 0
)
# Requires approved optional plotly and htmlwidgets packages.
interactive <- rt_interactive(p) # Defaults to no hover text.
rt_save_interactive(interactive, "artifacts/web/synthetic_heatmap.html",
                    data_status = "SYNTHETIC",
                    public_release_approved = FALSE)
```

This helper sorts samples by declared condition order and preserves original sample order within each condition unless `within_condition` is supplied. It does not perform clustering, differential testing or normalization. Plotly tooltip exposure is disabled by default; review hover content separately before any public release. HTML output includes a companion asset directory and is not a journal-ready static figure.

## Forest and volcano plot gates

Source `R/research_inference_plots.R` after the tidy and plots modules. `rt_verified_forest()` requires unique model terms, finite effect estimates, enclosing lower/upper interval bounds, interval level, units, model description, and reference group. Its zero-reference line assumes an additive or log-scale contrast; do not pass raw hazard ratios without an appropriate transformation. `rt_verified_volcano()` requires verified log2 effects and adjusted p values (not descriptive effects), a named contrast, modeling method, and multiple-testing adjustment. It displays adjusted p values of zero at a finite numerical floor.

Neither routine estimates missing inferential quantities. Release requires a separate provenance review of the fitting pipeline, effective sample size, estimand, confidence-interval method, comparison family, and threshold choices. Synthetic tests are at `R/tests/test_inference_plots.R`.


## Large-matrix ComplexHeatmap: grouped conditions and sample annotations

For gene-expression, assay, or biomarker matrices that need multi-track sample annotation and stable condition grouping, use `R/research_complex_heatmap.R`. This is **not a ggplot object**: it returns a ComplexHeatmap bundle rendered separately. Install the optional `ComplexHeatmap` and `circlize` packages in the approved R environment; the CI suite runs a small synthetic rendering test.

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_complex_heatmap.R")

# Rows are measured features; columns are precisely labeled samples.
mat <- matrix(c(-1, 2, NA, 4, 3, -3), nrow = 2,
              dimnames = list(c("Gene_A", "Gene_B"), c("T1", "N1", "T2")))
# The metadata rows may arrive in any order; IDs, not row position, govern joins.
samples <- data.frame(
  sample_id = c("T2", "T1", "N1"),
  condition = c("Tumor", "Tumor", "Normal"),
  subtype = c("LumA", "Basal", NA_character_)
)
bundle <- rt_complex_heatmap(
  mat, samples, condition_levels = c("Normal", "Tumor"),
  measurement = "Synthetic signed effect", unit = "log2 units",
  value_transform = "No additional transformation",
  mode = "diverging", center = 0,
  annotations = c("subtype"), rasterize = FALSE
)
stopifnot(identical(bundle$prepared$sample_order, c("N1", "T1", "T2")))
rt_export_complex_heatmap(
  bundle, "artifacts/manuscript/synthetic_heatmap",
  figure_id = "SyntheticHeatmap_01",
  legend = "Synthetic signed values; explicit condition and subtype tracks.",
  source = "Synthetic matrix; no patient records",
  data_status = "SYNTHETIC", width = 9, height = 7, dpi = 600
)
```

**Input/data contract:** Matrix dimensions, nonblank unique sample IDs and feature IDs, one-to-one sample metadata, complete condition labels, a caller-chosen full condition order, and finite numbers or explicit NA cells. Mismatched joins, duplicates, infinite values, undeclared condition levels, and undeclared / excessive annotation categories are rejected. Additional annotation tracks accept categorical values (up to eight categories per track), with missing values represented in gray. Condition levels, sample ordering, missing cells and annotations are recorded in the local provenance sidecar.

**Ordering:** Conditions are kept in the declared order without clustering column slices. Within each condition, the incoming matrix order is preserved, or sort explicitly by a metadata column through `within_condition = "timepoint"`. Rows and columns are *not clustered* by default; a manuscript seeking biological clustering needs a separately documented distance metric, normalization and stability/sensitivity study.

**Normalization:** No row z-scores, batch correction or model fitting are performed by the plotting wrapper. The `value_transform` field must explain upstream transformation; a signed quantity requires an explicit scientifically justified center. Sequential continuous values use a light-to-dark blue palette; signed deviations use blue–neutral–red; missingness is gray. Report row-wise versus global normalization in Methods, not just the caption.

**Scale and export:** The helper hides crowded row labels beyond 65 features and column labels beyond 45 samples unless explicitly overridden. The complete identifier/order metadata is kept in a local RDS sidecar that may itself be sensitive. Default `rasterize = FALSE` preserves vector heatmap cells in the manuscript PDF. Setting it to TRUE can make large exports manageable but **rasterizes the heatmap body** in PDF and must be disclosed. A 600-dpi PNG preview is also emitted. Neither output is automatically reviewed or deployed.

**Release gate:** Review annotation legends, grouping, missingness, all sample identifiers, panel clipping, publication-scale text, palette accessibility, data classification, PDF embedded fonts, output checksums and manuscript legend. If the sidecar contains sample IDs or subtype annotations, treat it with the same privacy controls as the underlying figure. An exported file is not permission to publish.

Primary documentation: [Gu et al. 2016](https://doi.org/10.1093/bioinformatics/btw313); [Gu 2022](https://doi.org/10.1002/imt2.43); [ComplexHeatmap Heatmap API](https://jokergoo.github.io/ComplexHeatmap/reference/Heatmap.html); [ComplexHeatmap split-order behavior](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html#order-of-slices).


## Synthetic figure-review gate and CI evidence

The automated QA routine lives in `R/research_figure_audit.R`; call
`rt_figure_audit("artifacts/manuscript/figure_01")` after a manuscript export.
It validates a nonempty single-page PDF, the exact figure size in points, PNG
width and height computed from inches and declared dpi, visible nonwhite
content, provenance and checksums, and embedded fonts where available. It
refuses blank, mismatched, unembedded-font or provenance-inconsistent outputs.

For reproducible **synthetic-only** regression examples, run:

```bash
Rscript --vanilla R/tests/generate_manuscript_review.R
Rscript --vanilla R/tests/test_plotly_export.R
```

The fixture suite exercises an internal-box violin, an inference-gated volcano
and a condition-grouped ComplexHeatmap. GitHub Actions tests these on a clean
runner and attaches a 14-day `synthetic-manuscript-review` artifact containing
PDF/PNG pairs, machine-readable provenance, audit results and a separate
non-self-contained Plotly HTML widget with its assets. Those reference
outputs are **not** patient data, and must not be confused with benchmark
clinical validity or scientific significance.

**Hard limitations:** Automated checks can detect a blank image, incorrect
page/pixel size, a missing or unembedded font, or a provenance mismatch.
They cannot establish annotation readability at journal column width,
color-vision accessibility, semantic interpretability, justified statistical
uncertainty, corrected multiple testing, or legal permission to publish.
Review every resulting figure visually, at final output size, before release.
All outputs remain `PENDING_VISUAL_AND_SCIENTIFIC_REVIEW`.

The audit uses the R `png` and `digest` packages plus Poppler
`pdfinfo`/`pdffonts`; all are explicitly installed in the figure CI job.
Optional Plotly requires both `plotly` and `htmlwidgets`, and the web
deliverable needs separate hover-field and disclosure review. No package
installation or I/O is performed when sourcing the reusable modules.


## Visual-review defects and adversarial export checks (October 2026)

The first synthetic reference export passed file-integrity checks, but rendered inspection found truncated captions/subtitles and a crowded, partially clipped ComplexHeatmap heading. The updated code wraps violin captions and volcano subtitles, places the unchanged heatmap measurement name in the title while retaining the full transformation in figure metadata, and separates the continuous heatmap legend below the panel from categorical annotation legends on the right. Check the **new** CI artifact visually rather than treating the earlier structural PASS as proof of typographic quality.

The CI gate also runs `R/tests/test_figure_audit_negative.R`: it requires rejection of absent PDF/PNG/metadata files, checksum mismatches or omissions, unreadable bytes, wrong PNG resolution, wholly white figures, wrong PDF page size, unembedded PDF fonts, heatmap sample-count inconsistency, restricted data marked public, and forged visual review status. Every synthetic comparison is isolated to temporary copied artifacts; production figures are not modified.

The audit requires both SHA-256 hashes and uses `digest` to verify them; exporters still permit missing optional digest, but such outputs are **not audit-admissible** until the approved environment includes it. CI success establishes the documented structural gates only. The image still requires a separate human review at its final print dimensions.


## TCGA-BRCA PAM50 frozen-research heatmaps (aligned adapter)

Use `R/research_pam50_heatmaps.R` when the columns are **subtype-level fitted effects**, not individual specimens. Do not route this matrix through the generic sample-condition heatmap: the four columns are four **model summaries** derived from 106 matched patients, not four patients or four raw RNA measurements. Frozen R11/R18/R19 research defines the research-specific contract:

| Figure | Strict orientation | Display order | Interpretation |
| --- | --- | --- | --- |
| PAM50 paired-effect signature | 60 frozen genes x 4 subtype effects (240 finite cells) | Basal, Her2, LumA, LumB | Tumor-minus-adjacent-normal log2 fold change within recorded tumor subtype |
| PAM50 planned contrasts | 60 frozen genes x 6 first-minus-second subtype effect contrasts (360 finite cells) | Basal_vs_LumA, Her2_vs_LumA, LumB_vs_LumA, Basal_vs_Her2, Basal_vs_LumB, Her2_vs_LumB | Difference of the two paired effects; not a raw tumor comparison |

The frozen source identifiers, anchors and ranks determine **all rows**. There are exactly 15 genes under each of Basal, Her2, LumA and LumB. Neither clustering nor new gene selection reorders them. Symbols are shown as entered; missing symbols fall back to gene IDs, and collisions receive identifying suffixes. The paired sample counts 16/9/59/22 (total 106 matched pairs) are annotated on the four-column figure. The separate primary discovery model contains 109 matched pairs; those 109 must **not** be attached to the formal subtype panels. The PAM50 *Normal* tumor classification is never displayed as a fifth normal-tissue subtype.

Color zero means no effect or no difference of effects. Blue means lower tumor expression relative to patient-matched adjacent normal (or a more negative first-minus-second effect). Red means the reverse. Both figures can share one symmetric color range, with separate unambiguous legend titles. The frozen gene anchors denote the largest paired effect, **not** which group has highest absolute tumor expression.

### Hash-pinned approved-local-input workflow

The reusable template never reads private data implicitly. The **three full R11 source tables** must match independently reviewed SHA-256 pins supplied by the operator. The loader will not silently downsample ST07 to 360 rows before checking that the complete 128,592-test contrast universe and its selected 360 rows align with ST06/ST09. A matching checksum is evidence of *identity against the supplied pin*, not independent proof of source authenticity.

~~~r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_pam50_heatmaps.R")
source("R/research_pam50_sources.R")
source("R/research_figure_audit.R")

# All three CSV files remain in the authorized private checkout.
files <- c(
  ST06 = "results/2026-09-30/R11_FROZEN/tables/ST06_PAM50_paired_effects.csv",
  ST07 = "results/2026-09-30/R11_FROZEN/tables/ST07_Six_planned_pairwise_tests.csv",
  ST09 = "results/2026-09-30/R11_FROZEN/tables/ST09_Frozen_60_gene_signature.csv"
)
# Replace these placeholders ONLY with source hashes reviewed in the
# private research repository; missing or invalid pins block execution.
approved_pins <- c(
  ST06 = "REPLACE_WITH_REVIEWED_ST06_SHA256",
  ST07 = "REPLACE_WITH_REVIEWED_ST07_SHA256",
  ST09 = "REPLACE_WITH_REVIEWED_ST09_SHA256"
)
locked <- rt_read_pam50_locked(
  files[["ST06"]], files[["ST07"]], files[["ST09"]],
  expected_sha256 = approved_pins
)
bundle <- rt_pam50_research_heatmaps(
  locked$signature, locked$selected_contrasts
)
rt_export_pam50_research(
  bundle, "artifacts/private_pam50_manuscript",
  source = "Private R11 ST06/ST07/ST09, hash matched to reviewed pins",
  data_status = "PRIVATE", width = 9, height = 13, dpi = 300
)
rt_figure_audit("artifacts/private_pam50_manuscript/PAM50_paired_effects")
rt_figure_audit("artifacts/private_pam50_manuscript/PAM50_six_contrasts")
~~~

After export, run the **on-device geometry review** (requires Poppler `pdftotext` and Python 3):

~~~bash
python3 scripts/audit_pam50_layout.py   artifacts/private_pam50_manuscript   --min-margin-pt 12 --check-labels
~~~

The geometry gate extracts actual vector PDF text bounding boxes, enforces a 12-point minimum perimeter clearance, confirms all 60 declared gene labels are present, checks both panels use identical frozen gene ordering and verified subtype denominators, and rejects mismatched color scales or contrast order. The research renderer applies 7 mm top/bottom and 6 mm left/right padding in the order `bottom, left, top, right`, consistent with ComplexHeatmap's documented plot padding convention. A geometry pass does not establish color accessibility, scientific validity, or final release permission. It cannot detect invisible semantic errors that an upstream source gate missed.

All real-data outputs, sidecars and geometry reports remain in the authorized **private** analysis environment. GitHub CI runs only synthetic 60-row and full 21,432-row input fixtures; it never ingests protected research datasets.

**Inferential boundary:** The R18 uncertainty/CI release gate remains blocked. These figures display historical point estimates, not confidence intervals, standard errors, patient distributions, or new inferential claims. The 60 genes are selected from this discovery cohort, so observed patterns are post-selection and not external validation. These are private manuscript derivatives until the source-specific release approval is complete.

**Export layout:** A 9 x 13 inch tall figure gives 60 gene labels, anchor blocks and category legends room to render. The PDF is vector; the PNG is 300 dpi by default. The figure metadata includes the actual gene order, anchor counts, color center/range, source, research interpretation status and source-side denominators. This provenance sidecar is private by default and must not be uploaded to public hosting without separate clearance.

**Research source-of-truth:** The private HSE research repository's `AI Enabled Research/scripts/113_r19_frozen_exchange.R`, `scripts/76_etl_r18_inputs.py`, `docs/R18A_UNCERTAINTY_METHOD_AUDIT_2026-10-10.md` and frozen ST06/ST07/ST09 tables govern this adapter. The public repository contains only reusable plotting code, schema expectations, and synthetic tests. CI generates no genuine patient or gene-result outputs.

**Legend refinement (2026-10-12).** The frozen PAM50 paired and contrast heatmaps use a centered, 98-mm horizontal continuous legend with a regular-weight 8.5-pt heading and 8-pt numeric ticks. Titles name the paired biological estimand and first-minus-second contrast, rather than showing an unexplained numerical scale. The limits continue to use the *full observed range* across both effect matrices; they are symmetric around zero and neither clipped, quantile-capped nor rescaled. The `scale_policy`, legend geometry, and complete color breaks are retained in the provenance sidecars. Near-neutral cells may look pale when a few effects approach the extremes; changing contrast would require a separately labeled, prospectively documented visualization sensitivity panel rather than silently changing the manuscript's main color encoding.


### Supplementary heatmap scale-distribution review

The principal 60×4 and 60×6 heatmaps retain the **shared full-range symmetric zero-centered** color scale. Extreme values may make many smaller effects look pale; the manuscript must not hide that with unannounced quantile clipping or ad hoc per-panel recoloring.

Use `R/research_pam50_scale_diagnostic.R` to generate a **separate supplementary descriptive distribution** for the two model-effect matrices. The diagnostic uses identical x-axis limits to the primary heatmaps, reports the signed minima, maxima, medians and 5th/95th percentiles, and marks the central portion of the *color scale* (default ±20% of the full absolute limit). These dashed markers are **display-scale references**, **not** clinical thresholds, FDR cutoffs or confidence intervals.

~~~r
source("R/research_pam50_scale_diagnostic.R")
source("R/manuscript_delivery.R")
scale_review <- rt_pam50_scale_diagnostic(bundle, neutral_fraction = 0.20)
print(scale_review$summary) # 240 paired effect cells and 360 contrast cells
rt_manuscript_export(
  scale_review$plot,
  "artifacts/private_pam50_manuscript/PAM50_scale_diagnostic",
  figure_id = "PAM50_Scale_Diagnostic",
  legend = "Distribution of the 240 subtype-effect and 360 planned-contrast cells; not patients.",
  study = "Frozen PAM50 discovery research",
  data_status = "PRIVATE",
  analysis_unit = "archived effect/contrast cell, not a patient",
  source = "Hash-matched R11 ST06/ST07/ST09 frozen estimates",
  n_analyzed = 600L, n_missing = 0L,
  inference = "DESCRIPTIVE_ONLY",
  width = 8, height = 7, dpi = 300L
)
rt_figure_audit("artifacts/private_pam50_manuscript/PAM50_scale_diagnostic")
~~~

**Reading the diagnostic:** Each bar counts fitted gene-by-subtype or gene-by-contrast *cells*; gene effects and contrasts are correlated and are not independent experimental replicates. Neither a sample-size distribution nor an uncertainty estimate is implied. The two facet counts differ by design (240 versus 360); do not compare bar heights as empirical patient frequencies. The printed `summary` provides the numerical fraction falling in the default near-neutral display band and must be retained in **private** research provenance. Source hashes and author approval remain separate.


### Caption completeness and on-page categorical key

The frozen 60-gene heatmap now displays a discrete **Gene anchor (15 each)** key to the left of the matrix, separate from the continuous effect legend below. The key names Basal, Her2, LumA and LumB directly, so readers need not interpret unexplained colored bars. Row labels and row grouping stay frozen; no re-clustering or reselection occurs. The color mapping remains the same for both effects and contrasts.

Each 9×13-inch output additionally creates a `PAM50_<kind>.caption.txt` file. The sidecar retains identical `manuscript_caption` text and the explicit `caption_review = PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW` state. The captions specify the study unit, 106 paired patient observations (16/9/59/22), 60 selected genes arranged as four 15-gene anchors, contrast direction, signed heatmap colors, zero midpoint, common scale, and post-selection descriptive-only interpretation. **They are drafts for author editing and journal word limits, not autogenerated journal approval.**

The Poppler geometry gate now requires the on-page anchor legend text and checks every full caption against its provenance sidecar. It refuses missing/stale captions or a forced approval state. Use the same private-data classification for the captions as for the figures: they describe unreleased research estimates and cannot be distributed merely because the plots contain no patient identifiers. Avoid using color alone to identify anchor groups, and inspect the exported PDFs at the actual intended manuscript column width.


### Internal spacing between subtype labels and heatmap legend (October 12 repair)

The earlier PDF exposed a **layout problem inside the figure**: the paired-subtype sample count line ended only about **0.9 pt** above the continuous bottom-legend heading, even though the external PDF margin audit had passed. Outer `draw(padding = ...)` regulates page-edge margins and **cannot** correct that internal collision.

The renderer now uses a temporary, locally restored `ComplexHeatmap::ht_opt(HEATMAP_LEGEND_PADDING = grid::unit(12, "mm"))` while drawing *each* PDF and PNG, together with `align_annotation_legend = "heatmap_top"` for the separate left-side gene anchor key. The 7/6/7/6-mm outer page padding is unchanged. The change creates dedicated whitespace below the four subtype labels, **not** a data transform, font reduction, altered gene ordering or taller paper size.

`scripts/audit_pam50_layout.py --min-footer-gap-pt 12` now measures actual PDF text bounding boxes and rejects the paired-effect PDF if the bottom legend title lies fewer than **12 pt** below the four `n=... pairs` labels. This is an independent inner-layout gate, in addition to the existing 12-pt PDF perimeter margin gate. Record the requested 12-mm internal separation and top-aligned anchor legend in the private figure sidecar; visual sign-off is still required.


### Independent rotated-contrast geometry regression

The `scripts/audit_pam50_layout.py` PDF validator now measures the true lower edge of vector heatmap cells against column-name glyph bounding boxes on **both** PAM50 figures. It expects exactly 240 vector cells and four unrotated labels for the paired-effect matrix, and exactly 360 vector cells and six approximately 35-degree rotated comparison labels for the contrast matrix. It rejects missing labels, missing cells, unknown figure modes, and any matrix-to-text clearance below **12 PDF points**.

The negative-control suite `scripts/tests/test_pam50_geometry.py` constructs **entirely synthetic vector PDFs** and demonstrates that deliberately overlapped layouts, missing labels, and missing heatmap cells are rejected, while properly spaced labels are accepted. No actual gene identifiers, frozen research bytes or private figures are included in those fixtures. Both panel checks are run in CI; an outer-page-margin pass is not sufficient to approve figure layout.

The corrected renderer retains a scoped 7-mm `DIMNAME_PADDING` to separate the heatmap body from column labels and 12-mm `HEATMAP_LEGEND_PADDING` to separate column labels from the bottom legend; the two settings address different gaps.


### Private manuscript review packet — explicit author decisions (October 2026)

After **both** real-data heatmaps, the descriptive scale supplement, the SHA-256 source admission and the PDF/vector geometry report have passed, run the standalone standard-library packet builder on the private artifact directory:

~~~bash
python3 scripts/build_pam50_review_packet.py /path/to/private/pam50-private-manuscript
~~~

It produces two **nonapproval** outputs: `PAM50_MANUSCRIPT_REVIEW.md` and `PAM50_REVIEW_PACKET.json`. The reviewer worksheet references the two caption files and vector PDFs, lists the measured subtype/contrast label clearances, and leaves the figure legibility, scientific interpretation, caption accuracy, privacy/distribution and journal-numbering checks **unchecked**. The JSON records `status = REVIEW_REQUIRED_NOT_APPROVED`, `merge_authorization = NOT_GRANTED`, and `public_release = BLOCKED`.

Admission is fail-closed: full ST06/ST07/ST09 source pins must be present in the **private validation result**; both panel SHA-256 digests must still match the locally exported PDF/PNG bytes; the 60-gene order, four anchored blocks, six first-minus-second contrasts, 106 formal paired patients, 109 primary-discovery pairs, unlabeled vs patient-level semantics, source scope, full symmetric scale and geometry pass must all remain consistent. The builder refuses missing captions, forged scientific/visual approval states, missing supplement evidence, modified figures or a preexisting packet. It does **not** independently retrieve clinical data or authenticate the original pin authority.

GitHub Actions' private figure job may generate this packet as a seven-day private review artifact. **Automated assembly must never check boxes, record approval, authorize publication or merge a PR.** Reviewer decisions belong to the human manuscript/research governance process; storing a completed worksheet is a separate controlled act. CI tests use fabricated miniature files and metadata, never protected genes, patient observations or genuine figures. External paired-cohort replication and uncertainty gates remain blocked.


### Post-assembly evidence verification

The unsigned private reviewer packet now records SHA-256 digests for the 14 exact input/figure/caption/sidecar/layout files and a digest for the worksheet. The check is reproducible on the downloaded, unmodified private artifact directory:

~~~bash
python3 scripts/build_pam50_review_packet.py --verify /path/to/private/pam50-private-manuscript
~~~

The verification command reconstructs the expected packet, checks each source/output hash and pending human-review state, and compares the worksheet byte-for-byte. Missing/altered files, checked-off worksheet boxes and forged release states fail closed. This is tamper detection against an independently retained reference, **not a cryptographic signature or independent certification**. If an attacker can replace the entire packet and all evidence, these internal checks alone cannot establish provenance; independently retain the GitHub Actions run, pinned commit SHAs and artifact digest. The verification command is read-only and does not sign, merge or distribute figures.
