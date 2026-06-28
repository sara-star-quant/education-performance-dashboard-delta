/* Global Education Performance Delta Dashboard - main view.
   Loads the latest snapshot, recomputes EPI/deltas client-side when pillar
   weights change, and renders map + regions + top-30 + developing segment. */
const PILLARS = ["R", "P", "A", "O"];
const PILLAR_LABEL = { R: "Rankings", P: "Research", A: "Attainment", O: "Outcomes" };
const TAG_LABEL = {
  ai_using: "Actively using AI", ai_educating: "Educating about AI", ai_adapting: "Adapting AI",
  quantum_programs: "Quantum programs", quantum_phd: "Quantum PhD",
  delivery_remote: "Remote available", delivery_hybrid: "Hybrid", delivery_onsite_only: "Onsite only",
  funding_government: "Govt-funded", funding_edu_org: "Org-funded",
  intl_dual_degree: "Intl dual-degree", youth_pathway: "Youth pathway",
  industry_rnd_partnership: "Industry R&D", open_access_mandate: "Open access",
  entrepreneurship_support: "Entrepreneurship", stem_intensive: "STEM-intensive",
};
const FILTERABLE = ["ai_using", "quantum_programs", "delivery_remote", "funding_government"];

const PALETTES = {
  default: ["#c0504d", "#f3f0ea", "#2e8b57"],   // red -> green
  cb: ["#c25a00", "#f4f1ea", "#1f6fb2"],         // orange -> blue (color-blind friendly)
};
const S = { snap: null, window: "5", weights: { R: 25, P: 25, A: 25, O: 25 }, filters: new Set(), map: null, byIso: {}, palette: "default", lastTrigger: null };

const $ = (s) => document.querySelector(s);
// escape strings from data sources (e.g. OpenAlex names, overlay text) before innerHTML
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDelta = (v) => (v == null ? "n/a" : (v >= 0 ? "+" : "") + v.toFixed(1));
const cls = (v) => (v == null ? "" : v >= 0 ? "pos" : "neg");
const arrow = (v) => (v == null ? "" : v >= 0 ? "▲" : "▼"); // up/down triangle, CVD-safe
// delta rendered with an arrow glyph so it never relies on color alone
const deltaSpan = (v) => `<span class="delta ${cls(v)}"><span class="arw" aria-hidden="true">${arrow(v)}</span> ${fmtDelta(v)}</span>`;

async function boot() {
  const man = await fetch("./data/manifest.json").then((r) => r.json());
  const sel = $("#snapSel");
  man.snapshots.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.path; o.textContent = `${s.version} (${s.country_count} countries)`;
    sel.appendChild(o);
  });
  sel.value = man.snapshots.find((s) => s.version === man.latest).path;
  sel.onchange = () => loadSnap(sel.value);
  await loadSnap(sel.value);
  wireControls();
}

async function loadSnap(path) {
  S.snap = await fetch("./data/" + path).then((r) => r.json());
  S.byIso = Object.fromEntries(S.snap.countries.map((c) => [c.iso2, c]));
  $("#metaLine").textContent =
    `Reference year ${S.snap.meta.reference_year} - ${S.snap.countries.length} countries - sources: ${S.snap.meta.sources.join(", ")}`;
  const geo = await fetch("./assets/world.json").then((r) => r.json());
  echarts.registerMap("world", geo);
  renderAll();
}

/* ---- client-side EPI recompute (weights) ---- */
function epiAt(c, year) {
  let s = 0, w = 0;
  for (const p of PILLARS) {
    const v = c.pillars[p]?.[year];
    if (v != null) { s += S.weights[p] * v; w += S.weights[p]; }
  }
  return w ? s / w : null;
}
function deltaAt(c, win) {
  const ref = S.snap.meta.reference_year;
  const a = epiAt(c, ref), b = epiAt(c, ref - +win);
  return a == null || b == null ? null : a - b;
}
function regionDelta(rid, win) {
  let num = 0, den = 0;
  for (const c of S.snap.countries) {
    if (c.region !== rid) continue;
    const d = deltaAt(c, win), wt = c.confounders.size || 0;
    if (d != null && wt) { num += wt * d; den += wt; }
  }
  return den ? num / den : null;
}
function passFilters(c) {
  for (const t of S.filters) if (!(c.tags[t] && c.tags[t].value)) return false;
  return true;
}

/* ---- renders ---- */
function renderAll() { renderMap(); renderRegions(); renderTop30(); renderDeveloping(); }

function renderMap() {
  if (!S.map) S.map = echarts.init($("#map"));
  const data = S.snap.countries.filter(passFilters).map((c) => ({ name: c.echarts, value: deltaAt(c, S.window), iso2: c.iso2 }));
  const vals = data.map((d) => d.value).filter((v) => v != null);
  const max = Math.max(3, ...vals.map(Math.abs));
  S.map.setOption({
    aria: { enabled: true, description: `World map of ${S.window}-year education performance change by country.` },
    tooltip: {
      trigger: "item",
      formatter: (p) => p.value == null || isNaN(p.value) ? `${p.name}: n/a`
        : `<b>${p.name}</b><br>${S.window}y EPI delta: ${arrow(p.value)} ${fmtDelta(p.value)}`,
    },
    visualMap: {
      min: -max, max: max, left: 14, bottom: 14, calculable: true,
      inRange: { color: PALETTES[S.palette] },
      text: ["improving", "declining"], textStyle: { fontSize: 11, color: "#6b7177" },
    },
    series: [{
      type: "map", map: "world", roam: true, data,
      // stop runaway zoom-out when the whole map already fits
      zoom: 1, scaleLimit: { min: 1, max: 8 },
      itemStyle: { areaColor: "#f0f1f2", borderColor: "#dfe1e3" },
      emphasis: { itemStyle: { areaColor: "#cfe3e1" }, label: { show: false } },
      select: { itemStyle: { areaColor: "#9fc7c4" } },
    }],
  }, true);
  S.map.off("click");
  S.map.on("click", (p) => { if (p.data && p.data.iso2) openDetail(p.data.iso2); });
}

function renderRegions() {
  const ranked = S.snap.regions
    .map((r) => ({ r, d: regionDelta(r.id, S.window) }))
    .filter((x) => x.d != null).sort((a, b) => b.d - a.d);
  $("#regionSub").textContent = `Enrollment-weighted mean EPI delta over ${S.window}y - top 3 of ${ranked.length}`;
  $("#regions").innerHTML = ranked.slice(0, 3).map((x, i) => `
    <div class="card region-card">
      <div class="rank">#${i + 1} improving region</div>
      <div class="name">${esc(x.r.name)}</div>
      <div>${deltaSpan(x.d)}</div>
      <div class="note">${x.r.members.length} countries - mean EPI ${x.r.epi_mean_ref}</div>
    </div>`).join("");
}

let sortKey = "delta", sortDir = -1;
function renderTop30() {
  const rows = S.snap.countries.filter(passFilters)
    .map((c) => ({ c, delta: deltaAt(c, S.window), epi: epiAt(c, S.snap.meta.reference_year) }))
    .filter((x) => x.delta != null);
  rows.sort((a, b) => sortDir * ((sortKey === "name" ? a.c.name.localeCompare(b.c.name)
    : (a[sortKey] ?? -1e9) - (b[sortKey] ?? -1e9))));
  const top = rows.slice(0, 30);
  $("#top30Sub").textContent = `Ranked by ${S.window}y EPI delta${S.filters.size ? " - filtered" : ""} - ${rows.length} match`;
  $("#top30 tbody").innerHTML = top.map((x, i) => {
    const c = x.c;
    const tg = Object.entries(c.tags).filter(([, v]) => v.value).slice(0, 3)
      .map(([k]) => `<span class="tag">${TAG_LABEL[k] || k}</span>`).join("");
    return `<tr data-iso="${esc(c.iso2)}" tabindex="0" role="button" aria-label="${esc(c.name)}, ${S.window} year delta ${fmtDelta(x.delta)}, open details">
      <td class="rankcol">${i + 1}</td>
      <td>${esc(c.name)} ${tg}</td>
      <td><span class="conf ${c.confidence}">${c.confidence}</span></td>
      <td class="num">${deltaSpan(x.delta)}</td>
      <td class="num">${x.epi != null ? x.epi.toFixed(1) : "n/a"}</td>
    </tr>`;
  }).join("");
  $("#top30 tbody").querySelectorAll("tr").forEach((tr) => {
    const open = () => openDetail(tr.dataset.iso);
    tr.onclick = open;
    tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } };
  });
}

function renderDeveloping() {
  const wrap = $("#developing");
  if (!S.snap.developing || !S.snap.developing.length) { wrap.innerHTML = ""; return; }
  wrap.innerHTML = S.snap.developing.map((d) => {
    const benches = ["neighbor", "peer"].map((role) => {
      const b = d.benchmarks[role];
      if (!b) return `<div><div class="label">${role}</div><div class="na">not available</div></div>`;
      const gapMax = 60;
      return `<div>
        <div class="label">${role}: ${esc(b.name)}</div>
        <div class="note">EPI gap ${b.epi_gap >= 0 ? "+" : ""}${b.epi_gap}</div>
        <div class="gapbar"><i style="width:${Math.min(100, Math.abs(b.epi_gap) / gapMax * 100)}%"></i></div>
      </div>`;
    }).join("");
    const mot = (d.youth_motivators || []).map((m) =>
      `<li>${esc(m.text)} ${m.citation ? `<a href="${esc(m.citation)}" target="_blank" rel="noopener">[src]</a>` : ""}</li>`).join("");
    return `<div class="card">
      <h2>${esc(d.name)} <span class="conf low">${esc(d.flag_reason.join(", "))}</span></h2>
      <div class="sub">EPI ${d.epi_ref} - 5y delta ${deltaSpan(d.delta["5"])}</div>
      <div class="bench">${benches}</div>
      ${mot ? `<div class="label" style="margin-top:12px">Youth motivators</div><ul class="note">${mot}</ul>` : ""}
    </div>`;
  }).join("");
}

/* ---- detail drawer ---- */
function openDetail(iso) {
  const c = S.byIso[iso]; if (!c) return;
  S.lastTrigger = document.activeElement;
  const ref = S.snap.meta.reference_year;
  $("#dName").textContent = c.name;
  const inst = c.top_institution;
  const cf = c.cost_funding;
  const sub = S.snap.subnational?.[c.iso3];
  const tags = Object.entries(c.tags).map(([k, v]) =>
    `<span class="tag ${v.value ? "" : "off"}" title="${esc(v.evidence)}">${esc(TAG_LABEL[k] || k)}${v.value ? "" : ": no"}</span>`).join("") || '<span class="na">none coded</span>';
  $("#dBody").innerHTML = `
    <div class="kv">
      <span class="k">Region</span><span>${esc(regionName(c.region))}</span>
      <span class="k">EPI (${ref})</span><span>${(epiAt(c, ref) ?? 0).toFixed(1)} <span class="conf ${c.confidence}">${c.confidence}</span></span>
      <span class="k">Delta</span><span>${["1", "3", "5", "10"].map((w) => `${w}y ${deltaSpan(deltaAt(c, w))}`).join(" &nbsp; ")}</span>
      <span class="k">GDP/capita</span><span>${cf || c.confounders.gdp_per_capita_usd ? "$" + Math.round(c.confounders.gdp_per_capita_usd || 0).toLocaleString() : "n/a"} &nbsp; R&D ${c.confounders.rd_pct_gdp ?? "n/a"}%</span>
    </div>
    <div id="trend"></div>
    <div class="label">Normalized pillar change (${S.window}y)</div>
    <div id="pillars"></div>
    <div class="label">Top contributing institution</div>
    ${inst ? `<div class="note"><b>${esc(inst.name)}</b><br>${esc(inst.evidence)}<br><span class="na">${esc(inst.metric_climbed)}</span></div>` : '<span class="na">not available</span>'}
    <div class="label" style="margin-top:14px">Why it moved</div>
    <div class="note">${esc(c.reason.text)} ${c.reason.auto_generated ? '<span class="na">(data-derived)</span>' : ""}
      <div class="cite">${(c.reason.citations || []).map((u) => /^https?:\/\//.test(u) ? `<a href="${esc(u)}" target="_blank" rel="noopener">[src]</a>` : `<span class="na">${esc(u)}</span>`).join(" ")}</div>
    </div>
    <div class="label" style="margin-top:14px">Feature tags</div><div>${tags}</div>
    <div class="label" style="margin-top:14px">Cost & funding</div>
    ${cf ? `<div class="note">${esc(cf.tuition_note)} ${cf.citation ? `<a href="${esc(cf.citation)}" target="_blank" rel="noopener">[src]</a>` : ""}</div>` : '<span class="na">not available</span>'}
    <div class="label" style="margin-top:14px">Sub-national breakdown</div>
    ${sub ? sub.map((s) => `<div class="note"><b>${esc(s.state)}</b> - ${esc(s.note)}<br>${s.institutions.map((i) => `${esc(i.name)} <span class="na">(${esc(i.feature)})</span>`).join("<br>")}</div>`).join("<br>")
      : '<span class="na">country-level only (no sub-national data)</span>'}
  `;
  drawer(true);
  drawTrend(c); drawPillars(c);
}

function reuse(sel) {
  const el = $(sel);
  return echarts.getInstanceByDom(el) || echarts.init(el);
}
function drawTrend(c) {
  const years = S.snap.meta.key_years;
  const epi = years.map((y) => { const v = epiAt(c, y); return v == null ? null : +v.toFixed(1); });
  reuse("#trend").setOption({
    grid: { left: 32, right: 12, top: 24, bottom: 24 }, title: { text: "EPI trend", textStyle: { fontSize: 12, color: "#6b7177" }, left: 0, top: 0 },
    xAxis: { type: "category", data: years, axisLine: { lineStyle: { color: "#dfe1e3" } } },
    yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: "#eef0f1" } } },
    tooltip: { trigger: "axis" },
    series: [{ type: "line", data: epi, smooth: true, symbolSize: 6, lineStyle: { color: "#2f6f72", width: 2.5 }, itemStyle: { color: "#2f6f72" }, areaStyle: { color: "rgba(47,111,114,.08)" } }],
  });
}
function drawPillars(c) {
  const d = PILLARS.map((p) => c.pillar_deltas[p]?.[S.window] ?? 0);
  reuse("#pillars").setOption({
    grid: { left: 70, right: 16, top: 8, bottom: 20 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#eef0f1" } } },
    yAxis: { type: "category", data: PILLARS.map((p) => PILLAR_LABEL[p]), axisLine: { lineStyle: { color: "#dfe1e3" } } },
    tooltip: { trigger: "item", formatter: (p) => `${p.name}: ${fmtDelta(p.value)}` },
    series: [{ type: "bar", data: d.map((v) => ({ value: +v.toFixed(1), itemStyle: { color: v >= 0 ? "#2e8b57" : "#c0504d" } })), barWidth: 14 }],
  });
}
function regionName(id) { return (S.snap.regions.find((r) => r.id === id) || {}).name || id; }

function drawer(open) {
  const d = $("#drawer");
  d.classList.toggle("open", open);
  $("#drawerBg").classList.toggle("open", open);
  d.setAttribute("aria-hidden", open ? "false" : "true");
  if (open) {
    $("#dClose").focus();
  } else if (S.lastTrigger && S.lastTrigger.focus) {
    S.lastTrigger.focus();
  }
}

/* ---- controls ---- */
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const renderAllDebounced = debounce(() => renderAll(), 90);

function wireControls() {
  document.querySelectorAll("#winSeg button").forEach((b) =>
    b.onclick = () => {
      S.window = b.dataset.w;
      document.querySelectorAll("#winSeg button").forEach((x) => {
        const on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on);
      });
      renderAll();
    });

  // color-blind palette toggle
  document.querySelectorAll("#palSeg button").forEach((b) =>
    b.onclick = () => {
      S.palette = b.dataset.p;
      document.body.classList.toggle("cb", S.palette === "cb");
      document.querySelectorAll("#palSeg button").forEach((x) => {
        const on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on);
      });
      renderAll();
    });

  const chips = $("#tagChips");
  chips.innerHTML = FILTERABLE.map((t) =>
    `<button type="button" class="chip" data-t="${t}" aria-pressed="false">${TAG_LABEL[t]}</button>`).join("");
  chips.querySelectorAll(".chip").forEach((ch) =>
    ch.onclick = () => {
      const t = ch.dataset.t;
      const on = !S.filters.has(t);
      on ? S.filters.add(t) : S.filters.delete(t);
      ch.classList.toggle("on", on); ch.setAttribute("aria-pressed", on);
      renderAll();
    });

  PILLARS.forEach((p) => {
    const el = document.querySelector(`#w_${p}`);
    el.oninput = () => { S.weights[p] = +el.value; document.querySelector(`#wv_${p}`).textContent = el.value; renderAllDebounced(); };
  });

  $("#top30 thead").querySelectorAll("th[data-k]").forEach((th) =>
    th.onclick = () => {
      const k = th.dataset.k;
      if (sortKey === k) sortDir *= -1; else { sortKey = k; sortDir = -1; }
      renderTop30();
    });

  $("#drawerBg").onclick = () => drawer(false);
  $("#dClose").onclick = () => drawer(false);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") drawer(false); });
  window.addEventListener("resize", debounce(() => { S.map && S.map.resize(); }, 120));
}

boot();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
