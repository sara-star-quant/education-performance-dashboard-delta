/* Insights page: renders the controlled correlation results + universal levers. */
const TAG_LABEL = {
  ai_using: "Actively using AI", quantum_programs: "Quantum programs",
  delivery_remote: "Remote available", funding_government: "Govt-funded",
  intl_dual_degree: "Intl dual-degree", quantum_phd: "Quantum PhD",
};
const lab = (k) => TAG_LABEL[k] || k;

(async function () {
  const man = await fetch("./data/manifest.json").then((r) => r.json());
  const path = man.snapshots.find((s) => s.version === man.latest).path;
  const snap = await fetch("./data/" + path).then((r) => r.json());
  const cor = snap.correlation;
  if (!cor) { document.querySelector(".wrap").insertAdjacentHTML("beforeend", "<p class='na'>No correlation results in this snapshot.</p>"); return; }

  document.getElementById("disc").textContent = `${cor.disclaimer} ${cor.multiple_comparisons}`;

  const tested = cor.results.filter((r) => "coef" in r);

  // forest plot (coef + CI)
  const cats = tested.map((r) => lab(r.feature));
  echarts.init(document.getElementById("forest")).setOption({
    grid: { left: 130, right: 24, top: 10, bottom: 30 },
    xAxis: { type: "value", name: "coef (5y EPI delta)", nameLocation: "middle", nameGap: 26, splitLine: { lineStyle: { color: "#eef0f1" } } },
    yAxis: { type: "category", data: cats, axisLine: { lineStyle: { color: "#dfe1e3" } } },
    tooltip: { trigger: "item", formatter: (p) => { const r = tested[p.dataIndex]; return `${lab(r.feature)}<br>coef ${r.coef} [${r.ci95[0]}, ${r.ci95[1]}]<br>p=${r.p}, n=${r.n}`; } },
    series: [
      { type: "scatter", symbolSize: 11, data: tested.map((r, i) => [r.coef, i]),
        itemStyle: { color: (p) => { const r = tested[p.dataIndex]; return r.p < 0.05 ? "#2e8b57" : "#2f6f72"; } } },
      { type: "custom", renderItem: (params, api) => {
          const r = tested[params.dataIndex];
          const y = api.coord([0, params.dataIndex])[1];
          const x0 = api.coord([r.ci95[0], 0])[0], x1 = api.coord([r.ci95[1], 0])[0];
          return { type: "line", shape: { x1: x0, y1: y, x2: x1, y2: y }, style: { stroke: "#9bb7b6", lineWidth: 2 } };
        }, data: tested.map((_, i) => i) },
      { type: "line", markLine: { silent: true, symbol: "none", lineStyle: { color: "#c0504d", type: "dashed" }, data: [{ xAxis: 0 }] }, data: [] },
    ],
  });

  // levers
  const levers = (snap.universal_approach.ranked_levers || []).filter((l) => l.coef > 0);
  document.getElementById("leverSub").textContent = snap.universal_approach.note;
  document.getElementById("levers").innerHTML = levers.length ? levers.map((l) =>
    `<div class="note" style="margin:6px 0"><b>${lab(l.feature)}</b> - assoc +${l.coef} ${l.p != null ? `(p=${l.p})` : ""} <span class="na">n=${l.n}</span></div>`
  ).join("") : '<span class="na">No positively-associated features cleared the bar in this cohort.</span>';

  // table
  document.querySelector("#tbl tbody").innerHTML = cor.results.map((r) =>
    `<tr><td>${lab(r.feature)}</td><td class="num">${r.n}</td>
      <td class="num">${r.pearson_r ?? "-"}</td>
      <td class="num">${r.coef ?? "-"}</td>
      <td class="num">${r.ci95 ? `[${r.ci95[0]}, ${r.ci95[1]}]` : "-"}</td>
      <td class="num">${r.p ?? "-"}</td>
      <td class="num">${r.r2 ?? "-"}</td></tr>`).join("");

  // robustness
  const s = snap.sensitivity;
  document.getElementById("robust").innerHTML =
    `Normalization sensitivity: ${s.note} <b>${s.stable ? "Stable" : "Unstable"}</b> across min-max vs z-score.<br>` +
    `${cor.note_institution_level}`;
})();
