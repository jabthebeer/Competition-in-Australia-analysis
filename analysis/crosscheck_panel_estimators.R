# Cross-check of the Python panel estimators (alicia.evaluate.panel) against the R reference packages.
#
# Forward plan (docs/forward_plan_macro_controls.md) §5.4: each new estimator must reproduce a reference
# case in R. The reference panel is synthetic (ILLUSTRATIVE, not real data), written with the Python
# estimates by alicia/analyses/panel_crosscheck/write_reference.py.
#
# Run from the repository root:  Rscript analysis/crosscheck_panel_estimators.R
# Packages: fixest, didimputation, fwildclusterboot, synthdid, gsynth, did, jsonlite (install with renv::install()).
# Not yet run: R is not installed in the environment where this script was written (18 Oct 2026).
#
# What must match:
#   - feols with three-way saturated fixed effects and with cell + period effects: coefficients to 1e-6,
#     cluster-robust standard errors to 1e-6 (relative), small-sample factor G/(G-1) only;
#   - the imputation estimator (Borusyak, Jaravel and Spiess): overall ATT and event-time effects to 1e-6;
#   - the restricted wild cluster bootstrap (Webb weights): p-values agree up to Monte Carlo error
#     (both use 9,999 draws, so within about 0.01);
#   - synthetic DiD, synthetic control and DiD (synthdid) on the first cohort: to 1e-6;
#   - generalised synthetic control with two factors (gsynth, no cross-validation): to 1e-4;
#   - Callaway-Sant'Anna with never-treated controls (did::att_gt, aggte simple and dynamic): to 1e-6.

suppressPackageStartupMessages({
  library(fixest)
  library(didimputation)
  library(fwildclusterboot)
  library(synthdid)
  library(gsynth)
  library(did)
  library(jsonlite)
})

d <- read.csv("analysis/crosscheck/panel_reference.csv")
py <- fromJSON("analysis/crosscheck/panel_reference_python.json")

# Small-sample adjustment G/(G-1) only. Argument names changed across fixest versions.
small <- if ("K.adj" %in% names(formals(fixest::ssc))) {
  fixest::ssc(K.adj = FALSE, G.adj = TRUE)
} else {
  fixest::ssc(adj = FALSE, cluster.adj = TRUE)
}

sat <- feols(y ~ D + x | state^industry + industry^period + state^period, d, cluster = ~state, ssc = small)
two <- feols(y ~ D + x | cell + period, d, cluster = ~state, ssc = small)

imp_sat <- did_imputation(d, yname = "y", gname = "gname", tname = "period1", idname = "cell",
                          first_stage = ~ x | state^industry + industry^period1 + state^period1)
imp_two <- did_imputation(d, yname = "y", gname = "gname", tname = "period1", idname = "cell",
                          first_stage = ~ x | cell + period1)
ev_sat <- did_imputation(d, yname = "y", gname = "gname", tname = "period1", idname = "cell",
                         first_stage = ~ x | state^industry + industry^period1 + state^period1, horizon = TRUE)

set.seed(1)
wb <- boottest(sat, param = "D", clustid = "state", B = 9999, type = "webb", impose_null = TRUE)

check <- function(label, r, p, tol, relative = FALSE) {
  diff <- if (relative) abs(r - p) / abs(p) else abs(r - p)
  data.frame(check = label, r = r, python = p, diff = diff, tol = tol, pass = diff <= tol)
}

# Synthetic-control family on the first cohort (controls first, treated cells last).
first <- py$synth_single_cohort
s1 <- subset(d, gname %in% c(0, 13))
Y <- as.matrix(reshape(s1[, c("cell", "period", "y")], idvar = "cell", timevar = "period", direction = "wide")[, -1])
rownames(Y) <- unique(s1$cell)
ord <- c(setdiff(rownames(Y), as.character(first$treated_cells)), as.character(first$treated_cells))
Y <- Y[ord, ]
N0 <- nrow(Y) - length(first$treated_cells)
T0 <- first$T0
sd_est <- c(sdid = c(synthdid_estimate(Y, N0, T0)), sc = c(sc_estimate(Y, N0, T0)), did = c(did_estimate(Y, N0, T0)))

s1$Dg <- as.numeric(s1$gname == 13 & s1$period1 >= 13)
gs <- gsynth(y ~ Dg, data = s1, index = c("cell", "period"), force = "two-way", CV = FALSE, r = 2, se = FALSE)

cs_r <- att_gt(yname = "y", tname = "period1", idname = "cell", gname = "gname", data = d,
               control_group = "nevertreated", est_method = "dr", bstrap = FALSE, cband = FALSE)
cs_simple <- aggte(cs_r, type = "simple", bstrap = FALSE)$overall.att
cs_dyn <- aggte(cs_r, type = "dynamic", bstrap = FALSE)
cs_dyn_r <- setNames(cs_dyn$att.egt, cs_dyn$egt)

ev_r <- setNames(ev_sat$estimate, ev_sat$term)
ev_terms <- intersect(names(ev_r), names(py$imputation_saturated$by_event))

out <- rbind(
  check("saturated: coef D", coef(sat)[["D"]], py$feols_saturated$coef$D, 1e-6),
  check("saturated: coef x", coef(sat)[["x"]], py$feols_saturated$coef$x, 1e-6),
  check("saturated: se D", se(sat)[["D"]], py$feols_saturated$se$D, 1e-6, relative = TRUE),
  check("saturated: se x", se(sat)[["x"]], py$feols_saturated$se$x, 1e-6, relative = TRUE),
  check("two-way: coef D", coef(two)[["D"]], py$feols_twoway$coef$D, 1e-6),
  check("two-way: se D", se(two)[["D"]], py$feols_twoway$se$D, 1e-6, relative = TRUE),
  check("imputation, saturated: ATT", imp_sat$estimate[1], py$imputation_saturated$att, 1e-6),
  check("imputation, two-way: ATT", imp_two$estimate[1], py$imputation_twoway$att, 1e-6),
  do.call(rbind, lapply(ev_terms, function(k)
    check(paste0("imputation, saturated: event ", k), ev_r[[k]], py$imputation_saturated$by_event[[k]], 1e-6))),
  check("wild cluster bootstrap: p-value", pval(wb), py$wild_cluster_bootstrap_saturated$p_value, 0.01),
  check("synthdid", sd_est[["sdid"]], first$sdid, 1e-6),
  check("synthetic control", sd_est[["sc"]], first$sc, 1e-6),
  check("DiD (synthdid)", sd_est[["did"]], first$did, 1e-6),
  check("gsynth, 2 factors", gs$att.avg, py$gsynth_single_cohort_r2$att, 1e-4),
  check("Callaway-Sant'Anna: simple", cs_simple, py$cs_never_treated$simple, 1e-6),
  do.call(rbind, lapply(intersect(names(cs_dyn_r), names(py$cs_never_treated$dynamic)), function(k)
    check(paste0("Callaway-Sant'Anna: event ", k), cs_dyn_r[[k]], py$cs_never_treated$dynamic[[k]], 1e-6)))
)
print(out, row.names = FALSE, digits = 8)
write_json(out, "analysis/crosscheck/panel_reference_r.json", digits = NA, pretty = TRUE)
if (!all(out$pass)) stop("cross-check failed: see the rows with pass = FALSE")
cat("All checks passed.\n")
