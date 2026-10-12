# Contract gate for hash-pinned source import, entirely synthetic ST06/ST07/ST09.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_pam50_heatmaps.R")
source("R/research_pam50_sources.R")
stopifnot(requireNamespace("readr", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE))
profile <- rt_pam50_profile()
sub <- profile$subtype_order
n <- 21432L
id <- sprintf("SYNTHETIC_%05d", seq_len(n))
set.seed(711)
effect <- matrix(stats::rnorm(n * 4L), ncol = 4L)
colnames(effect) <- paste0("logFC_", sub)
full <- data.frame(gene_id = id, effect, check.names = FALSE)
chosen <- seq_len(60L)
st09 <- data.frame(
  gene_id = id[chosen],
  SYMBOL = sprintf("FakeMarker_%02d", chosen),
  anchor_subtype = rep(sub, each = 15L),
  anchor_rank = rep(seq_len(15L), 4L),
  selected_signature = rep(TRUE, 60L),
  full[chosen, paste0("logFC_", sub)],
  check.names = FALSE
)
st07 <- do.call(rbind, lapply(profile$contrasts, function(name) {
  ab <- strsplit(name, "_vs_", fixed = TRUE)[[1L]]
  data.frame(
    gene_id = id, contrast = name,
    first_subtype = ab[1], second_subtype = ab[2],
    logFC = full[[paste0("logFC_", ab[1])]] -
            full[[paste0("logFC_", ab[2])]],
    stringsAsFactors = FALSE
  )
}))
folder <- tempfile("pam50_source_contract_")
dir.create(folder)
paths <- file.path(folder, c("ST06.csv", "ST07.csv", "ST09.csv"))
names(paths) <- c("ST06", "ST07", "ST09")
utils::write.csv(full, paths["ST06"], row.names = FALSE)
utils::write.csv(st07, paths["ST07"], row.names = FALSE)
utils::write.csv(st09, paths["ST09"], row.names = FALSE)
hash <- vapply(paths, digest::digest, character(1), file = TRUE,
               algo = "sha256")
loaded <- rt_read_pam50_locked(paths["ST06"], paths["ST07"],
                               paths["ST09"], hash)
stopifnot(loaded$status == "HASH_MATCHED_FROZEN_DESCRIPTIVE_INPUTS",
          loaded$inference == "POST_SELECTION_DESCRIPTIVE_ONLY",
          nrow(loaded$signature) == 60L,
          nrow(loaded$selected_contrasts) == 360L,
          identical(dim(loaded$prepared$effects), c(60L, 4L)),
          identical(dim(loaded$prepared$contrasts), c(60L, 6L)))
expect_bad <- function(expr) {
  if (!inherits(try(expr, silent = TRUE), "try-error"))
    stop("Fail-closed source admission unexpectedly accepted damaged input.")
}
bad_hash <- hash
bad_hash["ST06"] <- paste(rep("0", 64), collapse = "")
expect_bad(rt_read_pam50_locked(paths["ST06"], paths["ST07"], paths["ST09"], bad_hash))
expect_bad(rt_read_pam50_locked(paths["ST06"], paths["ST07"], paths["ST09"], unname(hash)))
st07$logFC[1L] <- st07$logFC[1L] + 0.02
utils::write.csv(st07, paths["ST07"], row.names = FALSE)
expect_bad(rt_read_pam50_locked(paths["ST06"], paths["ST07"], paths["ST09"], hash))
hash["ST07"] <- digest::digest(paths["ST07"], file = TRUE, algo = "sha256")
# A fresh malicious source pin does not make a mismatched contrast valid.
# The modified gene is selected: the adapter checks direction against ST09.
expect_bad(rt_read_pam50_locked(paths["ST06"], paths["ST07"], paths["ST09"], hash))
unlink(folder, recursive = TRUE)
cat("Hash-pinned PAM50 source tests PASS: complete 21,432-gene ST06/ST07 universe and ST09 alignments\n")
