source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_inference_plots.R")
if (all(vapply(c("ggplot2","dplyr","tidyr","tibble"), requireNamespace, logical(1), quietly=TRUE))) {
  dat <- data.frame(term=c("A","B"), estimate=c(0.4,-0.2), low=c(0.1,-0.5), high=c(0.7,0.1))
  p <- rt_verified_forest(dat,"term","estimate","low","high","log2 units",model_label="Synthetic",reference_label="Control")
  stopifnot(inherits(p,"ggplot"))
  dat$low[1] <- 0.8
  stopifnot(inherits(try(rt_verified_forest(dat,"term","estimate","low","high","log2 units",model_label="Synthetic",reference_label="Control"),silent=TRUE),"try-error"))
  de <- data.frame(gene=c("A","B"),lfc=c(-2,2),padj=c(0.01,0.03))
  stopifnot(inherits(rt_verified_volcano(de,"gene","lfc","padj","Synthetic contrast","Synthetic verified model"),"ggplot"))
  stopifnot(inherits(try(rt_verified_volcano(de[c("gene","lfc")],"gene","lfc","padj","Contrast","Model"),silent=TRUE),"try-error"))
}
