/* Shared chart helpers for the ALICIA summary pages. Inline SVG, no libraries. Each chart keeps what it was drawn
 * from in container._xl, for the Excel export (xlsx.js). */
const SVGNS = "http://www.w3.org/2000/svg";
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fyLabel = (y) => `${y}-${String((y + 1) % 100).padStart(2, "0")}`;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthLabel = (t) => { const d = new Date(t); return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`; };
const quarterLabel = (t) => { const d = new Date(t); return `${MONTHS[d.getUTCMonth()]}–${MONTHS[d.getUTCMonth() + 2]} ${d.getUTCFullYear()}`; };
const parseYm = (s) => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, 1);
const isNum = (v) => typeof v === "number" && Number.isFinite(v);

function fmt(v, d = 1) {
  if (!isNum(v)) return "–";
  return v.toLocaleString("en-AU", { minimumFractionDigits: d, maximumFractionDigits: d });
}
function fmtSigned(v, d = 1) {
  if (!isNum(v)) return "–";
  const s = fmt(Math.abs(v), d);
  return v > 0.0000001 ? `+${s}` : v < -0.0000001 ? `−${s}` : s;
}

function niceStep(span, n) {
  const raw = span / Math.max(1, n);
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const f = raw / mag;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
}
function niceTicks(lo, hi, n = 5) {
  if (!isNum(lo) || !isNum(hi)) return [0, 1];
  if (lo === hi) { lo -= 1; hi += 1; }
  const step = niceStep(hi - lo, n);
  const start = Math.floor(lo / step) * step;
  const ticks = [];
  for (let v = start; v <= hi + step * 0.5; v += step) ticks.push(+v.toPrecision(12));
  return ticks;
}

function el(tag, attrs = {}, parent = null) {
  const node = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

/* One tooltip element for the page. */
const TIP = (() => {
  const d = document.createElement("div");
  d.className = "tip";
  d.hidden = true;
  d.setAttribute("role", "status");
  document.body.appendChild(d);
  return d;
})();
function showTip(html, ev) {
  TIP.innerHTML = html;
  TIP.hidden = false;
  const pad = 14, w = TIP.offsetWidth, h = TIP.offsetHeight;
  let x = ev.clientX + pad, y = ev.clientY + pad;
  if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
  if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
  TIP.style.left = `${Math.max(8, x)}px`;
  TIP.style.top = `${Math.max(8, y)}px`;
}
const hideTip = () => { TIP.hidden = true; };

/* Charts redraw at their container's width, so text stays legible on phones. */
const CHARTS = new Map();
const RO = typeof ResizeObserver !== "undefined"
  ? new ResizeObserver((entries) => { for (const e of entries) { const f = CHARTS.get(e.target); if (f) f(); } })
  : null;
function mount(container, draw) {
  const known = CHARTS.has(container);
  CHARTS.set(container, draw);
  if (RO && !known) RO.observe(container);
  draw();
}

/**
 * Line chart.
 * opts: x (numbers: years, or UTC ms), xKind ("fy" | "year" | "month" | "quarter"),
 * series [{key, label, values, color, dash (true or a dash pattern), width}], yFmt (value -> text),
 * ref (y value for a dashed reference line), zero (true: the y axis includes 0), markers [{x, label}],
 * band ({from, to, label}: a shaded span of x),
 * height, yLabel, tipDigits.
 */
function lineChart(container, opts) {
  container._xl = { kind: "line", opts };
  const draw = () => {
    const W = Math.max(280, Math.floor(container.clientWidth || 600));
    const H = opts.height || Math.round(Math.min(300, Math.max(210, W * 0.48)));
    const m = { t: 14 + (opts.markers && opts.markers.length ? 14 : 0), r: 14, b: 26, l: 46 };
    const xs = opts.x;
    const series = opts.series.filter((s) => s.values.some(isNum));
    container.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opts.label || "" });
    container.appendChild(svg);
    if (!series.length || !xs.length) {
      el("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, svg).textContent = "No data for this selection";
      return;
    }
    let lo = Infinity, hi = -Infinity;
    for (const s of series) for (const v of s.values) if (isNum(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    if (isNum(opts.ref)) { lo = Math.min(lo, opts.ref); hi = Math.max(hi, opts.ref); }
    if (opts.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    const ticks = niceTicks(lo, hi, H > 240 ? 5 : 4);
    const y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const x0 = xs[0], x1 = xs[xs.length - 1];
    const sx = (x) => m.l + ((x - x0) / Math.max(1e-9, x1 - x0)) * (W - m.l - m.r);
    const sy = (v) => H - m.b - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - m.t - m.b);
    const yFmt = opts.yFmt || ((v) => fmt(v, 0));

    if (opts.band && isNum(opts.band.from) && isNum(opts.band.to)) {
      const a = Math.max(x0, opts.band.from), b = Math.min(x1, opts.band.to);
      if (b >= a) {
        const half = xs.length > 1 ? (sx(xs[1]) - sx(xs[0])) / 2 : 6;
        const g = el("g", { class: "band" }, svg);
        el("rect", { x: Math.max(m.l, sx(a) - half), y: m.t, width: Math.min(W - m.r, sx(b) + half) - Math.max(m.l, sx(a) - half), height: H - m.t - m.b }, g);
        if (opts.band.label) el("text", { x: Math.max(m.l, sx(a) - half) + 4, y: m.t + 11 }, g).textContent = opts.band.label;
      }
    }
    const grid = el("g", {}, svg);
    for (const t of ticks) {
      el("line", { class: "gridline", x1: m.l, x2: W - m.r, y1: sy(t), y2: sy(t) }, grid);
      const tx = el("text", { x: m.l - 6, y: sy(t) + 3.5, "text-anchor": "end" }, grid);
      tx.textContent = yFmt(t);
    }
    if (isNum(opts.ref)) el("line", { class: "refline", x1: m.l, x2: W - m.r, y1: sy(opts.ref), y2: sy(opts.ref) }, svg);

    // x ticks: years for financial years, calendar years for monthly and quarterly data.
    const axis = el("g", { class: "axis" }, svg);
    el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }, axis);
    const maxTicks = Math.max(2, Math.floor((W - m.l - m.r) / (opts.xKind === "fy" ? 72 : 56)));
    if (opts.xKind === "fy" || opts.xKind === "year") {
      const span = x1 - x0;
      const step = [1, 2, 5, 10].find((s) => span / s <= maxTicks) || 10;
      for (let y = Math.ceil(x0 / step) * step; y <= x1; y += step) {
        el("line", { x1: sx(y), x2: sx(y), y1: H - m.b, y2: H - m.b + 4 }, axis);
        el("text", { x: sx(y), y: H - 8, "text-anchor": "middle" }, axis).textContent = opts.xKind === "fy" ? fyLabel(y) : String(y);
      }
    } else {
      const ya = new Date(x0).getUTCFullYear(), yb = new Date(x1).getUTCFullYear();
      const step = [1, 2, 5, 10].find((s) => (yb - ya) / s <= maxTicks) || 10;
      for (let y = Math.ceil(ya / step) * step; y <= yb; y += step) {
        const t = Date.UTC(y, 0, 1);
        if (t < x0 || t > x1) continue;
        el("line", { x1: sx(t), x2: sx(t), y1: H - m.b, y2: H - m.b + 4 }, axis);
        el("text", { x: sx(t), y: H - 8, "text-anchor": "middle" }, axis).textContent = String(y);
      }
    }

    // Markers (evaluated reform dates), labels staggered on two rows.
    (opts.markers || []).filter((mk) => mk.x >= x0 && mk.x <= x1).forEach((mk, i) => {
      const g = el("g", { class: "marker" }, svg);
      el("line", { x1: sx(mk.x), x2: sx(mk.x), y1: m.t - 2, y2: H - m.b }, g);
      const t = el("text", { x: sx(mk.x) + 3, y: i % 2 ? m.t - 4 : m.t - 16 + 8, "text-anchor": "start" }, g);
      t.textContent = mk.short || "";
      const title = el("title", {}, g);
      title.textContent = mk.label;
    });

    // Lines, broken at missing values.
    for (const s of series) {
      let d = "", pen = false;
      s.values.forEach((v, i) => {
        if (!isNum(v)) { pen = false; return; }
        d += `${pen ? "L" : "M"}${sx(xs[i]).toFixed(1)},${sy(v).toFixed(1)}`;
        pen = true;
      });
      el("path", {
        d, fill: "none", style: `stroke:${s.color}`, "stroke-width": s.width || 1.8,
        "stroke-dasharray": s.dash ? (typeof s.dash === "string" ? s.dash : "5 4") : null, "stroke-linejoin": "round", "stroke-linecap": "round",
      }, svg);
    }

    // Hover readout.
    const cross = el("line", { class: "cross", y1: m.t, y2: H - m.b, visibility: "hidden" }, svg);
    const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
    const xLabel = opts.xKind === "fy" ? fyLabel : opts.xKind === "year" ? String : opts.xKind === "quarter" ? quarterLabel : monthLabel;
    const move = (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ((ev.clientX - r.left) / r.width) * W;
      let best = 0, bd = Infinity;
      xs.forEach((x, i) => { const dd = Math.abs(sx(x) - px); if (dd < bd) { bd = dd; best = i; } });
      cross.setAttribute("x1", sx(xs[best])); cross.setAttribute("x2", sx(xs[best]));
      cross.setAttribute("visibility", "visible");
      const rows = series.map((s) => ({ s, v: s.values[best] })).filter((r) => isNum(r.v)).sort((a, b) => b.v - a.v);
      const tipFmt = opts.tipFmt || yFmt;
      showTip(`<strong>${esc(xLabel(xs[best]))}</strong><table>${rows.map((r) =>
        `<tr><td><span class="k" style="background:${r.s.color}"></span>${esc(r.s.label)}</td><td class="v">${esc(tipFmt(r.v))}</td></tr>`).join("")}</table>`, ev);
    };
    hit.addEventListener("pointermove", move);
    hit.addEventListener("pointerdown", move);
    hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
  };
  mount(container, draw);
}

/* Horizontal bars around zero, sorted by the caller. rows: [{key, label, value, title, color, cls}]. With
 * opts.onSelect, each row is a button (opts.selected is pressed) that calls onSelect(key). */
function rankedBars(container, rows, opts = {}) {
  container._xl = { kind: "ranked", rows, opts };
  const vals = rows.map((r) => r.value).filter(isNum);
  const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const span = Math.max(1e-9, hi - lo);
  const pos = (v) => ((v - lo) / span) * 100;
  container.innerHTML = rows.map((r) => {
    const ok = isNum(r.value);
    const a = ok ? pos(Math.min(0, r.value)) : 0, b = ok ? pos(Math.max(0, r.value)) : 0;
    const color = r.color || (ok && r.value < 0 ? "var(--neg)" : "var(--pos)");
    const inner = `<span class="lab">${esc(r.label)}</span>
      <span class="track"><span class="axis0" style="left:${pos(0)}%"></span>${ok ? `<span class="fill" style="left:${a}%;width:${Math.max(0.5, b - a)}%;background:${color}"></span>` : ""}</span>
      <span class="val">${ok ? esc((opts.fmt || fmtSigned)(r.value)) : "–"}</span>`;
    const cls = `row${r.cls ? ` ${r.cls}` : ""}`;
    return opts.onSelect
      ? `<button type="button" class="${cls}" data-key="${esc(r.key)}" aria-pressed="${r.key === opts.selected}" title="${esc(r.title || r.label)}">${inner}</button>`
      : `<div class="${cls}" title="${esc(r.title || r.label)}">${inner}</div>`;
  }).join("");
  if (opts.onSelect) container.querySelectorAll("button.row").forEach((b) => b.addEventListener("click", () => opts.onSelect(b.dataset.key)));
}

/* Cell shading: diverging (growth) or sequential (shares), mixed into the surface colour so text stays legible. */
function heatColor(v, scale, kind = "div") {
  if (!isNum(v)) return "transparent";
  const p = Math.round(Math.min(1, Math.abs(v) / Math.max(1e-9, scale)) * 58);
  const base = kind === "seq" ? "var(--seq)" : v < 0 ? "var(--neg)" : "var(--pos)";
  return `color-mix(in oklab, ${base} ${p}%, var(--surface))`;
}

/* Legend chips that toggle series. keys: [{key, label, color, dash}]; state: Set of active keys. A chip whose key has
 * a definition (TERMS) shows it on hover, focus or tap, like a defined word. */
function toggleChips(container, keys, active, onChange) {
  const def = (k) => (TERMS[k] ? ` data-term="${esc(k)}" aria-describedby="def-${esc(k)}"` : "");
  container.innerHTML = keys.map((k) => `<button type="button" class="chip" data-key="${esc(k.key)}"${def(k.key)} aria-pressed="${active.has(k.key)}">
    <span class="key${k.dash ? " dash" : ""}" style="${k.dash ? `color:${k.color}` : `background:${k.color}`}"></span>${esc(k.label)}</button>`).join("");
  container.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
    const key = b.dataset.key;
    if (active.has(key)) active.delete(key); else active.add(key);
    b.setAttribute("aria-pressed", active.has(key));
    onChange();
  }));
}

const stateColor = (s) => `var(--s-${s})`;

/* Range slider: two thumbs on one track, for choosing a span of years.
 * opts: min, max, from, to, step (1), minGap (1; 0 lets both ends meet), fmt (value -> text), label,
 * summary ((from, to) -> text), presets [{label, from, to}], onChange(from, to). Returns {set, get}. */
function rangeSlider(container, opts) {
  const { min, max } = opts;
  const step = opts.step || 1, gap = opts.minGap ?? 1, fmtV = opts.fmt || String;
  const clamp = (v) => Math.min(max, Math.max(min, Math.round(v / step) * step));
  let lo = clamp(opts.from ?? min), hi = clamp(opts.to ?? max);
  if (hi - lo < gap) lo = Math.max(min, hi - gap);
  container.classList.add("range");
  container.innerHTML = `<div class="range-head"><span class="range-label">${esc(opts.label || "Period")}</span><output class="range-out"></output></div>
    <div class="range-track"><span class="range-rail"></span><span class="range-fill"></span>
      <input type="range" class="lo" min="${min}" max="${max}" step="${step}" aria-label="${esc(opts.fromLabel || "First year")}">
      <input type="range" class="hi" min="${min}" max="${max}" step="${step}" aria-label="${esc(opts.toLabel || "Last year")}">
    </div>
    <div class="range-ends" aria-hidden="true"><span>${esc(fmtV(min))}</span><span>${esc(fmtV(max))}</span></div>
    ${(opts.presets || []).length ? `<div class="chips range-presets">${opts.presets.map((p, i) => `<button type="button" class="chip" data-i="${i}" aria-pressed="false">${esc(p.label)}</button>`).join("")}</div>` : ""}`;
  const loIn = container.querySelector("input.lo"), hiIn = container.querySelector("input.hi");
  const fill = container.querySelector(".range-fill"), out = container.querySelector(".range-out");
  const pct = (v) => (max > min ? ((v - min) / (max - min)) * 100 : 0);
  function paint() {
    loIn.value = lo; hiIn.value = hi;
    fill.style.left = `${pct(lo)}%`; fill.style.width = `${pct(hi) - pct(lo)}%`;
    loIn.setAttribute("aria-valuetext", fmtV(lo)); hiIn.setAttribute("aria-valuetext", fmtV(hi));
    // Where the thumbs meet near the top end, the low thumb goes on top so it can still be moved.
    loIn.style.zIndex = lo >= max - step && hi - lo <= step ? 4 : 3;
    out.textContent = opts.summary ? opts.summary(lo, hi) : `${fmtV(lo)} to ${fmtV(hi)}`;
    container.querySelectorAll(".range-presets .chip").forEach((b) => {
      const p = opts.presets[+b.dataset.i];
      b.setAttribute("aria-pressed", String(clamp(p.from) === lo && clamp(p.to) === hi));
    });
  }
  let raf = 0;
  const emit = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => opts.onChange(lo, hi)); };
  loIn.addEventListener("input", () => { lo = Math.min(+loIn.value, hi - gap); paint(); emit(); });
  hiIn.addEventListener("input", () => { hi = Math.max(+hiIn.value, lo + gap); paint(); emit(); });
  // A press on the track moves the nearer thumb there.
  container.querySelector(".range-track").addEventListener("pointerdown", (ev) => {
    if (ev.target === loIn || ev.target === hiIn) return;
    const r = ev.currentTarget.getBoundingClientRect();
    const v = clamp(min + ((ev.clientX - r.left) / r.width) * (max - min));
    if (Math.abs(v - lo) <= Math.abs(v - hi)) lo = Math.min(v, hi - gap); else hi = Math.max(v, lo + gap);
    paint(); emit();
  });
  container.querySelectorAll(".range-presets .chip").forEach((b) => b.addEventListener("click", () => {
    const p = opts.presets[+b.dataset.i];
    api.set(p.from, p.to); emit();
  }));
  const api = {
    set(a, b) { hi = clamp(b); lo = Math.min(clamp(a), hi - gap); if (lo < min) { lo = min; hi = Math.max(hi, min + gap); } paint(); },
    get: () => [lo, hi],
  };
  paint();
  return api;
}

/* A bar with a 4px rounded data end and a square end at the baseline (y0). */
function barPath(x, w, y0, y1, r = 4) {
  const up = y1 < y0, h = Math.abs(y1 - y0);
  const rr = Math.max(0, Math.min(r, w / 2, h));
  if (up) return `M${x},${y0}V${y1 + rr}Q${x},${y1} ${x + rr},${y1}H${x + w - rr}Q${x + w},${y1} ${x + w},${y1 + rr}V${y0}Z`;
  return `M${x},${y0}V${y1 - rr}Q${x},${y1} ${x + rr},${y1}H${x + w - rr}Q${x + w},${y1} ${x + w},${y1 - rr}V${y0}Z`;
}

function yAxis(svg, ticks, sy, m, W, yFmt) {
  const grid = el("g", {}, svg);
  for (const t of ticks) {
    el("line", { class: "gridline", x1: m.l, x2: W - m.r, y1: sy(t), y2: sy(t) }, grid);
    el("text", { x: m.l - 6, y: sy(t) + 3.5, "text-anchor": "end" }, grid).textContent = yFmt(t);
  }
}

/* Columns around zero, one series over years. opts: x (years), xKind ("fy" | "year"), values, yFmt, tipFmt,
 * label, tipLabel. Positive columns use --pos, negative --neg. */
function columnChart(container, opts) {
  container._xl = { kind: "column", opts };
  const draw = () => {
    const W = Math.max(280, Math.floor(container.clientWidth || 600));
    const H = opts.height || Math.round(Math.min(260, Math.max(190, W * 0.4)));
    const m = { t: 12, r: 14, b: 26, l: 46 };
    container.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opts.label || "" });
    container.appendChild(svg);
    const xs = opts.x, vals = opts.values;
    if (!xs.length || !vals.some(isNum)) { el("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, svg).textContent = "No data for this selection"; return; }
    const lo = Math.min(0, ...vals.filter(isNum)), hi = Math.max(0, ...vals.filter(isNum));
    const ticks = niceTicks(lo, hi, 4), y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const sy = (v) => H - m.b - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - m.t - m.b);
    const band = (W - m.l - m.r) / xs.length, bw = Math.max(2, Math.min(24, band - 4));
    const yFmt = opts.yFmt || ((v) => fmt(v, 0));
    yAxis(svg, ticks, sy, m, W, yFmt);
    const axis = el("g", { class: "axis" }, svg);
    el("line", { x1: m.l, x2: W - m.r, y1: sy(0), y2: sy(0) }, axis);
    const xl = opts.xKind === "year" ? String : fyLabel;
    const every = [1, 2, 5, 10].find((s) => xs.length / s <= Math.max(2, Math.floor((W - m.l - m.r) / 72))) || 10;
    xs.forEach((x, i) => { if ((x % every) === 0 || every === 1) el("text", { x: m.l + band * (i + 0.5), y: H - 8, "text-anchor": "middle" }, axis).textContent = xl(x); });
    xs.forEach((x, i) => {
      const v = vals[i];
      const g = el("g", { class: "col" }, svg);
      if (isNum(v) && v !== 0) el("path", { d: barPath(m.l + band * (i + 0.5) - bw / 2, bw, sy(0), sy(v)), style: `fill:${v < 0 ? "var(--neg)" : opts.color || "var(--pos)"}` }, g);
      const hit = el("rect", { x: m.l + band * i, y: m.t, width: band, height: H - m.t - m.b, fill: "transparent" }, g);
      const tip = (ev) => showTip(`<strong>${esc(xl(x))}</strong><table><tr><td>${esc(opts.tipLabel || "")}</td><td class="v">${esc((opts.tipFmt || yFmt)(v))}</td></tr></table>`, ev);
      hit.addEventListener("pointermove", tip); hit.addEventListener("pointerdown", tip);
      hit.addEventListener("pointerleave", hideTip);
    });
  };
  mount(container, draw);
}

/* Vertical bars for a few categories. opts: bars [{key, label, value, color, tip}], refs [{value, dash}],
 * yFmt, label, height. Values sit on the bar caps; reference lines are dashed (name them in a legend). */
function barChart(container, opts) {
  container._xl = { kind: "bar", opts };
  const draw = () => {
    const W = Math.max(280, Math.floor(container.clientWidth || 600));
    const H = opts.height || Math.round(Math.min(280, Math.max(220, W * 0.45)));
    const m = { t: 18, r: 14, b: 40, l: 40 };
    container.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opts.label || "" });
    container.appendChild(svg);
    const vals = [...opts.bars.map((b) => b.value), ...(opts.refs || []).map((r) => r.value)].filter(isNum);
    if (!vals.length) { el("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, svg).textContent = "No data for this selection"; return; }
    const ticks = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals), 4), y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const sy = (v) => H - m.b - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - m.t - m.b);
    const yFmt = opts.yFmt || ((v) => fmt(v, 0));
    yAxis(svg, ticks, sy, m, W, yFmt);
    const band = (W - m.l - m.r) / opts.bars.length, bw = Math.min(24, band * 0.5);
    const axis = el("g", { class: "axis" }, svg);
    el("line", { x1: m.l, x2: W - m.r, y1: sy(0), y2: sy(0) }, axis);
    opts.bars.forEach((b, i) => {
      const cx = m.l + band * (i + 0.5);
      const g = el("g", { class: "col" }, svg);
      if (isNum(b.value)) {
        el("path", { d: barPath(cx - bw / 2, bw, sy(0), sy(b.value)), style: `fill:${b.color}` }, g);
        el("text", { x: cx, y: b.value >= 0 ? sy(b.value) - 5 : sy(b.value) + 13, "text-anchor": "middle", class: "val" }, g).textContent = yFmt(b.value);
      }
      const words = b.label.split(" "), half = Math.ceil(words.length / 2);
      const lines = band < b.label.length * 6.2 && words.length > 1 ? [words.slice(0, half).join(" "), words.slice(half).join(" ")] : [b.label];
      lines.forEach((ln, k) => { el("text", { x: cx, y: H - m.b + 15 + k * 12, "text-anchor": "middle", class: "cat" }, axis).textContent = ln; });
      const hit = el("rect", { x: m.l + band * i, y: m.t, width: band, height: H - m.t - m.b, fill: "transparent" }, g);
      const tip = (ev) => showTip(b.tip || `<strong>${esc(b.label)}</strong> ${esc(yFmt(b.value))}`, ev);
      hit.addEventListener("pointermove", tip); hit.addEventListener("pointerdown", tip);
      hit.addEventListener("pointerleave", hideTip);
    });
    (opts.refs || []).filter((r) => isNum(r.value)).forEach((r) => {
      el("line", { class: "refline", x1: m.l, x2: W - m.r, y1: sy(r.value), y2: sy(r.value), style: r.dash ? `stroke-dasharray:${r.dash}` : null }, svg);
    });
  };
  mount(container, draw);
}

/* Scatter of sized points. opts: points [{x, y, size, color, label, tip, muted}], xDomain, yDomain ([lo, hi];
 * points outside are drawn hollow at the edge), xFmt, yFmt, xTitle, yTitle, fit ({slope, intercept, label}),
 * label, height. The nearest point to the pointer gets the tooltip. */
function scatterChart(container, opts) {
  container._xl = { kind: "scatter", opts };
  const draw = () => {
    const W = Math.max(280, Math.floor(container.clientWidth || 600));
    const H = opts.height || Math.round(Math.min(380, Math.max(260, W * 0.55)));
    const m = { t: opts.yTitle ? 24 : 14, r: 16, b: 40, l: 48 };
    container.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opts.label || "" });
    container.appendChild(svg);
    const pts = opts.points.filter((p) => isNum(p.x) && isNum(p.y));
    if (!pts.length) { el("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, svg).textContent = "No data for this selection"; return; }
    const [xa, xb] = opts.xDomain, [ya, yb] = opts.yDomain;
    const xt = niceTicks(xa, xb, W > 480 ? 6 : 4), yt = niceTicks(ya, yb, 5);
    const X0 = xt[0], X1 = xt[xt.length - 1], Y0 = yt[0], Y1 = yt[yt.length - 1];
    const sx = (v) => m.l + ((Math.min(X1, Math.max(X0, v)) - X0) / (X1 - X0)) * (W - m.l - m.r);
    const sy = (v) => H - m.b - ((Math.min(Y1, Math.max(Y0, v)) - Y0) / (Y1 - Y0)) * (H - m.t - m.b);
    yAxis(svg, yt, sy, m, W, opts.yFmt || ((v) => fmt(v, 0)));
    const axis = el("g", { class: "axis" }, svg);
    el("line", { x1: m.l, x2: W - m.r, y1: sy(Math.max(Y0, Math.min(Y1, 0))), y2: sy(Math.max(Y0, Math.min(Y1, 0))) }, axis);
    xt.forEach((t) => {
      el("line", { x1: sx(t), x2: sx(t), y1: H - m.b, y2: H - m.b + 4 }, axis);
      el("text", { x: sx(t), y: H - m.b + 15, "text-anchor": "middle" }, axis).textContent = (opts.xFmt || ((v) => fmt(v, 0)))(t);
    });
    if (opts.xTitle) el("text", { x: (m.l + W - m.r) / 2, y: H - 4, "text-anchor": "middle", class: "title" }, axis).textContent = opts.xTitle;
    if (opts.yTitle) el("text", { x: m.l - 40, y: m.t - 12, "text-anchor": "start", class: "title" }, axis).textContent = opts.yTitle;
    if (opts.fit && isNum(opts.fit.slope)) {
      const f = (x) => opts.fit.intercept + opts.fit.slope * x;
      el("line", { class: "fitline", x1: sx(X0), x2: sx(X1), y1: sy(f(X0)), y2: sy(f(X1)) }, svg);
    }
    const layer = el("g", {}, svg);
    const placed = pts.map((p) => {
      const out = p.x < X0 || p.x > X1 || p.y < Y0 || p.y > Y1;
      return { p, cx: sx(p.x), cy: sy(p.y), r: Math.max(3.5, p.size || 4), out };
    }).sort((a, b) => b.r - a.r);
    for (const q of placed) {
      el("circle", {
        cx: q.cx, cy: q.cy, r: q.r, class: `dot${q.p.muted ? " muted" : ""}${q.out ? " out" : ""}`,
        style: q.out ? `stroke:${q.p.color}` : `fill:${q.p.color}`,
      }, layer);
    }
    const ring = el("circle", { r: 0, class: "dot-hover", visibility: "hidden" }, svg);
    const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
    const move = (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ((ev.clientX - r.left) / r.width) * W, py = ((ev.clientY - r.top) / r.height) * H;
      let best = null, bd = Infinity;
      for (const q of placed) { const d = Math.hypot(q.cx - px, q.cy - py) - q.r; if (d < bd) { bd = d; best = q; } }
      if (!best || bd > 24) { ring.setAttribute("visibility", "hidden"); hideTip(); return; }
      ring.setAttribute("cx", best.cx); ring.setAttribute("cy", best.cy); ring.setAttribute("r", best.r + 3);
      ring.setAttribute("visibility", "visible");
      showTip(best.p.tip || esc(best.p.label), ev);
    };
    hit.addEventListener("pointermove", move); hit.addEventListener("pointerdown", move);
    hit.addEventListener("pointerleave", () => { ring.setAttribute("visibility", "hidden"); hideTip(); });
  };
  mount(container, draw);
}

/* Bars whose width is a weight (equity) and whose height a rate (return), split at a threshold (the cost of
 * equity), after Grattan's profit charts. opts: bars [{label, width, value, tip}] in drawing order, threshold,
 * yDomain [lo, hi] (bars beyond it are cut at the edge), xFmt, yFmt, xTitle, label, height.
 * Fills: --p-normal up to the threshold, --p-super above it, --p-short for a shortfall below it, --p-loss below 0. */
function mekkoChart(container, opts) {
  container._xl = { kind: "mekko", opts };
  const draw = () => {
    const W = Math.max(280, Math.floor(container.clientWidth || 600));
    const H = opts.height || Math.round(Math.min(340, Math.max(240, W * 0.42)));
    const m = { t: 16, r: 14, b: 40, l: 40 };
    container.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opts.label || "" });
    container.appendChild(svg);
    const bars = opts.bars.filter((b) => isNum(b.value) && isNum(b.width) && b.width > 0);
    if (!bars.length) { el("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, svg).textContent = "No data for this selection"; return; }
    const t = opts.threshold;
    const [lo, hi] = opts.yDomain;
    const yt = niceTicks(lo, hi, 5), Y0 = yt[0], Y1 = yt[yt.length - 1];
    const sy = (v) => H - m.b - ((Math.min(Y1, Math.max(Y0, v)) - Y0) / (Y1 - Y0)) * (H - m.t - m.b);
    const yFmt = opts.yFmt || ((v) => fmt(v, 0));
    yAxis(svg, yt, sy, m, W, yFmt);
    const total = bars.reduce((a, b) => a + b.width, 0);
    const scale = (W - m.l - m.r) / total;
    const axis = el("g", { class: "axis" }, svg);
    el("line", { x1: m.l, x2: W - m.r, y1: sy(0), y2: sy(0) }, axis);
    const xt = niceTicks(0, total, W > 520 ? 6 : 3).filter((v) => v <= total * 1.001);
    xt.forEach((v) => {
      el("line", { x1: m.l + v * scale, x2: m.l + v * scale, y1: H - m.b, y2: H - m.b + 4 }, axis);
      el("text", { x: m.l + v * scale, y: H - m.b + 15, "text-anchor": "middle" }, axis).textContent = (opts.xFmt || ((x) => fmt(x, 0)))(v);
    });
    if (opts.xTitle) el("text", { x: (m.l + W - m.r) / 2, y: H - 4, "text-anchor": "middle", class: "title" }, axis).textContent = opts.xTitle;
    const layer = el("g", { class: "mekko" }, svg);
    let cum = 0;
    for (const b of bars) {
      const x = m.l + cum * scale, full = b.width * scale;
      cum += b.width;
      const gap = full > 6 ? 2 : full > 2.5 ? 1 : 0;
      const w = Math.max(0.6, full - gap);
      const g = el("g", { class: "mk" }, layer);
      const seg = (a, z, cls) => { if (z !== a) el("rect", { x, width: w, y: Math.min(sy(a), sy(z)), height: Math.abs(sy(a) - sy(z)), class: cls }, g); };
      const v = b.value;
      if (v >= t) { seg(0, t, "normal"); seg(t, v, "super"); }
      else if (v >= 0) { seg(0, v, "normal"); seg(v, t, "short"); }
      else { seg(v, 0, "loss"); seg(0, t, "short"); }
      if (v > Y1 || v < Y0) el("text", { x: x + w / 2, y: v > Y1 ? m.t - 3 : H - m.b - 3, "text-anchor": "middle", class: "cut" }, g).textContent = v > Y1 ? "▲" : "▼";
      if (b.label && w >= b.label.length * 5.6 + 8) {
        const top = sy(Math.min(Y1, Math.max(v, t)));
        el("text", { x: x + w / 2, y: Math.max(m.t + 9, top - 5), "text-anchor": "middle", class: "lab" }, g).textContent = b.label;
      }
      const hit = el("rect", { x: x - gap / 2, y: m.t, width: Math.max(w + gap, 3), height: H - m.t - m.b, fill: "transparent" }, g);
      const tip = (ev) => { g.classList.add("on"); showTip(b.tip || esc(b.label), ev); };
      hit.addEventListener("pointermove", tip); hit.addEventListener("pointerdown", tip);
      hit.addEventListener("pointerleave", () => { g.classList.remove("on"); hideTip(); });
    }
    if (isNum(t)) el("line", { class: "refline", x1: m.l, x2: W - m.r, y1: sy(t), y2: sy(t) }, svg);
  };
  mount(container, draw);
}

/* Bar table: a row per item, a column per measure, and in each cell a bar of the item's share of the column's total
 * (0-100) with its value. rows [{key, label (plain text), labelHtml, cells: {colKey: [{value, color}]}, cls}]: a cell
 * with several parts is a stacked bar (a subtotal). cols [{key, label, labelHtml, short (label on phones), kind, fmt}]:
 * a column of kind "num" shows its value (formatted by its fmt) without a bar. opts: fmt, tipFmt(row, col) -> html. */
function barTable(container, rows, cols, opts = {}) {
  container._xl = { kind: "bartable", rows, cols, opts };
  const f = opts.fmt || ((v) => `${fmt(v, 1)}%`);
  const total = (parts) => (parts.some((p) => isNum(p.value)) ? parts.reduce((a, p) => a + (isNum(p.value) ? p.value : 0), 0) : null);
  container.innerHTML = `<table class="bartable"><thead><tr><th></th>${cols.map((c) => `<th scope="col"${c.kind === "num" ? ' class="numcol"' : ""}>${c.labelHtml || esc(c.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((r, i) => `<tr class="${r.cls || ""}"><th scope="row">${r.labelHtml || esc(r.label)}</th>${cols.map((c, j) => {
    const parts = r.cells[c.key] || [], v = total(parts);
    if (c.kind === "num") {
      const t = isNum(v) ? (c.fmt || f)(v) : "–";
      return `<td data-r="${i}" data-c="${j}" aria-label="${esc(`${r.label}, ${c.label}: ${isNum(v) ? t : "no data"}`)}"><span class="bt bt-num" data-label="${esc(c.short || c.label)}"><span class="bt-val">${esc(t)}</span></span></td>`;
    }
    const fills = parts.filter((p) => isNum(p.value) && p.value > 0).map((p) => `<span class="bt-fill" style="width:${Math.min(100, p.value)}%;background:${p.color}"></span>`).join("");
    return `<td data-r="${i}" data-c="${j}" aria-label="${esc(`${r.label}, ${c.label}: ${isNum(v) ? f(v) : "no data"}`)}"><span class="bt" data-label="${esc(c.short || c.label)}"><span class="bt-track">${fills}</span><span class="bt-val">${isNum(v) ? esc(f(v)) : "–"}</span></span></td>`;
  }).join("")}</tr>`).join("")}</tbody></table>`;
  container.querySelectorAll("td[data-r]").forEach((td) => {
    const tip = (ev) => showTip((opts.tipFmt || ((r, c) => esc(`${r.label}, ${c.label}`)))(rows[+td.dataset.r], cols[+td.dataset.c]), ev);
    td.addEventListener("pointermove", tip); td.addEventListener("pointerdown", tip);
    td.addEventListener("pointerleave", hideTip);
  });
}

/* A table view for a chart: head [text], rows [[text]]; numeric cells (class num) are right-aligned. */
function tableView(container, head, rows) {
  container.innerHTML = `<table class="data"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c, i) => `<td class="${i ? "num" : ""}">${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

/* Weighted least squares of y on x: {slope, intercept, r2}. */
function wls(xs, ys, ws) {
  let sw = 0, sx = 0, sy = 0;
  xs.forEach((x, i) => { sw += ws[i]; sx += ws[i] * x; sy += ws[i] * ys[i]; });
  if (!(sw > 0)) return null;
  const mx = sx / sw, my = sy / sw;
  let sxx = 0, sxy = 0, syy = 0;
  xs.forEach((x, i) => { sxx += ws[i] * (x - mx) ** 2; sxy += ws[i] * (x - mx) * (ys[i] - my); syy += ws[i] * (ys[i] - my) ** 2; });
  if (!(sxx > 0) || !(syy > 0)) return null;
  const slope = sxy / sxx;
  return { slope, intercept: my - slope * mx, r2: (sxy * sxy) / (sxx * syy) };
}

/* Share of the weighted variance of y explained by group means (the R-squared of y on group dummies). */
function groupR2(ys, ws, groups) {
  const sw = ws.reduce((a, w) => a + w, 0);
  if (!(sw > 0)) return null;
  const my = ys.reduce((a, y, i) => a + ws[i] * y, 0) / sw;
  const by = {};
  ys.forEach((y, i) => { const g = (by[groups[i]] ||= { w: 0, s: 0 }); g.w += ws[i]; g.s += ws[i] * y; });
  let tot = 0, within = 0;
  ys.forEach((y, i) => { const g = by[groups[i]]; tot += ws[i] * (y - my) ** 2; within += ws[i] * (y - g.s / g.w) ** 2; });
  return tot > 0 ? 1 - within / tot : null;
}

/* ---- Company returns by sector (both pages) -------------------------------------------------------------
 * A sector holds yearly sums from the ATO's company tax statistics: income, pbt (profit before tax), npat
 * (after tax), equity (assets less liabilities). Over the chosen years, a year counts when equity is positive
 * and the items are published; the sector's figures are averages over those years (so a year missing for one
 * sector does not shrink it), and the reasons for any left-out years are kept. k: cost of equity (per cent). */
function sectorStats(s, years, from, to, k, taxRate = 30) {
  const idx = years.map((y, i) => i).filter((i) => years[i] >= from && years[i] <= to);
  const ok = [], left = [];
  for (const i of idx) {
    if (![s.income[i], s.npat[i], s.equity[i]].every(isNum)) left.push({ year: years[i], why: "not published" });
    else if (s.equity[i] <= 0) left.push({ year: years[i], why: "liabilities exceed assets" });
    else ok.push(i);
  }
  if (!ok.length) return { left, n: 0 };
  const mean = (a) => ok.reduce((t, i) => t + a[i], 0) / ok.length;
  const E = mean(s.equity), N = mean(s.npat), I = mean(s.income), B = mean(s.pbt);
  const req = (k / 100) * E;
  const snp = N - req;
  return {
    n: ok.length, left, E, N, I, B, roe: (N / E) * 100, snp,
    normal: Math.max(0, Math.min(N, req)), superP: Math.max(0, snp),
    markup: I > 0 ? (Math.max(0, snp) / (1 - taxRate / 100) / I) * 100 : null,
  };
}
function groupStats(rows, taxRate = 30) {
  const t = rows.reduce((a, r) => ({ E: a.E + r.E, N: a.N + r.N, I: a.I + r.I, normal: a.normal + r.normal, superP: a.superP + r.superP, n: a.n + 1 }), { E: 0, N: 0, I: 0, normal: 0, superP: 0, n: 0 });
  return { ...t, roe: t.E > 0 ? (t.N / t.E) * 100 : null, superShare: t.normal + t.superP > 0 ? (t.superP / (t.normal + t.superP)) * 100 : null, markup: t.I > 0 ? (t.superP / (1 - taxRate / 100) / t.I) * 100 : null };
}
const fmtB = (v, d = 1) => (isNum(v) ? `$${fmt(v / 1000, d)}b` : "–");

/* ---- Plain-English definitions --------------------------------------------------------------------------
 * term(key, text) marks a word that has a definition: dotted underline; the definition shows on hover,
 * keyboard focus or tap, and screen readers get it as the button's description. An entry is [word, meaning]
 * or [word, meaning, examples]. Pages add their own entries (for example the barriers-to-entry groups) with
 * initTerms(). */
const TERMS = {
  gsp: ["Gross state product", "The value of everything produced in a state in a year: the state version of GDP."],
  real: ["Real", "Adjusted for inflation, so it shows changes in quantities rather than prices."],
  output: ["Output", "The value an industry creates: its sales less what it buys from other businesses to make them (gross value added)."],
  industry: ["Industry", "One of the 19 broad industries the ABS uses, such as Retail Trade or Mining (ANZSIC divisions)."],
  sector: ["Sector", "A narrower part of an industry, such as supermarkets or banks (an ANZSIC class, or a group of classes)."],
  fy: ["Financial year", "1 July to 30 June. 2014-15 runs from July 2014 to June 2015."],
  avgGrowth: ["Average annual growth", "The steady yearly rate that would take the first year's value to the last year's."],
  index100: ["Index", "Each line starts at 100 in the first year, so it shows growth from there: 120 means 20% higher."],
  pp: ["Percentage points", "The difference between two percentages: going from 10% to 12% is a rise of 2 percentage points."],
  entry: ["Entry rate", "New businesses in a year for every 100 businesses operating at the start of that year."],
  exit: ["Exit rate", "Businesses that closed in a year for every 100 operating at the start of that year."],
  netEntry: ["Net entry rate", "The entry rate less the exit rate. Above zero, the number of businesses grew."],
  churn: ["Churn", "The entry rate plus the exit rate: how much businesses turn over."],
  employing: ["Businesses with employees", "Businesses employing at least one person. Sole traders without staff, such as most rideshare drivers, are left out."],
  barriers: ["Barriers to entry", "Things that make it hard for new firms to start up and compete: networks that would be wasteful to duplicate, large economies of scale, or rules that limit who can operate."],
  nontraded: ["Non-traded private economy", "Private businesses that mostly compete within Australia. It leaves out farms, mines and factories, which face competition from imports and exports, and services run mostly by government."],
  companyIncome: ["Company income", "Total income reported in company tax returns, mostly from sales."],
  equity: ["Equity", "What shareholders own on paper: a company's assets less its debts and other liabilities (book value)."],
  profitAfterTax: ["Profit after tax", "Accounting profit less the tax the companies paid."],
  roe: ["Return on equity", "Profit after tax as a percentage of equity: the return shareholders earn on what they have put into the business."],
  weighted: ["Weighted by equity", "Sectors with more equity count for more in the average, so it reflects where most of the money is."],
  fit: ["Line of best fit", "The straight line that best follows the dots, giving more weight to sectors with more equity."],
  explains: ["How much a measure explains", "The share of the differences in returns between sectors that lines up with the measure (R²). 0% means none; 100% would mean all of it."],
  concentration: ["Concentration", "How much of an industry's sales its biggest firms make. Higher concentration can mean less competition, but not always."],
  topShare: ["Share of sales made by the biggest firms", "Worked out for each detailed industry, then averaged within each broad industry, with bigger industries counting for more."],
  blade: ["BLADE", "The ABS's confidential database of business tax and survey records. The RBA used it to calculate these figures; the firm-level data are not public."],
  coe: ["Cost of equity", "The return shareholders need, given the risk, to keep their money in a business. Here: the 10-year government bond rate plus 6 percentage points, the same for every sector."],
  bond: ["10-year bond rate", "The interest rate on 10-year Australian Government bonds: the return on an investment with almost no risk."],
  normalProfit: ["Normal profit", "Profit up to the cost of equity: what is needed to keep investors."],
  superProfit: ["Super-normal profit", "Profit above the cost of equity: more than investors need. If it lasts, it can be a sign of weak competition."],
  shortfall: ["Shortfall", "How far a sector's return falls short of the cost of equity."],
  markup: ["Mark-up", "How far prices are above full costs, including a normal return to shareholders, as a percentage of sales (Grattan's measure). Sectors earning less than the cost of equity count as zero."],
  markupRba: ["Mark-up (price over marginal cost)", "Price divided by the cost of making one more unit, averaged across firms. 1.25 means prices are 25% above that cost. Prices also have to cover fixed costs, so a mark-up above 1 is normal."],
  incomeYear: ["Income year", "The ATO's name for the financial year, 1 July to 30 June."],
  sfd: ["State final demand", "Spending in a state by households, businesses and governments. It leaves out trade with other states and countries."],
  hhc: ["Household spending", "What households spend on goods and services (household final consumption expenditure)."],
  unemp: ["Unemployment rate", "People looking for work as a percentage of everyone working or looking for work."],
  wpi: ["Wage Price Index", "Tracks pay rates for the same jobs over time, so changes in the mix of jobs don't move it."],
  seasonal: ["Seasonally adjusted", "Regular seasonal patterns, such as Christmas hiring, are removed so the underlying movement is clearer."],
  dwell: ["Dwelling approvals", "New homes approved for building: an early sign of construction to come."],
  commodity: ["Commodity price index", "The RBA's index of the prices of Australia's main commodity exports, such as iron ore, coal, gas and farm products, in Australian dollars."],
};
function term(key, text) {
  const t = TERMS[key];
  if (!t) return esc(text ?? key);
  return `<button type="button" class="term" data-term="${esc(key)}" aria-describedby="def-${esc(key)}">${esc(text ?? t[0])}</button>`;
}
function showTipAt(html, target) {
  TIP.innerHTML = html;
  TIP.hidden = false;
  const r = target.getBoundingClientRect(), w = TIP.offsetWidth, h = TIP.offsetHeight;
  let x = Math.min(window.innerWidth - w - 8, Math.max(8, r.left));
  let y = r.bottom + 6;
  if (y + h > window.innerHeight - 8) y = r.top - h - 6;
  TIP.style.left = `${x}px`;
  TIP.style.top = `${Math.max(8, y)}px`;
}
const termText = (t) => `${t[1]}${t[2] ? ` For example: ${t[2]}.` : ""}`;
function initTerms(extra = {}) {
  Object.assign(TERMS, extra);
  // Static markup marks a defined word as <span data-term="key">word</span>.
  document.querySelectorAll("span[data-term]").forEach((s) => { s.outerHTML = term(s.dataset.term, s.textContent); });
  const box = document.createElement("div");
  box.hidden = true;
  box.innerHTML = Object.entries(TERMS).map(([k, t]) => `<span id="def-${esc(k)}">${esc(termText(t))}</span>`).join("");
  document.body.appendChild(box);
  let pinned = null, pointer = "mouse";
  const show = (b) => {
    const t = TERMS[b.dataset.term];
    showTipAt(`<strong>${esc(t[0])}</strong><br>${esc(t[1])}${t[2] ? `<br><span class="tip-ex">For example: ${esc(t[2])}.</span>` : ""}`, b);
  };
  // Defined words, and legend chips whose series has a definition.
  const termOf = (e) => (e.target instanceof Element ? e.target.closest(".term, .chip[data-term]") : null);
  document.addEventListener("pointerdown", (e) => { pointer = e.pointerType; }, true);
  document.addEventListener("pointerover", (e) => { const b = termOf(e); if (b && e.pointerType === "mouse") show(b); });
  document.addEventListener("pointerout", (e) => { const b = termOf(e); if (b && b !== pinned && e.pointerType === "mouse") hideTip(); });
  document.addEventListener("focusin", (e) => { const b = termOf(e); if (b) show(b); });
  document.addEventListener("focusout", (e) => { if (termOf(e)) { pinned = null; hideTip(); } });
  document.addEventListener("click", (e) => {
    const b = termOf(e);
    // A mouse click on a chip toggles its series; hovering already shows the definition.
    if (b && b.classList.contains("chip") && pointer === "mouse") return;
    if (b) { pinned = b; show(b); } else if (pinned) { pinned = null; hideTip(); }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { pinned = null; hideTip(); } });
}
/* A list of every defined word on the page, for the footer. */
function glossaryHtml() {
  const keys = [...new Set([...document.querySelectorAll(".term, .chip[data-term]")].map((b) => b.dataset.term))].filter((k) => TERMS[k]);
  keys.sort((a, b) => TERMS[a][0].localeCompare(TERMS[b][0]));
  return `<dl class="glossary">${keys.map((k) => `<div><dt>${esc(TERMS[k][0])}</dt><dd>${esc(TERMS[k][1])}${TERMS[k][2] ? ` <span class="ex">For example: ${esc(TERMS[k][2])}.</span>` : ""}</dd></div>`).join("")}</dl>`;
}

/* "Source: ..." links under a chart. sources: {key: {label, url}}; keys: the datasets the chart uses. */
function sourceHtml(sources, keys) {
  const links = keys.filter((k) => sources[k]).map((k) => `<a href="${esc(sources[k].url)}" target="_blank" rel="noopener" data-src="${esc(k)}">${esc(sources[k].label)}</a>`);
  return links.length ? `Source${links.length > 1 ? "s" : ""}: ${links.join("; ")}.` : "";
}

/* Dumbbell rows: one row per item, a hollow dot for the first value and a filled dot for the last, joined by a
 * line, with the change written at the end. Rows are buttons (select one with onSelect).
 * rows [{key, label, a, b, total}], opts: {domain: [lo, hi], fmt, fmtChange, selected, onSelect, aLabel, bLabel}. */
function dumbbellChart(container, rows, opts) {
  container._xl = { kind: "dumbbell", rows, opts };
  const [lo, hi] = opts.domain;
  const pos = (v) => ((Math.min(hi, Math.max(lo, v)) - lo) / Math.max(1e-9, hi - lo)) * 100;
  const ticks = niceTicks(lo, hi, 5).filter((t) => t >= lo && t <= hi);
  const fmtV = opts.fmt || ((v) => fmt(v, 1)), fmtC = opts.fmtChange || ((v) => fmtSigned(v, 1));
  const grid = ticks.map((t) => `<span class="db-grid" style="left:${pos(t)}%"></span>`).join("");
  const head = `<div class="db-head" aria-hidden="true"><span></span><span class="db-axis">${ticks.map((t) => `<span style="left:${pos(t)}%">${esc(fmtV(t).replace(/\.0$/, ""))}</span>`).join("")}</span><span class="db-val">Change</span></div>`;
  container.innerHTML = head + rows.map((r) => {
    const ok = isNum(r.a) && isNum(r.b);
    const a = ok ? pos(r.a) : 0, b = ok ? pos(r.b) : 0;
    const label = `${r.label}: ${ok ? `${fmtV(r.a)} in ${opts.aLabel}, ${fmtV(r.b)} in ${opts.bLabel}, change ${fmtC(r.b - r.a)}` : "no data"}`;
    return `<button type="button" class="db-row${r.total ? " total" : ""}" data-key="${esc(r.key)}" aria-pressed="${r.key === opts.selected}" aria-label="${esc(label)}">
      <span class="db-lab">${esc(r.label)}</span>
      <span class="db-track">${grid}${ok ? `<span class="db-seg" style="left:${Math.min(a, b)}%;width:${Math.abs(b - a)}%"></span><span class="db-dot a" style="left:${a}%"></span><span class="db-dot b" style="left:${b}%"></span>` : ""}</span>
      <span class="db-val">${ok ? `${esc(fmtC(r.b - r.a))}` : "–"}</span></button>`;
  }).join("");
  container.querySelectorAll(".db-row").forEach((btn) => {
    const r = rows.find((x) => x.key === btn.dataset.key);
    btn.addEventListener("click", () => opts.onSelect && opts.onSelect(btn.dataset.key));
    const tip = (ev) => showTip(`<strong>${esc(r.label)}</strong><table><tr><td>${esc(opts.aLabel)}</td><td class="v">${esc(fmtV(r.a))}</td></tr><tr><td>${esc(opts.bLabel)}</td><td class="v">${esc(fmtV(r.b))}</td></tr><tr><td>Change</td><td class="v">${esc(fmtC(r.b - r.a))}</td></tr></table>`, ev);
    btn.addEventListener("pointermove", tip);
    btn.addEventListener("pointerleave", hideTip);
  });
}

/* Three-circle Venn of the tiers of government in a regulatory regime: Commonwealth (top left), state or territory
   (top right) and local council (bottom). regions: {key: [{label, title, hot}]}, keyed by the tiers that share the
   region joined with "+" in the order cth, state, local (e.g. "state+local"). A tier in no region is drawn dashed.
   opts.names: {cth, state, local} labels; opts.max: labels listed per region before "+n more"; opts.count: show
   each region's number of items instead of their labels (for many regimes at once). Returns an SVG string: text is
   in ink colours; each circle is named directly beside it, so identity never rests on colour alone. */
const VENN_TIERS = ["cth", "state", "local"];
function vennSvg(regions, opts = {}) {
  const names = opts.names || { cth: "Commonwealth", state: "State or territory", local: "Local council" };
  const max = opts.max || 3;
  const C = { cth: [112, 100], state: [196, 100], local: [154, 172] };
  const R = 76;
  const AT = { cth: [78, 84], state: [230, 84], local: [154, 212], "cth+state": [154, 76], "cth+local": [105, 149],
    "state+local": [203, 149], "cth+state+local": [154, 124] };
  const used = new Set(Object.keys(regions).filter((k) => regions[k].length).flatMap((k) => k.split("+")));
  const parts = [];
  VENN_TIERS.forEach((t) => {
    const [cx, cy] = C[t], on = used.has(t);
    parts.push(`<circle cx="${cx}" cy="${cy}" r="${R}" class="vc vc-${t}${on ? "" : " off"}"/>`);
  });
  const lab = { cth: [18, 18, "start"], state: [290, 18, "end"], local: [154, 266, "middle"] };
  VENN_TIERS.forEach((t) => {
    const [x, y, anchor] = lab[t];
    const sw = anchor === "start" ? x : anchor === "end" ? x - (names[t].length * 6.4 + 14) : x - (names[t].length * 3.2 + 7);
    parts.push(`<circle cx="${sw + 5}" cy="${y - 4}" r="5" class="vc-key vc-${t}${used.has(t) ? "" : " off"}"/>`);
    parts.push(`<text x="${anchor === "start" ? x + 14 : anchor === "end" ? x : x + 7}" y="${y}" text-anchor="${anchor}" class="vt${used.has(t) ? "" : " off"}">${esc(names[t])}${used.has(t) ? "" : " (none)"}</text>`);
  });
  Object.entries(regions).forEach(([key, items]) => {
    if (!items.length || !AT[key]) return;
    const [x, y] = AT[key];
    const hot = key.includes("+");
    const all = items.map((i) => i.title || i.label).join("\n");
    if (opts.count) {
      parts.push(`<g class="vg${hot ? " hot" : ""}" tabindex="0"><title>${esc(all)}</title><text x="${x}" y="${y + 2}" text-anchor="middle" class="vn">${items.length}</text></g>`);
      return;
    }
    const shown = items.length > max ? items.slice(0, max - 1) : items;
    const lines = shown.map((i) => ({ text: i.label, title: i.title || i.label, hot: i.hot }));
    if (items.length > shown.length) lines.push({ text: `+${items.length - shown.length} more`, title: all, hot: false });
    const y0 = y - ((lines.length - 1) * 13) / 2 + 4;
    lines.forEach((l, n) => parts.push(`<text x="${x}" y="${y0 + n * 13}" text-anchor="middle" class="vl${l.hot ? " hot" : ""}"><title>${esc(l.title)}</title>${esc(l.text)}</text>`));
  });
  return `<svg class="venn" viewBox="0 0 308 274" role="img" aria-label="${esc(opts.label || "Which tiers of government do what")}">${parts.join("")}</svg>`;
}
