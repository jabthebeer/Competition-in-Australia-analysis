# Cross-check of the international benchmark engine (alicia.international.benchmark) in base R.
#
# Forward plan for international benchmarking (docs/forward_plan_international_benchmarking.md), phase P3: the
# benchmark statistics get an R cross-check. This script recomputes, from the same inputs and settings, every
# year's peer quartiles (type 7, R's default), median, mean and standard deviation, Australia's side of the range,
# the persistence and leave-one-out tests, the consistency of the window-average gap, and each comparison's status,
# and compares them with the Python results.
#
# Inputs (written by `alicia international benchmark`, in analysis/crosscheck/):
#   benchmark_inputs.csv          Australia and the core peers: country, group, measure, year, value, comparability
#   benchmark_settings.json       core peers, minimum peers a year, windows, years left out, rating levels
#   benchmark_years_python.csv    Python's statistics for each counted year
#   benchmark_summary_python.csv  Python's status for each group, measure and window
#
# Run from the repository root:  Rscript analysis/crosscheck_international_benchmarks.R
# Packages: jsonlite. What must match: every statistic to 1e-9, and every status exactly.

suppressPackageStartupMessages(library(jsonlite))

d <- read.csv("analysis/crosscheck/benchmark_inputs.csv", stringsAsFactors = FALSE)
cfg <- fromJSON("analysis/crosscheck/benchmark_settings.json")
py_years <- read.csv("analysis/crosscheck/benchmark_years_python.csv", stringsAsFactors = FALSE)
py_sum <- read.csv("analysis/crosscheck/benchmark_summary_python.csv", stringsAsFactors = FALSE)

core <- cfg$core
min_peers <- cfg$min_peers
levels_ <- cfg$levels

year_stats <- function(au, v) {
  q <- quantile(v, c(0.25, 0.5, 0.75), type = 7, names = FALSE)
  side <- if (au < q[1]) "below" else if (au > q[3]) "above" else "within"
  data.frame(au = au, median = q[2], q1 = q[1], q3 = q[3], mean = mean(v),
             sd = if (length(v) > 1) sd(v) else NA_real_, n_peers = length(v), side = side,
             stringsAsFactors = FALSE)
}

evaluate <- function(cell, peers, years, need) {
  out <- NULL
  for (y in years) {
    au <- cell$value[cell$country == "AUS" & cell$year == y]
    if (length(au) == 0) next
    v <- cell$value[cell$country %in% peers & cell$year == y]
    if (length(v) >= need) out <- rbind(out, cbind(year = y, year_stats(au, v)))
  }
  out
}

persistent <- function(sides) {
  if (length(sides) < 2) return(NA_character_)
  for (s in c("below", "above")) if (sum(sides == s) > length(sides) / 2) return(s)
  NA_character_
}

years_in <- function(cell, measure, lo, hi) {
  ys <- lo:hi
  if (!(measure %in% cfg$regulation)) ys <- setdiff(ys, cfg$exclude_years)
  sort(intersect(ys, unique(cell$year)))
}

r_years <- NULL
r_sum <- NULL
for (key in unique(paste(d$group, d$measure, sep = "|"))) {
  parts <- strsplit(key, "|", fixed = TRUE)[[1]]
  g <- parts[1]; m <- parts[2]
  cell <- d[d$group == g & d$measure == m, ]
  if (!("AUS" %in% cell$country)) next
  wins <- cfg$windows[[m]]
  for (w in names(wins)) {
    lohi <- wins[[w]]
    rows <- evaluate(cell, core, years_in(cell, m, lohi[1], lohi[2]), min_peers)
    n <- if (is.null(rows)) 0 else nrow(rows)
    if (n > 0) r_years <- rbind(r_years, cbind(group = g, measure = m, window = w, rows))
    side <- if (n > 0) persistent(rows$side) else NA_character_
    counted <- if (n > 0) rows$year else integer(0)
    loo_ok <- TRUE
    if (!is.na(side)) {
      for (p in core) {
        lr <- evaluate(cell, setdiff(core, p), counted, min_peers - 1)
        ls <- if (is.null(lr)) NA_character_ else persistent(lr$side)
        if (is.na(ls) || ls != side) loo_ok <- FALSE
      }
    }
    au_r <- cell$comparability[cell$country == "AUS" & cell$year %in% counted]
    rating <- if (length(au_r)) levels_[min(match(au_r, levels_))] else NA_character_
    gap <- if (n > 0) mean(rows$au - rows$median) else NA_real_
    status <- if (n < 2) {
      "too few years"
    } else if (is.na(side)) {
      if (all(rows$side == "within")) "within the range" else "outside, not persistent"
    } else if (gap * (if (side == "above") 1 else -1) <= 0) {
      "outside, average on the other side"
    } else if (!loo_ok) {
      "outside, fails leave-one-out"
    } else if (match(rating, levels_) < match("medium", levels_)) {
      "outside, low comparability"
    } else {
      "flag"
    }
    r_sum <- rbind(r_sum, data.frame(group = g, measure = m, window = w, years = n,
                                     side = ifelse(is.na(side), "", side), status = status,
                                     stringsAsFactors = FALSE))
  }
}

# Compare the yearly statistics
k <- function(x) paste(x$group, x$measure, x$window, x$year, sep = "|")
py_years$key <- k(py_years); r_years$key <- k(r_years)
stopifnot(setequal(py_years$key, r_years$key))
mm <- merge(py_years, r_years, by = "key", suffixes = c(".py", ".r"))
num <- c("au", "median", "q1", "q3", "mean", "sd")
worst <- max(sapply(num, function(v) max(abs(mm[[paste0(v, ".py")]] - mm[[paste0(v, ".r")]]), na.rm = TRUE)))
sides_ok <- all(mm$side.py == mm$side.r)

# Compare the statuses
py_sum$side[is.na(py_sum$side)] <- ""
ks <- function(x) paste(x$group, x$measure, x$window, sep = "|")
py_sum$key <- ks(py_sum); r_sum$key <- ks(r_sum)
stopifnot(setequal(py_sum$key, r_sum$key))
ms <- merge(py_sum, r_sum, by = "key", suffixes = c(".py", ".r"))
status_bad <- ms[ms$status.py != ms$status.r | ms$side.py != ms$side.r | ms$years.py != ms$years.r, ]

cat(sprintf("Years compared: %d; largest difference in any statistic: %.3g; sides identical: %s\n",
            nrow(mm), worst, sides_ok))
cat(sprintf("Comparisons: %d; statuses that differ: %d; flags: %d (R), %d (Python)\n",
            nrow(ms), nrow(status_bad), sum(r_sum$status == "flag"), sum(py_sum$status == "flag")))
if (nrow(status_bad) > 0) print(status_bad[, c("key", "status.py", "status.r")])
ok <- worst < 1e-9 && sides_ok && nrow(status_bad) == 0
cat(if (ok) "CROSS-CHECK PASSED\n" else "CROSS-CHECK FAILED\n")
quit(status = if (ok) 0 else 1)
