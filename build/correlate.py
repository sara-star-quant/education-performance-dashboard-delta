#!/usr/bin/env python3
"""Controlled, observational correlation: do feature tags associate with faster
EPI / rankings gains?

For each binary feature tag (country level), report:
  - descriptive: Pearson/point-biserial r with the 5y outcome, n
  - controlled : OLS  outcome ~ tag + log(gdp_pc) + rd_pct_gdp + log(size) + base_rank
                 -> coefficient, 95% CI, p (normal approx), n, model R^2

Association, NEVER causation. Missing values are dropped listwise (no imputation).
A multiple-comparisons caveat is attached. Pure standard library (no numpy).

Writes results into snapshot["correlation"] and enriches universal_approach.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAP = os.path.join(ROOT, "docs", "data", "snapshots", "2026Q3.json")
OUTCOME_WINDOW = "5"


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def matinv(a):
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [x / pv for x in m[col]]
        for r in range(n):
            if r != col:
                f = m[r][col]
                m[r] = [a_ - f * b_ for a_, b_ in zip(m[r], m[col])]
    return [row[n:] for row in m]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
            for i in range(len(a))]


def ols(y, X):
    """y: n list; X: n x k (includes intercept). Returns dict per column."""
    n, k = len(y), len(X[0])
    Xt = [[X[i][j] for i in range(n)] for j in range(k)]
    XtX = [[sum(Xt[i][t] * Xt[j][t] for t in range(n)) for j in range(k)] for i in range(k)]
    XtY = [sum(Xt[i][t] * y[t] for t in range(n)) for i in range(k)]
    inv = matinv(XtX)
    beta = [sum(inv[i][j] * XtY[j] for j in range(k)) for i in range(k)]
    yhat = [sum(X[t][j] * beta[j] for j in range(k)) for t in range(n)]
    resid = [y[t] - yhat[t] for t in range(n)]
    rss = sum(e * e for e in resid)
    ybar = sum(y) / n
    tss = sum((v - ybar) ** 2 for v in y) or 1e-12
    dof = max(n - k, 1)
    sigma2 = rss / dof
    se = [math.sqrt(max(sigma2 * inv[i][i], 0)) for i in range(k)]
    return {"beta": beta, "se": se, "r2": 1 - rss / tss, "n": n, "dof": dof}


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def main():
    with open(SNAP) as f:
        snap = json.load(f)
    countries = snap["countries"]

    # gather all boolean tag keys
    tagkeys = set()
    for c in countries:
        for k, v in c["tags"].items():
            if isinstance(v, dict) and isinstance(v.get("value"), bool):
                tagkeys.add(k)
    tagkeys = sorted(tagkeys)

    def controls(c):
        cf = c["confounders"]
        gdp, rd, size, base = cf["gdp_per_capita_usd"], cf["rd_pct_gdp"], cf["size"], cf["base_rank"]
        if None in (gdp, rd, size) or gdp <= 0 or size <= 0:
            return None
        return [math.log(gdp), rd, math.log(size), base]

    results = []
    for tag in tagkeys:
        rows = []
        for c in countries:
            tv = c["tags"].get(tag)
            out = c["deltas"].get(OUTCOME_WINDOW)
            ctrl = controls(c)
            if isinstance(tv, dict) and isinstance(tv.get("value"), bool) and out is not None and ctrl:
                rows.append((1.0 if tv["value"] else 0.0, out, ctrl))
        n = len(rows)
        entry = {"feature": tag, "n": n, "outcome": f"{OUTCOME_WINDOW}y EPI delta"}
        if n >= 12 and len({r[0] for r in rows}) == 2:
            xs = [r[0] for r in rows]
            ys = [r[1] for r in rows]
            entry["pearson_r"] = round(pearson(xs, ys), 3)
            try:
                X = [[1.0, r[0]] + r[2] for r in rows]
                fit = ols(ys, X)
                b, se = fit["beta"][1], fit["se"][1]
                t = b / se if se else 0.0
                p = 2 * (1 - phi(abs(t)))
                entry.update({
                    "coef": round(b, 3),
                    "ci95": [round(b - 1.96 * se, 3), round(b + 1.96 * se, 3)],
                    "p": round(p, 4),
                    "r2": round(fit["r2"], 3),
                    "controls": ["log_gdp_pc", "rd_pct_gdp", "log_size", "base_rank"],
                })
            except ValueError:
                entry["note"] = "regression singular (insufficient variation)"
        else:
            entry["note"] = "insufficient n or no variation"
        results.append(entry)

    tested = sum(1 for r in results if "p" in r)
    snap["correlation"] = {
        "level": "country",
        "outcome_window": OUTCOME_WINDOW,
        "method": "Pearson/point-biserial + OLS with confounder controls",
        "controls": ["log_gdp_pc", "rd_pct_gdp", "log_size", "base_rank"],
        "multiple_comparisons": (
            f"{tested} features tested; treat single p-values cautiously "
            f"(Bonferroni alpha ~ {round(0.05 / tested, 4) if tested else 'n/a'})."
        ),
        "disclaimer": "Observational association, not causation. Small n; interpret as directional.",
        "results": results,
        "note_institution_level": (
            "Seed uses country-level tags (derived from each country's top institution). "
            "Institution-level regression is enabled once per-institution tags are populated."
        ),
    }

    # enrich universal_approach with strongest positive controlled associations
    pos = [r for r in results if r.get("coef", 0) > 0]
    pos.sort(key=lambda r: r["coef"], reverse=True)
    snap["universal_approach"]["ranked_levers"] = [
        {"feature": r["feature"], "coef": r["coef"], "p": r.get("p"),
         "ci95": r.get("ci95"), "n": r["n"]}
        for r in pos
    ]

    with open(SNAP, "w") as f:
        json.dump(snap, f, separators=(",", ":"))
    print(f"correlation: tested {tested}/{len(results)} features at country level")
    for r in results:
        if "coef" in r:
            print(f"  {r['feature']:24s} coef={r['coef']:+.2f} p={r['p']:.3f} n={r['n']} r2={r['r2']}")
        else:
            print(f"  {r['feature']:24s} {r.get('note')}")


if __name__ == "__main__":
    main()
