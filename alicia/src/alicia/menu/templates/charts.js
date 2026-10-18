/* Shared chart helpers for the ALICIA summary pages. Inline SVG, no libraries. */
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
 * opts: x (numbers: years, or UTC ms), xKind ("fy" | "month" | "quarter"), series [{key, label, values, color, dash, width}],
 * yFmt (value -> text), ref (y value for a dashed reference line), markers [{x, label}], height, yLabel, tipDigits.
 */
function lineChart(container, opts) {
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
    const ticks = niceTicks(lo, hi, H > 240 ? 5 : 4);
    const y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const x0 = xs[0], x1 = xs[xs.length - 1];
    const sx = (x) => m.l + ((x - x0) / Math.max(1e-9, x1 - x0)) * (W - m.l - m.r);
    const sy = (v) => H - m.b - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - m.t - m.b);
    const yFmt = opts.yFmt || ((v) => fmt(v, 0));

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
    if (opts.xKind === "fy") {
      const span = x1 - x0;
      const step = [1, 2, 5, 10].find((s) => span / s <= maxTicks) || 10;
      for (let y = Math.ceil(x0 / step) * step; y <= x1; y += step) {
        el("line", { x1: sx(y), x2: sx(y), y1: H - m.b, y2: H - m.b + 4 }, axis);
        el("text", { x: sx(y), y: H - 8, "text-anchor": "middle" }, axis).textContent = fyLabel(y);
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
        "stroke-dasharray": s.dash ? "5 4" : null, "stroke-linejoin": "round", "stroke-linecap": "round",
      }, svg);
    }

    // Hover readout.
    const cross = el("line", { class: "cross", y1: m.t, y2: H - m.b, visibility: "hidden" }, svg);
    const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
    const xLabel = opts.xKind === "fy" ? fyLabel : opts.xKind === "quarter" ? quarterLabel : monthLabel;
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

/* Horizontal bars around zero, sorted by the caller. rows: [{label, value, title}] */
function rankedBars(container, rows, opts = {}) {
  const vals = rows.map((r) => r.value).filter(isNum);
  const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const span = Math.max(1e-9, hi - lo);
  const pos = (v) => ((v - lo) / span) * 100;
  container.innerHTML = rows.map((r) => {
    const ok = isNum(r.value);
    const a = ok ? pos(Math.min(0, r.value)) : 0, b = ok ? pos(Math.max(0, r.value)) : 0;
    const color = ok && r.value < 0 ? "var(--neg)" : "var(--pos)";
    return `<div class="row" title="${esc(r.title || r.label)}"><span class="lab">${esc(r.label)}</span>
      <span class="track"><span class="axis0" style="left:${pos(0)}%"></span>${ok ? `<span class="fill" style="left:${a}%;width:${Math.max(0.5, b - a)}%;background:${color}"></span>` : ""}</span>
      <span class="val">${ok ? esc((opts.fmt || fmtSigned)(r.value)) : "–"}</span></div>`;
  }).join("");
}

/* Cell shading: diverging (growth) or sequential (shares), mixed into the surface colour so text stays legible. */
function heatColor(v, scale, kind = "div") {
  if (!isNum(v)) return "transparent";
  const p = Math.round(Math.min(1, Math.abs(v) / Math.max(1e-9, scale)) * 58);
  const base = kind === "seq" ? "var(--seq)" : v < 0 ? "var(--neg)" : "var(--pos)";
  return `color-mix(in oklab, ${base} ${p}%, var(--surface))`;
}

/* Legend chips that toggle series. keys: [{key, label, color, dash}]; state: Set of active keys. */
function toggleChips(container, keys, active, onChange) {
  container.innerHTML = keys.map((k) => `<button type="button" class="chip" data-key="${esc(k.key)}" aria-pressed="${active.has(k.key)}">
    <span class="key${k.dash ? " dash" : ""}" style="${k.dash ? `color:${k.color}` : `background:${k.color}`}"></span>${esc(k.label)}</button>`).join("");
  container.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
    const key = b.dataset.key;
    if (active.has(key)) active.delete(key); else active.add(key);
    b.setAttribute("aria-pressed", active.has(key));
    onChange();
  }));
}

const stateColor = (s) => `var(--s-${s})`;
