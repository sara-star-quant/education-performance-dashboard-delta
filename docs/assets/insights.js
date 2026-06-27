/* Insights page: renders the controlled correlation results + universal levers.
   DOM tables render first and the chart is isolated in try/catch, so a chart
   error can never blank the data. Color-blind-safe palette throughout. */
const TAG_LABEL = {
  ai_using: "Actively using AI", quantum_programs: "Quantum programs",
  delivery_remote: "Remote available", funding_government: "Govt-funded",
  intl_dual_degree: "Intl dual-degree", quantum_phd: "Quantum PhD",
};
const lab = (k) => TAG_LABEL[k] || k;
const POS = "#1f6fb2", NEG = "#c25a00"; // blue / orange, color-blind friendly

(async function () {
  const wrap = document.querySelector(".wrap");
  try {
    const man = await fetch("./data/manifest.json").then((r) => r.json());
    const path = man.snapshots.find((s) => s.version === man.latest).path;
    const snap = await fetch("./data/" + path).then((r) => r.json());
    const cor = snap.correlation;
    if (!cor) {
      document.getElementById("disc").textContent =
        "This snapshot has no correlation results yet (run build/correlate.py).";
      return;
    }

    document.getElementById("disc").textContent = `${cor.disclaimer} ${cor.multiple_comparisons}`;
    const tested = cor.results.filter((r) => "coef" in r);

    // ---- DOM first (always shows, independent of charts) ----
    const levers = (snap.universal_approach.ranked_levers || []).filter((l) => l.coef > 0);
    document.getElementById("leverSub").textContent = snap.universal_approach.note;
    document.getElementById("levers").innerHTML = levers.length ? levers.map((l) =>
      `<div class="note" style="margin:6px 0"><b>${lab(l.feature)}</b> - assoc +${l.coef} ${l.p != null ? `(p=${l.p})` : ""} <span class="na">n=${l.n}</span></div>`
    ).join("") : '<span class="na">No positively-associated features cleared the bar in this cohort.</span>';

    document.querySelector("#tbl tbody").innerHTML = cor.results.map((r) =>
      `<tr><td>${lab(r.feature)}</td><td class="num">${r.n}</td>
        <td class="num">${r.pearson_r ?? "-"}</td>
        <td class="num">${r.coef ?? "-"}</td>
        <td class="num">${r.ci95 ? `[${r.ci95[0]}, ${r.ci95[1]}]` : "-"}</td>
        <td class="num">${r.p ?? "-"}</td>
        <td class="num">${r.r2 ?? "-"}</td></tr>`).join("");

    const s = snap.sensitivity;
    document.getElementById("robust").innerHTML =
      `Normalization sensitivity: ${s.note} <b>${s.stable ? "Stable" : "Unstable"}</b> across min-max vs z-score.<br>` +
      `${cor.note_institution_level}`;

    // ---- chart last, isolated ----
    if (!tested.length) {
      document.getElementById("forest").innerHTML =
        '<span class="na">Not enough varying features in this cohort to plot associations.</span>';
      return;
    }
    try {
      const cats = tested.map((r) => lab(r.feature));
      echarts.init(document.getElementById("forest")).setOption({
        aria: { enabled: true },
        grid: { left: 140, right: 24, top: 10, bottom: 34 },
        xAxis: { type: "value", name: "coef (5y EPI delta)", nameLocation: "middle", nameGap: 26, splitLine: { lineStyle: { color: "#eef0f1" } } },
        yAxis: { type: "category", data: cats, axisLine: { lineStyle: { color: "#dfe1e3" } } },
        tooltip: { trigger: "item", formatter: (p) => { const r = tested[p.dataIndex]; return `${lab(r.feature)}<br>coef ${r.coef} [${r.ci95[0]}, ${r.ci95[1]}]<br>p=${r.p}, n=${r.n}`; } },
        series: [
          // CI whisker (custom line)
          { type: "custom", renderItem: (params, api) => {
              const r = tested[params.dataIndex];
              const y = api.coord([0, params.dataIndex])[1];
              const x0 = api.coord([r.ci95[0], 0])[0], x1 = api.coord([r.ci95[1], 0])[0];
              return { type: "line", shape: { x1: x0, y1: y, x2: x1, y2: y }, style: { stroke: "#9aa0a6", lineWidth: 2 } };
            }, data: tested.map((_, i) => i), silent: true },
          // point estimate; blue = positive, orange = negative; solid if p<0.05 else hollow
          { type: "scatter", symbolSize: 13, data: tested.map((r, i) => ({
              value: [r.coef, i],
              symbol: r.p < 0.05 ? "circle" : "emptyCircle",
              itemStyle: { color: r.coef >= 0 ? POS : NEG, borderColor: r.coef >= 0 ? POS : NEG, borderWidth: 2 },
            })) },
          { type: "line", markLine: { silent: true, symbol: "none", lineStyle: { color: "#888", type: "dashed" }, data: [{ xAxis: 0 }] }, data: [] },
        ],
      });
    } catch (e) {
      document.getElementById("forest").innerHTML =
        '<span class="na">Chart unavailable; see the detail table above.</span>';
    }
  } catch (e) {
    wrap.insertAdjacentHTML("beforeend", `<p class="na">Could not load snapshot data: ${e}</p>`);
  }
})();
