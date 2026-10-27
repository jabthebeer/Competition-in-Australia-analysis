/* Excel export for the ALICIA summary pages, with no libraries: a small XLSX writer (an uncompressed zip, inline
 * strings, and native Excel charts drawn from the sheet's own cells) and a "Download Excel" button for chart cards.
 * A workbook has a sheet per chart, holding the chart and the numbers behind it, and an About sheet: the page settings
 * in use, each data source with its link, release and licence, the notes and the definitions.
 * The writer (xlsxWorkbook and the functions it calls) does not touch the page, so it can be tested on its own. */

const xlNum = (v) => typeof v === "number" && Number.isFinite(v);
const xlEsc = (s) => String(s ?? "")
  .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F￾￿]/g, "")
  .replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';
const XL_NS = {
  main: "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
  r: "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
  rel: "http://schemas.openxmlformats.org/package/2006/relationships",
  c: "http://schemas.openxmlformats.org/drawingml/2006/chart",
  a: "http://schemas.openxmlformats.org/drawingml/2006/main",
  xdr: "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
};
const XL_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const XL_CT = "application/vnd.openxmlformats-officedocument";

/* ---- zip (stored) ------------------------------------------------------------------------------------------- */
const XL_CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
  return t;
})();
function xlCrc32(bytes) {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = XL_CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
/* files: [{name, data (string or bytes)}] -> the zip as bytes. */
function xlZip(files, when) {
  const enc = new TextEncoder();
  const time = (when.getHours() << 11) | (when.getMinutes() << 5) | (when.getSeconds() >> 1);
  const date = ((Math.max(1980, when.getFullYear()) - 1980) << 9) | ((when.getMonth() + 1) << 5) | when.getDate();
  const local = [], central = [];
  let offset = 0;
  for (const f of files) {
    const name = enc.encode(f.name), data = typeof f.data === "string" ? enc.encode(f.data) : f.data;
    const crc = xlCrc32(data);
    const h = new DataView(new ArrayBuffer(30));
    h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true);
    h.setUint16(10, time, true); h.setUint16(12, date, true); h.setUint32(14, crc, true);
    h.setUint32(18, data.length, true); h.setUint32(22, data.length, true); h.setUint16(26, name.length, true);
    local.push(new Uint8Array(h.buffer), name, data);
    const d = new DataView(new ArrayBuffer(46));
    d.setUint32(0, 0x02014b50, true); d.setUint16(4, 20, true); d.setUint16(6, 20, true); d.setUint16(8, 0x0800, true);
    d.setUint16(12, time, true); d.setUint16(14, date, true); d.setUint32(16, crc, true);
    d.setUint32(20, data.length, true); d.setUint32(24, data.length, true); d.setUint16(28, name.length, true);
    d.setUint32(42, offset, true);
    central.push(new Uint8Array(d.buffer), name);
    offset += 30 + name.length + data.length;
  }
  const size = central.reduce((a, p) => a + p.length, 0);
  const e = new DataView(new ArrayBuffer(22));
  e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true);
  e.setUint32(12, size, true); e.setUint32(16, offset, true);
  const parts = [...local, ...central, new Uint8Array(e.buffer)];
  const out = new Uint8Array(parts.reduce((a, p) => a + p.length, 0));
  let at = 0;
  for (const p of parts) { out.set(p, at); at += p.length; }
  return out;
}

/* ---- cells and styles ----------------------------------------------------------------------------------------- */
const xlCol = (i) => { let s = ""; for (let n = i + 1; n > 0; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + ((n - 1) % 26)) + s; return s; };
const xlRef = (c, r) => `${xlCol(c)}${r + 1}`;
const xlAbs = (sheet, c0, r0, c1 = c0, r1 = r0) =>
  `'${sheet.replace(/'/g, "''")}'!$${xlCol(c0)}$${r0 + 1}${c1 === c0 && r1 === r0 ? "" : `:$${xlCol(c1)}$${r1 + 1}`}`;
/* Days since 30 December 1899 (Excel's date numbers) for a UTC time in milliseconds. */
const xlSerial = (t) => t / 86400000 + 25569;

const XL_NUMFMTS = ["0.0", "0.00", "0.000", "#,##0", "#,##0.0", "+0.0;-0.0;0.0", "+0.00;-0.00;0.00", "+0.000;-0.000;0.000", "mmm yyyy"];
// Named cell formats: [name, font, fill, border, number format, alignment].
const XL_BASE = [
  ["normal", 0, 0, 0, 0, ""],
  ["title", 2, 0, 0, 0, ""],
  ["sub", 3, 0, 0, 0, ""],
  ["head", 1, 2, 1, 0, '<alignment wrapText="1" vertical="bottom"/>'],
  ["headNum", 1, 2, 1, 0, '<alignment wrapText="1" vertical="bottom" horizontal="right"/>'],
  ["wrap", 0, 0, 0, 0, '<alignment wrapText="1" vertical="top"/>'],
  ["label", 1, 0, 0, 0, '<alignment wrapText="1" vertical="top"/>'],
  ["link", 4, 0, 0, 0, '<alignment vertical="top"/>'],
  ["section", 5, 0, 0, 0, ""],
  ["int", 0, 0, 0, 1, ""],
];
const XL_STYLE = Object.fromEntries([
  ...XL_BASE.map(([n], i) => [n, i]),
  ...XL_NUMFMTS.map((f, i) => [`n:${f}`, XL_BASE.length + i]),
  ["n:0", XL_BASE.findIndex(([n]) => n === "int")],
]);
function xlStylesXml() {
  const font = (extra, sz, rgb) => `<font>${extra}<sz val="${sz}"/><color rgb="FF${rgb}"/><name val="Calibri"/><family val="2"/></font>`;
  const fonts = [font("", 11, "1B1C1A"), font("<b/>", 11, "1B1C1A"), font("<b/>", 14, "1B1C1A"), font("", 10, "52514E"), font("<u/>", 11, "0563C1"), font("<b/>", 12, "1D5C57")];
  const fills = ['<fill><patternFill patternType="none"/></fill>', '<fill><patternFill patternType="gray125"/></fill>',
    '<fill><patternFill patternType="solid"><fgColor rgb="FFEEEEEA"/><bgColor indexed="64"/></patternFill></fill>'];
  const borders = ["<border><left/><right/><top/><bottom/><diagonal/></border>",
    '<border><left/><right/><top/><bottom style="thin"><color rgb="FFC3C2B7"/></bottom><diagonal/></border>'];
  const xf = (f, fi, b, n, al) => `<xf numFmtId="${n}" fontId="${f}" fillId="${fi}" borderId="${b}" xfId="0"${f ? ' applyFont="1"' : ""}${fi ? ' applyFill="1"' : ""}${b ? ' applyBorder="1"' : ""}${n ? ' applyNumberFormat="1"' : ""}${al ? ` applyAlignment="1">${al}</xf>` : "/>"}`;
  const xfs = [...XL_BASE.map(([, f, fi, b, n, al]) => xf(f, fi, b, n, al)), ...XL_NUMFMTS.map((_, i) => xf(0, 0, 0, 164 + i, ""))];
  return `${XML_HEAD}<styleSheet xmlns="${XL_NS.main}"><numFmts count="${XL_NUMFMTS.length}">${XL_NUMFMTS.map((f, i) => `<numFmt numFmtId="${164 + i}" formatCode="${xlEsc(f)}"/>`).join("")}</numFmts>`
    + `<fonts count="${fonts.length}">${fonts.join("")}</fonts><fills count="${fills.length}">${fills.join("")}</fills><borders count="${borders.length}">${borders.join("")}</borders>`
    + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    + `<cellXfs count="${xfs.length}">${xfs.join("")}</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles><dxfs count="0"/><tableStyles count="0"/></styleSheet>`;
}

/* sheet: {name, widths [characters], cells [{r, c, v, s}], links [{r, c, url}], scales [{sqref, stops [[value, hex]]}],
 * charts [{from, to, chart}]}; rows and columns count from 0. */
function xlSheetXml(sh, selected, hasDrawing) {
  const byRow = new Map();
  for (const x of sh.cells) { if (!byRow.has(x.r)) byRow.set(x.r, []); byRow.get(x.r).push(x); }
  const rows = [...byRow.keys()].sort((a, b) => a - b).map((r) => {
    const cells = byRow.get(r).sort((a, b) => a.c - b.c).map((x) => {
      const ref = xlRef(x.c, x.r), s = x.s ? ` s="${x.s}"` : "";
      if (xlNum(x.v)) return `<c r="${ref}"${s}><v>${x.v}</v></c>`;
      if (x.v === null || x.v === undefined || x.v === "") return x.s ? `<c r="${ref}"${s}/>` : "";
      return `<c r="${ref}"${s} t="inlineStr"><is><t xml:space="preserve">${xlEsc(x.v)}</t></is></c>`;
    }).join("");
    return `<row r="${r + 1}">${cells}</row>`;
  }).join("");
  const cols = (sh.widths || []).map((w, i) => (xlNum(w) ? `<col min="${i + 1}" max="${i + 1}" width="${w}" customWidth="1"/>` : "")).join("");
  const scales = (sh.scales || []).map((cs, i) => `<conditionalFormatting sqref="${cs.sqref}"><cfRule type="colorScale" priority="${i + 1}"><colorScale>${cs.stops.map(([v]) => `<cfvo type="num" val="${v}"/>`).join("")}${cs.stops.map(([, hex]) => `<color rgb="FF${xlHex(hex)}"/>`).join("")}</colorScale></cfRule></conditionalFormatting>`).join("");
  const links = (sh.links || []).length ? `<hyperlinks>${sh.links.map((l, i) => `<hyperlink ref="${xlRef(l.c, l.r)}" r:id="rIdL${i + 1}"/>`).join("")}</hyperlinks>` : "";
  return `${XML_HEAD}<worksheet xmlns="${XL_NS.main}" xmlns:r="${XL_NS.r}"><sheetPr><pageSetUpPr fitToPage="1"/></sheetPr><sheetViews><sheetView workbookViewId="0"${selected ? ' tabSelected="1"' : ""}/></sheetViews>`
    + `<sheetFormatPr defaultRowHeight="15"/>${cols ? `<cols>${cols}</cols>` : ""}<sheetData>${rows}</sheetData>${scales}${links}`
    + `<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/><pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="0"/>${hasDrawing ? '<drawing r:id="rIdD1"/>' : ""}</worksheet>`;
}

/* ---- charts ------------------------------------------------------------------------------------------------------ */
const XL_INK = "#1B1C1A", XL_INK2 = "#52514E", XL_GRID = "#EBEAE4", XL_AXIS = "#C3C2B7";
const xlHex = (c) => String(c || XL_INK2).replace("#", "").toUpperCase();
const xlFill = (hex, alpha) => (hex === null ? "<a:noFill/>" : `<a:solidFill><a:srgbClr val="${xlHex(hex)}">${xlNum(alpha) && alpha < 1 ? `<a:alpha val="${Math.round(alpha * 100000)}"/>` : ""}</a:srgbClr></a:solidFill>`);
const xlLn = (hex, pt = 0.75, dash) => `<a:ln w="${Math.round(pt * 12700)}" cap="rnd">${hex === null ? "<a:noFill/>" : xlFill(hex)}${dash ? `<a:prstDash val="${dash}"/>` : ""}<a:round/></a:ln>`;
const xlTxPr = (sz, hex, rot) => `<c:txPr><a:bodyPr${rot ? ` rot="${rot}" vert="horz"` : ""}/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="${sz}" b="0">${xlFill(hex)}</a:defRPr></a:pPr><a:endParaRPr lang="en-AU"/></a:p></c:txPr>`;
const xlRich = (text, sz, bold, rot) => `<c:title><c:tx><c:rich><a:bodyPr${rot ? ` rot="${rot}" vert="horz"` : ""}/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="${sz}" b="${bold ? 1 : 0}"/></a:pPr><a:r><a:rPr lang="en-AU" sz="${sz}" b="${bold ? 1 : 0}">${xlFill(bold ? XL_INK : XL_INK2)}</a:rPr><a:t>${xlEsc(text)}</a:t></a:r></a:p></c:rich></c:tx><c:overlay val="0"/></c:title>`;
const xlStrRef = (ref, vals) => `<c:strRef><c:f>${xlEsc(ref)}</c:f><c:strCache><c:ptCount val="${vals.length}"/>${vals.map((v, i) => `<c:pt idx="${i}"><c:v>${xlEsc(v)}</c:v></c:pt>`).join("")}</c:strCache></c:strRef>`;
const xlNumRef = (ref, vals, fmt = "General") => `<c:numRef><c:f>${xlEsc(ref)}</c:f><c:numCache><c:formatCode>${xlEsc(fmt)}</c:formatCode><c:ptCount val="${vals.length}"/>${vals.map((v, i) => (xlNum(v) ? `<c:pt idx="${i}"><c:v>${v}</c:v></c:pt>` : "")).join("")}</c:numCache></c:numRef>`;
const xlMarker = (hex, size, alpha, hollow) => `<c:marker><c:symbol val="circle"/><c:size val="${Math.max(2, Math.min(72, Math.round(size || 7)))}"/><c:spPr>${hollow ? "<a:noFill/>" : xlFill(hex, alpha)}${xlLn(hollow ? hex : "#FFFFFF", hollow ? 1.5 : 0.75)}</c:spPr></c:marker>`;
function xlDLbls(l) {
  const hide = (l.hide || []).map((i) => `<c:dLbl><c:idx val="${i}"/><c:delete val="1"/></c:dLbl>`).join("");
  return `<c:dLbls>${hide}<c:numFmt formatCode="${xlEsc(l.fmt || "General")}" sourceLinked="0"/><c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>${xlTxPr(800, l.color || XL_INK2)}`
    + `${l.pos ? `<c:dLblPos val="${l.pos}"/>` : ""}<c:showLegendKey val="0"/><c:showVal val="1"/><c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbls>`;
}
/* A series, resolved: {name, nameRef, cat {ref, vals, kind "str" | "num", fmt}, val {ref, vals}, xv (scatter x),
 * color, width (points), dash (preset), alpha, outline, line (scatter: draw a line, no markers), size, points
 * [{idx, color, size, alpha, hollow}], labels {fmt, pos, hide, color}}. */
function xlSerXml(type, s, idx) {
  const tx = s.nameRef ? `<c:tx>${xlStrRef(s.nameRef, [s.name])}</c:tx>` : `<c:tx><c:v>${xlEsc(s.name)}</c:v></c:tx>`;
  let sp, marker = "", inv = "";
  if (type === "line") {
    sp = `<c:spPr>${xlLn(s.color, s.width || 1.4, s.dash)}</c:spPr>`;
    marker = '<c:marker><c:symbol val="none"/></c:marker>';
  } else if (type === "bar") {
    sp = `<c:spPr>${xlFill(s.color, s.alpha)}${s.outline ? xlLn(s.outline, 1) : "<a:ln><a:noFill/></a:ln>"}</c:spPr>`;
    inv = '<c:invertIfNegative val="0"/>';
  } else {
    sp = `<c:spPr>${s.line ? xlLn(s.color, s.width || 1, s.dash) : '<a:ln w="19050"><a:noFill/></a:ln>'}</c:spPr>`;
    marker = s.line ? '<c:marker><c:symbol val="none"/></c:marker>' : xlMarker(s.color, s.size, s.alpha);
  }
  const pts = (s.points || []).map((d) => (type === "bar"
    ? `<c:dPt><c:idx val="${d.idx}"/><c:invertIfNegative val="0"/><c:bubble3D val="0"/><c:spPr>${xlFill(d.color, d.alpha)}<a:ln><a:noFill/></a:ln></c:spPr></c:dPt>`
    : `<c:dPt><c:idx val="${d.idx}"/>${xlMarker(d.color ?? s.color, d.size ?? s.size, d.alpha ?? s.alpha, d.hollow)}<c:bubble3D val="0"/></c:dPt>`)).join("");
  const lbls = s.labels ? xlDLbls(s.labels) : "";
  const data = type === "scatter"
    ? `<c:xVal>${xlNumRef(s.xv.ref, s.xv.vals)}</c:xVal><c:yVal>${xlNumRef(s.val.ref, s.val.vals)}</c:yVal><c:smooth val="0"/>`
    : `<c:cat>${s.cat.kind === "num" ? xlNumRef(s.cat.ref, s.cat.vals, s.cat.fmt) : xlStrRef(s.cat.ref, s.cat.vals)}</c:cat><c:val>${xlNumRef(s.val.ref, s.val.vals)}</c:val>${type === "line" ? '<c:smooth val="0"/>' : ""}`;
  return `<c:ser><c:idx val="${idx}"/><c:order val="${idx}"/>${tx}${sp}${inv}${marker}${pts}${lbls}${data}</c:ser>`;
}
const XL_AX = { cat: 500001, val: 500002 };
function xlPlotXml(p, first) {
  const ids = [XL_AX.cat, XL_AX.val];
  const sers = p.series.map((s, i) => xlSerXml(p.type, s, first + i)).join("");
  const ax = `<c:axId val="${ids[0]}"/><c:axId val="${ids[1]}"/>`;
  if (p.type === "line") return `<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>${sers}<c:marker val="1"/>${ax}</c:lineChart>`;
  if (p.type === "scatter") return `<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>${sers}${ax}</c:scatterChart>`;
  const stacked = p.grouping === "stacked" || p.grouping === "percentStacked";
  return `<c:barChart><c:barDir val="${p.dir || "col"}"/><c:grouping val="${p.grouping || "clustered"}"/><c:varyColors val="0"/>${sers}`
    + `<c:gapWidth val="${p.gap ?? 60}"/>${stacked ? '<c:overlap val="100"/>' : xlNum(p.overlap) ? `<c:overlap val="${p.overlap}"/>` : ""}${ax}</c:barChart>`;
}
/* ch: {title, plots [{type "line" | "bar" | "scatter", dir "col" | "bar", grouping, gap, overlap, series}],
 * x {kind "cat" | "date" | "val", reverse, title, min, max, unit (years between date labels)}, y {title, min, max},
 * legend, hideLegend [series index]}. All plots share one pair of axes. */
function xlChartXml(ch) {
  let n = 0;
  const plots = ch.plots.map((p) => { const x = xlPlotXml(p, n); n += p.series.length; return x; }).join("");
  const horiz = ch.plots.some((p) => p.type === "bar" && p.dir === "bar");
  const tx = xlTxPr(900, XL_INK2), axisLine = `<c:spPr>${xlLn(XL_AXIS, 0.75)}</c:spPr>`;
  const scaling = (a) => `<c:scaling><c:orientation val="${a.reverse ? "maxMin" : "minMax"}"/>${xlNum(a.max) ? `<c:max val="${a.max}"/>` : ""}${xlNum(a.min) ? `<c:min val="${a.min}"/>` : ""}</c:scaling>`;
  const title = (t, vertical) => (t ? xlRich(t, 900, false, vertical ? -5400000 : 0) : "");
  const x = ch.x || {}, y = ch.y || {};
  let xAx;
  if (x.kind === "val") {
    xAx = `<c:valAx><c:axId val="${XL_AX.cat}"/>${scaling(x)}<c:delete val="0"/><c:axPos val="b"/>${title(x.title)}<c:numFmt formatCode="General" sourceLinked="0"/>`
      + `<c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="low"/>${axisLine}${tx}<c:crossAx val="${XL_AX.val}"/><c:crosses val="autoZero"/><c:crossBetween val="midCat"/></c:valAx>`;
  } else if (x.kind === "date") {
    xAx = `<c:dateAx><c:axId val="${XL_AX.cat}"/>${scaling(x)}<c:delete val="0"/><c:axPos val="b"/>${title(x.title)}<c:numFmt formatCode="yyyy" sourceLinked="0"/>`
      + `<c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="low"/>${axisLine}${tx}<c:crossAx val="${XL_AX.val}"/><c:crosses val="autoZero"/>`
      + `<c:auto val="0"/><c:lblOffset val="100"/><c:baseTimeUnit val="months"/><c:majorUnit val="${x.unit || 1}"/><c:majorTimeUnit val="years"/></c:dateAx>`;
  } else {
    xAx = `<c:catAx><c:axId val="${XL_AX.cat}"/>${scaling(x)}<c:delete val="0"/><c:axPos val="${horiz ? "l" : "b"}"/>${title(x.title, horiz)}<c:numFmt formatCode="General" sourceLinked="0"/>`
      + `<c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="low"/>${axisLine}${tx}<c:crossAx val="${XL_AX.val}"/><c:crosses val="autoZero"/>`
      + '<c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>';
  }
  // With the categories of a horizontal bar chart running top to bottom, the value axis crosses at the last one so
  // it stays at the bottom.
  const yAx = `<c:valAx><c:axId val="${XL_AX.val}"/>${scaling({ min: y.min, max: y.max })}<c:delete val="0"/><c:axPos val="${horiz ? "b" : "l"}"/>`
    + `<c:majorGridlines><c:spPr>${xlLn(XL_GRID, 0.75)}</c:spPr></c:majorGridlines>${title(y.title, !horiz)}<c:numFmt formatCode="${xlEsc(y.fmt || "General")}" sourceLinked="0"/>`
    + `<c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/><c:spPr><a:ln><a:noFill/></a:ln></c:spPr>${tx}`
    + `<c:crossAx val="${XL_AX.cat}"/><c:crosses val="${horiz && x.reverse ? "max" : "autoZero"}"/><c:crossBetween val="${x.kind === "val" ? "midCat" : "between"}"/></c:valAx>`;
  const legend = ch.legend
    ? `<c:legend><c:legendPos val="b"/>${(ch.hideLegend || []).map((i) => `<c:legendEntry><c:idx val="${i}"/><c:delete val="1"/></c:legendEntry>`).join("")}<c:overlay val="0"/>${xlTxPr(900, XL_INK)}</c:legend>`
    : "";
  return `${XML_HEAD}<c:chartSpace xmlns:c="${XL_NS.c}" xmlns:a="${XL_NS.a}" xmlns:r="${XL_NS.r}"><c:date1904 val="0"/><c:lang val="en-AU"/><c:roundedCorners val="0"/>`
    + `<c:chart>${ch.title ? xlRich(ch.title, 1200, true) : ""}<c:autoTitleDeleted val="${ch.title ? 0 : 1}"/><c:plotArea><c:layout/>${plots}${xAx}${yAx}`
    + `<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr></c:plotArea>${legend}<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>`
    + `<c:spPr>${xlFill("#FFFFFF")}<a:ln><a:noFill/></a:ln></c:spPr><c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="900"/></a:pPr><a:endParaRPr lang="en-AU"/></a:p></c:txPr></c:chartSpace>`;
}
const xlColPx = (sh, c) => Math.round((xlNum(sh.widths?.[c]) ? sh.widths[c] : 8.43) * 7 + 5);
/* Cells covered by a chart w x h pixels whose top-left corner is at cell (c, r), with default 20-pixel rows. */
function xlAnchor(sh, c, r, w, h) {
  let col = c, x = w;
  while (x > xlColPx(sh, col)) { x -= xlColPx(sh, col); col++; }
  return { from: { c, r }, to: { c: col, dx: Math.round(x * 9525), r: r + Math.floor(h / 20), dy: Math.round((h % 20) * 9525) } };
}
function xlDrawingXml(charts, firstId) {
  const pos = (tag, p, dx = 0, dy = 0) => `<xdr:${tag}><xdr:col>${p.c}</xdr:col><xdr:colOff>${dx}</xdr:colOff><xdr:row>${p.r}</xdr:row><xdr:rowOff>${dy}</xdr:rowOff></xdr:${tag}>`;
  return `${XML_HEAD}<xdr:wsDr xmlns:xdr="${XL_NS.xdr}" xmlns:a="${XL_NS.a}">${charts.map((ch, i) => `<xdr:twoCellAnchor editAs="oneCell">${pos("from", ch.from)}${pos("to", ch.to, ch.to.dx, ch.to.dy)}`
    + `<xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="${firstId + i + 1}" name="Chart ${firstId + i}"/><xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr>`
    + '<xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
    + `<c:chart xmlns:c="${XL_NS.c}" xmlns:r="${XL_NS.r}" r:id="rIdC${i + 1}"/></a:graphicData></a:graphic></xdr:graphicFrame><xdr:clientData/></xdr:twoCellAnchor>`).join("")}</xdr:wsDr>`;
}
const xlRels = (rels) => `${XML_HEAD}<Relationships xmlns="${XL_NS.rel}">${rels.map(([id, type, target, ext]) => `<Relationship Id="${id}" Type="${type}" Target="${xlEsc(target)}"${ext ? ' TargetMode="External"' : ""}/>`).join("")}</Relationships>`;

/* book: {title, sheets: [sheet]} (see xlSheetXml) -> the .xlsx file as bytes. */
function xlsxWorkbook(book, when = new Date()) {
  const files = [], over = [];
  let nChart = 0, nDrawing = 0;
  book.sheets.forEach((sh, i) => {
    const n = i + 1, rels = [];
    (sh.links || []).forEach((l, k) => rels.push([`rIdL${k + 1}`, `${XL_REL}/hyperlink`, l.url, true]));
    const charts = sh.charts || [];
    if (charts.length) {
      nDrawing += 1;
      rels.push(["rIdD1", `${XL_REL}/drawing`, `../drawings/drawing${nDrawing}.xml`]);
      const first = nChart + 1;
      files.push({ name: `xl/drawings/drawing${nDrawing}.xml`, data: xlDrawingXml(charts, first) });
      over.push([`/xl/drawings/drawing${nDrawing}.xml`, `${XL_CT}.drawing+xml`]);
      files.push({ name: `xl/drawings/_rels/drawing${nDrawing}.xml.rels`, data: xlRels(charts.map((_, k) => [`rIdC${k + 1}`, `${XL_REL}/chart`, `../charts/chart${first + k}.xml`])) });
      charts.forEach((ch) => {
        nChart += 1;
        files.push({ name: `xl/charts/chart${nChart}.xml`, data: xlChartXml(ch.chart) });
        over.push([`/xl/charts/chart${nChart}.xml`, `${XL_CT}.drawingml.chart+xml`]);
      });
    }
    files.push({ name: `xl/worksheets/sheet${n}.xml`, data: xlSheetXml(sh, i === 0, charts.length > 0) });
    over.push([`/xl/worksheets/sheet${n}.xml`, `${XL_CT}.spreadsheetml.worksheet+xml`]);
    if (rels.length) files.push({ name: `xl/worksheets/_rels/sheet${n}.xml.rels`, data: xlRels(rels) });
  });
  const sheets = book.sheets.map((sh, i) => `<sheet name="${xlEsc(sh.name)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join("");
  files.push({ name: "xl/workbook.xml", data: `${XML_HEAD}<workbook xmlns="${XL_NS.main}" xmlns:r="${XL_NS.r}"><bookViews><workbookView activeTab="0"/></bookViews><sheets>${sheets}</sheets></workbook>` });
  files.push({ name: "xl/_rels/workbook.xml.rels", data: xlRels([...book.sheets.map((_, i) => [`rId${i + 1}`, `${XL_REL}/worksheet`, `worksheets/sheet${i + 1}.xml`]), [`rId${book.sheets.length + 1}`, `${XL_REL}/styles`, "styles.xml"]]) });
  files.push({ name: "xl/styles.xml", data: xlStylesXml() });
  const stamp = new Date(when.getTime() - (when.getTime() % 1000)).toISOString().replace(".000Z", "Z");
  files.push({ name: "docProps/core.xml", data: `${XML_HEAD}<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>${xlEsc(book.title)}</dc:title><dc:creator>ALICIA</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">${stamp}</dcterms:created></cp:coreProperties>` });
  files.push({ name: "docProps/app.xml", data: `${XML_HEAD}<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>ALICIA</Application></Properties>` });
  files.push({ name: "_rels/.rels", data: xlRels([["rId1", `${XL_REL}/officeDocument`, "xl/workbook.xml"], ["rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"], ["rId3", `${XL_REL}/extended-properties`, "docProps/app.xml"]]) });
  over.push(["/xl/workbook.xml", `${XL_CT}.spreadsheetml.sheet.main+xml`], ["/xl/styles.xml", `${XL_CT}.spreadsheetml.styles+xml`],
    ["/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"], ["/docProps/app.xml", `${XL_CT}.extended-properties+xml`]);
  files.unshift({ name: "[Content_Types].xml", data: `${XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>${over.map(([p, t]) => `<Override PartName="${p}" ContentType="${t}"/>`).join("")}</Types>` });
  return xlZip(files, when);
}

/* ---- laying out a sheet: titles, then the chart, then the table it is drawn from ----------------------------------- */
const XL_CHART = { w: 760, h: 400 };
/* spec: {name, title, unit, lines [text], head [text], rows [[number | text | null]], fmts [number format per column, or
 * "text"], colorScale {kind "div" | "seq", scale, from (first column), neg, mid, pos}, chart}.
 * chart, in terms of the table's columns: {type "line" | "bar" | "scatter", title, cat (column), catKind "str" | "date",
 * series [{col, kind "line" | "bar", color, width, dash, alpha, outline, points [{idx, color}], labels}],
 * dir "col" | "bar", grouping, gap, overlap, reverse, xTitle, yTitle, xMin, xMax, yMin, yMax, dateUnit, legend,
 * hideLegend, groups (scatter: [{name, x, y, from, to, color, alpha, sizes, hollow}]), fit ({name, x, y, color})}. */
function xlTableSheet(spec) {
  const sh = { name: spec.name, cells: [], links: [], scales: [], charts: [] };
  const put = (r, c, v, s = 0) => sh.cells.push({ r, c, v, s });
  put(0, 0, spec.title, XL_STYLE.title);
  let r = 1;
  if (spec.unit) put(r++, 0, spec.unit, XL_STYLE.sub);
  for (const line of spec.lines || []) if (line) put(r++, 0, line, XL_STYLE.sub);
  r += 1;
  const chartRow = r;
  if (spec.chart) r += Math.ceil(XL_CHART.h / 20) + 1;
  const hr = r, n = spec.rows.length;
  const isText = (c) => !spec.fmts?.[c] || spec.fmts[c] === "text";
  const len = (v) => (xlNum(v) ? 8 : String(v ?? "").length);
  sh.widths = spec.widths || spec.head.map((h, c) => {
    if (spec.fmts?.[c] === "mmm yyyy") return 11;
    if (isText(c)) return Math.max(10, Math.min(46, Math.max(Math.ceil(String(h).length / 2), ...spec.rows.map((row) => len(row[c]))) + 2));
    const words = String(h).split(/\s+/).map((w) => w.length);
    return Math.max(10, Math.min(22, Math.max(Math.max(...words) + 2, Math.ceil(String(h).length / 2) + 2)));
  });
  spec.head.forEach((h, c) => put(hr, c, h, isText(c) ? XL_STYLE.head : XL_STYLE.headNum));
  spec.rows.forEach((row, i) => row.forEach((v, c) => {
    const f = spec.fmts?.[c];
    put(hr + 1 + i, c, xlNum(v) || (v !== null && v !== undefined) ? v : null, xlNum(v) && f && f !== "text" ? XL_STYLE[`n:${f}`] ?? 0 : 0);
  }));
  const cs = spec.colorScale;
  if (cs && n) {
    const sqref = `${xlRef(cs.from ?? 1, hr + 1)}:${xlRef(spec.head.length - 1, hr + n)}`;
    sh.scales.push({ sqref, stops: cs.kind === "div" ? [[-cs.scale, cs.neg], [0, cs.mid], [cs.scale, cs.pos]] : [[0, cs.mid], [cs.scale, cs.pos]] });
  }
  if (spec.chart) sh.charts.push({ ...xlAnchor(sh, 0, chartRow, XL_CHART.w, XL_CHART.h), chart: xlResolveChart(spec, hr) });
  return sh;
}
function xlResolveChart(spec, hr) {
  const ch = spec.chart, n = spec.rows.length, name = spec.name;
  const col = (c, from = 0, to = n - 1) => ({ ref: xlAbs(name, c, hr + 1 + from, c, hr + 1 + to), vals: spec.rows.slice(from, to + 1).map((row) => (xlNum(row[c]) ? row[c] : null)) });
  const cat = ch.cat === undefined ? null : ch.catKind === "date"
    ? { ...col(ch.cat), kind: "num", fmt: "mmm yyyy" }
    : { ref: col(ch.cat).ref, vals: spec.rows.map((row) => String(row[ch.cat] ?? "")), kind: "str" };
  const plots = [], byKind = new Map();
  for (const s of ch.series || []) {
    const type = (s.kind || ch.type) === "line" ? "line" : "bar";
    if (!byKind.has(type)) {
      const p = { type, dir: ch.dir, grouping: type === "bar" ? ch.grouping : undefined, gap: ch.gap, overlap: ch.overlap, series: [] };
      byKind.set(type, p); plots.push(p);
    }
    byKind.get(type).series.push({ ...s, name: String(spec.head[s.col] ?? ""), nameRef: xlAbs(name, s.col, hr), cat, val: col(s.col) });
  }
  if (ch.type === "scatter") {
    const p = { type: "scatter", series: [] };
    for (const g of ch.groups || []) {
      p.series.push({ name: g.name, xv: col(g.x, g.from, g.to), val: col(g.y, g.from, g.to), color: g.color, alpha: g.alpha, size: 7,
        points: (g.sizes || []).map((size, i) => ({ idx: i, size, hollow: g.hollow?.[i] })) });
    }
    if (ch.fit) p.series.push({ name: ch.fit.name, xv: col(ch.fit.x, 0, 1), val: col(ch.fit.y, 0, 1), color: ch.fit.color, width: 1, line: true });
    plots.push(p);
  }
  // Bars first, so lines are drawn on top.
  plots.sort((a, b) => (a.type === "bar" ? 0 : 1) - (b.type === "bar" ? 0 : 1));
  const count = plots.reduce((a, p) => a + p.series.length, 0);
  return {
    title: ch.title ?? spec.title, plots,
    x: { kind: ch.type === "scatter" ? "val" : ch.catKind === "date" ? "date" : "cat", reverse: ch.reverse, title: ch.xTitle, min: ch.xMin, max: ch.xMax, unit: ch.dateUnit },
    y: { title: ch.yTitle, min: ch.yMin, max: ch.yMax },
    legend: ch.legend ?? count > 1, hideLegend: ch.hideLegend,
  };
}
/* The About sheet. m: {title, unit, page, exported, built, settings [[name, value]], sources [{label, url, release,
 * licence}], notes [[heading, text]], terms [[word, meaning]], links [[label, url]], caveat}. */
function xlAboutSheet(m) {
  const sh = { name: "About", cells: [], links: [], scales: [], charts: [], widths: [30, 72, 14, 16] };
  const put = (r, c, v, s = 0) => sh.cells.push({ r, c, v, s });
  const web = (u) => /^https?:\/\//.test(u || "");
  let r = 0;
  const pair = (k, v, url) => {
    put(r, 0, k, XL_STYLE.label);
    put(r, 1, v, web(url) ? XL_STYLE.link : XL_STYLE.wrap);
    if (web(url)) sh.links.push({ r, c: 1, url });
    r++;
  };
  const section = (t) => { r++; put(r++, 0, t, XL_STYLE.section); };
  put(r++, 0, m.title, XL_STYLE.title);
  put(r++, 0, "Exported from the ALICIA website (Australian Legislation Impact on Competition Industry Analysis).", XL_STYLE.sub);
  r++;
  if (m.unit) pair("What the chart shows", m.unit);
  pair("Web page", m.page, m.page);
  pair("Exported", m.exported);
  if (m.built) pair("Data built", m.built);
  if ((m.settings || []).length) { section("Settings on the page when exported"); for (const [k, v] of m.settings) pair(k, v); }
  // The link goes last, so a long address runs on into the empty cells to its right.
  section("Data sources");
  ["Dataset", "Release used", "Licence", "Link"].forEach((h, c) => put(r, c, h, XL_STYLE.head));
  r++;
  for (const s of m.sources || []) {
    put(r, 0, s.label, XL_STYLE.wrap);
    put(r, 1, s.release || "", XL_STYLE.wrap);
    put(r, 2, s.licence || "–", XL_STYLE.wrap);
    put(r, 3, s.url, web(s.url) ? XL_STYLE.link : XL_STYLE.wrap);
    if (web(s.url)) sh.links.push({ r, c: 3, url: s.url });
    r++;
  }
  if ((m.notes || []).length) { section("Notes"); for (const [k, v] of m.notes) pair(k, v); }
  if ((m.terms || []).length) { section("Words used"); for (const [k, v] of m.terms) pair(k, v); }
  section("Method and limits");
  for (const [k, u] of m.links || []) pair(k, u, u);
  if (m.caveat) pair("Limits", m.caveat);
  return sh;
}
/* Sheet names: at most 31 characters, none of : \ / ? * [ ], unique within the workbook. */
function xlSheetNames(names) {
  const seen = new Set();
  return names.map((raw) => {
    const base = String(raw || "Sheet").replace(/[:\\/?*[\]']/g, "").replace(/\s+/g, " ").trim().slice(0, 31) || "Sheet";
    let name = base;
    for (let k = 2; seen.has(name.toLowerCase()); k++) name = `${base.slice(0, 28)} ${k}`;
    seen.add(name.toLowerCase());
    return name;
  });
}

/* ---- from the page's charts to sheets ----------------------------------------------------------------------------- */
/* Light-theme colours, so charts read on Excel's white background even when the page is dark. */
let XL_TOKENS = null;
function xlColor(c) {
  if (!c) return XL_INK2;
  if (/^#[0-9a-f]{6}$/i.test(c)) return c;
  const m = /^var\((--[\w-]+)\)$/.exec(String(c).trim());
  if (!m) return XL_INK2;
  if (!XL_TOKENS) {
    XL_TOKENS = {};
    for (const sheet of document.styleSheets) {
      let rules;
      try { rules = sheet.cssRules; } catch { continue; }
      for (const rule of rules) if (rule.selectorText === ":root") for (const p of rule.style) if (p.startsWith("--")) XL_TOKENS[p] ??= rule.style.getPropertyValue(p).trim();
    }
  }
  const v = XL_TOKENS[m[1]];
  return /^#[0-9a-f]{6}$/i.test(v || "") ? v : XL_INK2;
}
const xlDash = (d) => (!d ? null : d === true || d === "5 4" ? "dash" : d === "6 4" ? "lgDash" : /^1\.5 /.test(d) ? "sysDot" : "dash");
const xlMix = (a, b, p) => `#${[0, 2, 4].map((i) => Math.round(parseInt(xlHex(a).slice(i, i + 2), 16) * p + parseInt(xlHex(b).slice(i, i + 2), 16) * (1 - p)).toString(16).padStart(2, "0")).join("")}`;
/* The page's axis ends for a range (its first and last ticks); cover: widened by a step if the data run past them. */
function xlSpan(lo, hi, cover = false) {
  const t = niceTicks(lo, hi, 5), step = t.length > 1 ? t[1] - t[0] : 1;
  let a = t[0], b = t[t.length - 1];
  while (cover && b < hi) b = +(b + step).toPrecision(12);
  return [a, b];
}
const xlXHead = { fy: "Financial year", year: "Year", month: "Month", quarter: "Quarter beginning" };

function xlLine(o) {
  const series = o.series.filter((s) => s.values.some(xlNum));
  const date = o.xKind === "month" || o.xKind === "quarter";
  const head = [xlXHead[o.xKind] || "Period", ...series.map((s) => s.label)];
  const rows = o.x.map((x, i) => [date ? xlSerial(x) : o.xKind === "fy" ? fyLabel(x) : String(x), ...series.map((s) => (xlNum(s.values[i]) ? s.values[i] : null))]);
  const fmts = [date ? "mmm yyyy" : "text", ...series.map(() => o.xlFmt || "0.0")];
  const chart = { type: "line", cat: 0, catKind: date ? "date" : "str", series: series.map((s, i) => ({ col: i + 1, color: xlColor(s.color), width: (s.width || 1.8) * 0.75, dash: xlDash(s.dash) })) };
  const notes = [];
  // The page's axis range, so Excel's matches it (and the shading below can fill it).
  const vals = series.flatMap((s) => s.values.filter(xlNum));
  if (vals.length) {
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (xlNum(o.ref)) { lo = Math.min(lo, o.ref); hi = Math.max(hi, o.ref); }
    if (o.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    [chart.yMin, chart.yMax] = xlSpan(lo, hi, true);
  }
  if (date && o.x.length) {
    const years = (o.x[o.x.length - 1] - o.x[0]) / (365.25 * 86400000);
    chart.dateUnit = years <= 8 ? 1 : years <= 16 ? 2 : years <= 40 ? 5 : 10;
  }
  // The shaded years are columns reaching the top of the axis (and its bottom, below zero), drawn behind the lines.
  if (o.band && xlNum(o.band.from) && xlNum(o.band.to) && vals.length) {
    const inBand = (i) => o.x[i] >= o.band.from && o.x[i] <= o.band.to;
    const ends = chart.yMin < 0 ? [chart.yMax, chart.yMin] : [chart.yMax];
    const shade = ends.map((end, k) => {
      head.push(`${o.band.xlLabel || "Shaded: the selected period"}${k ? ", below zero" : ""}`);
      fmts.push("0.0");
      rows.forEach((row, i) => row.push(inBand(i) ? end : null));
      return { col: head.length - 1, kind: "bar", color: xlColor("var(--accent)"), alpha: 0.12 };
    });
    chart.series = [...shade, ...chart.series];
    chart.gap = 0;
    chart.overlap = 100;
    if (ends.length > 1) chart.hideLegend = [1];
    notes.push(["In this workbook", `The shaded columns mark the years the page highlights. The "Shaded" column${ends.length > 1 ? "s" : ""} of the table only draw${ends.length > 1 ? "" : "s"} them: ${ends.length > 1 ? "they hold the top and bottom" : "it holds the top"} of the axis in those years.`]);
  }
  return { head, rows, fmts, chart, notes };
}
function xlColumn(o) {
  const head = [xlXHead[o.xKind] || "Year", o.tipLabel || "Value"];
  const rows = o.x.map((x, i) => [o.xKind === "year" ? String(x) : fyLabel(x), xlNum(o.values[i]) ? o.values[i] : null]);
  const neg = xlColor("var(--neg)");
  return {
    head, rows, fmts: ["text", o.xlFmt || "0.0"],
    chart: { type: "bar", dir: "col", grouping: "clustered", gap: 40, cat: 0, legend: false,
      series: [{ col: 1, color: xlColor(o.color || "var(--pos)"), points: rows.map((row, i) => (row[1] < 0 ? { idx: i, color: neg } : null)).filter(Boolean) }] },
  };
}
function xlBars(o) {
  const refs = (o.refs || []).filter((r) => xlNum(r.value));
  const head = [o.xlCat || "Group", o.xlValue || "Value", ...refs.map((r) => r.label || "Reference")];
  const rows = o.bars.map((b) => [b.label, xlNum(b.value) ? b.value : null, ...refs.map((r) => r.value)]);
  return {
    head, rows, fmts: ["text", "0.0", ...refs.map(() => "0.0")],
    chart: { type: "bar", dir: "col", grouping: "clustered", gap: 80, cat: 0, legend: refs.length > 0, hideLegend: [0],
      series: [{ col: 1, color: xlColor(o.bars[0]?.color), points: o.bars.map((b, i) => ({ idx: i, color: xlColor(b.color) })), labels: { fmt: "0.0", pos: "outEnd" } },
        ...refs.map((r, j) => ({ col: 2 + j, kind: "line", color: XL_INK2, width: 1.25, dash: xlDash(r.dash) || "dash" }))] },
    notes: refs.length ? [["In this workbook", "Excel draws the reference lines from the first bar to the last, not across the whole chart."]] : [],
  };
}
function xlScatter(o) {
  const [X0, X1] = xlSpan(...o.xDomain), [Y0, Y1] = xlSpan(...o.yDomain);
  const pts = o.points.filter((p) => xlNum(p.x) && xlNum(p.y));
  const order = [...new Set(pts.map((p) => p.group ?? p.color))];
  pts.sort((a, b) => order.indexOf(a.group ?? a.color) - order.indexOf(b.group ?? b.color) || String(a.label).localeCompare(String(b.label)));
  const out = (p) => p.x < X0 || p.x > X1 || p.y < Y0 || p.y > Y1;
  const fit = o.fit && xlNum(o.fit.slope) ? [[X0, o.fit.intercept + o.fit.slope * X0], [X1, o.fit.intercept + o.fit.slope * X1]] : null;
  const head = ["Sector", "Group", o.xTitle || "x", o.yTitle || "y", o.weightTitle || "Size", ...(fit ? ["", `${o.fitLabel || "Line of best fit"}: x`, `${o.fitLabel || "Line of best fit"}: y`] : [])];
  const rows = pts.map((p, i) => [p.label, p.groupLabel ?? "", p.x, p.y, xlNum(p.weight) ? p.weight : null, ...(fit ? [null, fit[i]?.[0] ?? null, fit[i]?.[1] ?? null] : [])]);
  if (fit && rows.length < 2) for (let i = rows.length; i < 2; i++) rows.push(["", "", null, null, null, null, fit[i][0], fit[i][1]]);
  const groups = order.map((g) => {
    const idx = pts.map((p, i) => ((p.group ?? p.color) === g ? i : -1)).filter((i) => i >= 0);
    const p0 = pts[idx[0]];
    return { name: p0.groupLabel ?? "Sectors", x: 2, y: 3, from: idx[0], to: idx[idx.length - 1], color: xlColor(p0.color), alpha: p0.muted ? 0.55 : 0.85,
      sizes: idx.map((i) => 2 * Math.max(3.5, pts[i].size || 4) * 0.75), hollow: idx.map((i) => out(pts[i])) };
  });
  const off = pts.filter(out).map((p) => p.label);
  return {
    head, rows, fmts: ["text", "text", "0.0", "0.0", "0.0", ...(fit ? ["text", "0.0", "0.0"] : [])],
    chart: { type: "scatter", groups, fit: fit ? { name: o.fitLabel || "Line of best fit", x: 6, y: 7, color: XL_INK2 } : null, xTitle: o.xTitle, yTitle: o.yTitle, xMin: X0, xMax: X1, yMin: Y0, yMax: Y1 },
    notes: [["In this workbook", `Dot sizes follow ${o.weightTitle ? o.weightTitle.replace(/,.*/, "").toLowerCase() : "size"}, as on the page.${off.length ? ` Outside the chart's scale, and so not drawn by Excel: ${off.join(", ")}.` : ""}`]],
  };
}
function xlMekko(o) {
  const t = o.threshold;
  const bars = o.bars.filter((b) => xlNum(b.value) && xlNum(b.width) && b.width > 0);
  const [Y0, Y1] = xlSpan(...o.yDomain);
  const head = ["Sector", "Return on equity, %", o.xTitle || "Width", "Normal profit (up to the cost of equity)", "Shortfall (below the cost of equity)", "Super-normal profit (above the cost of equity)", "Loss", "Cost of equity, %"];
  const rows = bars.map((b) => {
    const v = b.value, pos = Math.max(0, v);
    return [b.label, v, b.width, Math.min(pos, t), v < t ? t - pos : 0, Math.max(0, v - t), Math.min(0, v), t];
  });
  return {
    head, rows, fmts: ["text", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
    chart: { type: "bar", dir: "col", grouping: "stacked", gap: 30, cat: 0, yMin: Y0, yMax: Y1, yTitle: "Return on equity, %",
      series: [{ col: 3, color: xlColor("var(--p-normal)") }, { col: 4, color: xlColor("var(--p-short)") }, { col: 5, color: xlColor("var(--p-super)") }, { col: 6, color: xlColor("var(--p-loss)") },
        { col: 7, kind: "line", color: XL_INK2, width: 1.25, dash: "dash" }] },
    notes: [["In this workbook", `Excel has no chart with bars of different widths, so every sector's bar is the same width here. On the page each bar is as wide as the sector's equity (column C). Bars beyond ${fmt(Y0, 0)}% to ${fmt(Y1, 0)}% are cut off at the edge, as on the page.`]],
  };
}
function xlShares(rows, keys) {
  const pct = rows.map((r) => {
    const sum = keys.reduce((a, k) => a + Math.max(0, r.parts[k.key] || 0), 0);
    return keys.map((k) => (sum > 0 ? (Math.max(0, r.parts[k.key] || 0) / sum) * 100 : null));
  });
  return {
    head: ["Share of the total, %", ...keys.map((k) => k.label)],
    rows: rows.map((r, i) => [r.label, ...pct[i]]), fmts: ["text", ...keys.map(() => "0.0")],
    chart: { type: "bar", dir: "bar", grouping: "stacked", gap: 40, cat: 0, reverse: true, yMin: 0, yMax: 100, legend: true,
      series: keys.map((k, j) => ({ col: j + 1, color: xlColor(`var(--fill-${k.key})`), labels: { fmt: "0", pos: "ctr", color: xlColor(`var(--ink-${k.key})`), hide: pct.map((p, i) => (!(p[j] >= 9) ? i : -1)).filter((i) => i >= 0) } })) },
    notes: [["In this workbook", "Each bar adds to 100%. A group whose total is negative counts as zero, as on the page."]],
  };
}
function xlRanked(rows, o) {
  const pos = xlColor("var(--pos)"), neg = xlColor("var(--neg)");
  return {
    head: [o.xlCat || "Item", o.xlValue || "Value"], rows: rows.map((r) => [r.label, xlNum(r.value) ? r.value : null]), fmts: ["text", "0.0"],
    chart: { type: "bar", dir: "bar", grouping: "clustered", gap: 40, cat: 0, reverse: true, legend: false,
      series: [{ col: 1, color: pos, points: rows.map((r, i) => ({ idx: i, color: r.color ? xlColor(r.color) : xlNum(r.value) && r.value < 0 ? neg : pos })), labels: { fmt: "0.0", pos: "outEnd" } }] },
  };
}
function xlDumbbell(rows, o) {
  return {
    head: [o.xlCat || "Item", String(o.aLabel), String(o.bLabel), "Change, percentage points"],
    rows: rows.map((r) => [r.label, xlNum(r.a) ? r.a : null, xlNum(r.b) ? r.b : null, xlNum(r.a) && xlNum(r.b) ? r.b - r.a : null]), fmts: ["text", "0.0", "0.0", "+0.0;-0.0;0.0"],
    chart: { type: "bar", dir: "bar", grouping: "clustered", gap: 50, cat: 0, reverse: true, yMin: o.domain[0], legend: true,
      series: [{ col: 1, color: "#D3D2CA" }, { col: 2, color: xlColor("var(--accent)") }] },
    notes: [["In this workbook", "On the page each row is a pair of dots joined by a line; Excel shows the two years as a pair of bars."]],
  };
}
function xlFromChart(x) {
  switch (x.kind) {
    case "line": return xlLine(x.opts);
    case "column": return xlColumn(x.opts);
    case "bar": return xlBars(x.opts);
    case "scatter": return xlScatter(x.opts);
    case "mekko": return xlMekko(x.opts);
    case "shares": return xlShares(x.rows, x.keys, x.opts);
    case "ranked": return xlRanked(x.rows, x.opts);
    case "dumbbell": return xlDumbbell(x.rows, x.opts);
    default: return null;
  }
}

/* ---- the button ------------------------------------------------------------------------------------------------------ */
/* Page-wide settings: {sources: {key: {label, url, licence}}, release: {key: text}, built, links [[label, url]]}. */
let XL_PAGE = { sources: {}, release: {}, links: [] };
function excelSetup(cfg) { XL_PAGE = { ...XL_PAGE, ...cfg }; }
const xlText = (n) => (n ? n.textContent.replace(/\s+/g, " ").trim() : "");
const xlFile = (s) => s.replace(/\s*:\s*/g, " - ").replace(/[\\/]+/g, "-").replace(/[*?"<>|]+/g, "").replace(/\s+/g, " ").trim().slice(0, 140);

/* The workbook for a card: a sheet for each chart in it (in page order, each titled by the heading above it), any
 * extra tables, and the About sheet. cfg: {title (), settings () -> [[name, value]], tables () -> [sheet spec],
 * sheets [names], sources [extra keys], notes () -> [[heading, text]], terms [extra keys], file () -> text}. */
function xlCardBook(card, cfg = {}) {
  const heads = [...card.querySelectorAll("h3")];
  const title = (cfg.title && cfg.title()) || xlText(heads[0]) || "Chart";
  const settings = (cfg.settings ? cfg.settings() : []).filter(([, v]) => v !== undefined && v !== null && v !== "");
  const settingsLine = settings.length ? `Settings: ${settings.map(([k, v]) => `${k}: ${v}`).join("; ")}.` : "";
  const srcKeys = [...new Set([...[...card.querySelectorAll(".source a[data-src]")].map((a) => a.dataset.src), ...(cfg.sources || [])])].filter((k) => XL_PAGE.sources[k]);
  const srcLine = srcKeys.length ? `Source${srcKeys.length > 1 ? "s" : ""}: ${srcKeys.map((k) => XL_PAGE.sources[k].label).join("; ")}. Links, releases and licences are on the About sheet.` : "";
  const parts = [];
  let h = title, unit = "", first = true;
  for (const node of card.querySelectorAll("h3, .unit, .chart, .bars, .dumbbell, .shares")) {
    if (node.matches("h3")) { h = first && cfg.title ? title : xlText(node); first = false; unit = ""; }
    else if (node.matches(".unit")) unit = xlText(node);
    else if (node._xl) {
      const made = xlFromChart(node._xl);
      if (made && made.rows.length) parts.push({ ...made, title: node._xl.opts?.xlTitle || h, unit: node._xl.opts?.xlUnit || unit });
    }
  }
  const extra = cfg.tables ? cfg.tables() : [];
  const names = xlSheetNames([...parts.map((p, i) => cfg.sheets?.[i] || (parts.length > 1 ? `Chart ${i + 1}` : "Chart")), ...extra.map((t) => t.name), "About"]);
  const sheets = [
    ...parts.map((p, i) => xlTableSheet({ ...p, name: names[i], lines: [settingsLine, srcLine], chart: { ...p.chart, title: p.title } })),
    ...extra.map((t, i) => xlTableSheet({ ...t, name: names[parts.length + i], title: t.title || title, lines: [settingsLine, srcLine] })),
  ];
  const notes = [];
  card.querySelectorAll(".hint, .note, details.more p").forEach((n) => { const t = xlText(n); if (t) notes.push([n.closest("details") ? xlText(n.closest("details").querySelector("summary")) : "Note", t]); });
  if (cfg.notes) notes.push(...cfg.notes());
  for (const p of parts) for (const nt of p.notes || []) if (!notes.some(([, t]) => t === nt[1])) notes.push(nt);
  const keys = [...new Set([...[...card.querySelectorAll(".term[data-term]")].map((b) => b.dataset.term), ...(cfg.terms || [])])].filter((k) => TERMS[k]);
  const about = xlAboutSheet({
    title, unit: parts.length === 1 ? parts[0].unit : parts.map((p) => p.unit).filter(Boolean).join(" ") || (extra[0]?.unit ?? ""),
    page: location.href.split("#")[0], exported: new Date().toLocaleString("en-AU", { dateStyle: "long", timeStyle: "short" }), built: XL_PAGE.built,
    settings,
    sources: srcKeys.map((k) => ({ ...XL_PAGE.sources[k], release: XL_PAGE.release[k] || "" })),
    notes, terms: keys.map((k) => TERMS[k]).sort((a, b) => a[0].localeCompare(b[0])),
    links: XL_PAGE.links, caveat: "These are descriptive statistics: they show what happened, not why.",
  });
  return { title, file: `ALICIA - ${xlFile(title)}${cfg.file ? ` - ${xlFile(cfg.file())}` : ""}.xlsx`, sheets: [...sheets, { ...about, name: names[names.length - 1] }] };
}
function xlDownload(bytes, name) {
  const url = URL.createObjectURL(new Blob([bytes], { type: `${XL_CT}.spreadsheetml.sheet` }));
  const a = document.createElement("a");
  a.href = url; a.download = name; a.hidden = true;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
const XL_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v8M4.5 6.8 8 10.3l3.5-3.5M3 13.5h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
/* Adds a "Download Excel" button to a card: at the end of cfg.anchor, or beside the card's heading (or its first line). */
function excelButton(card, cfg = {}) {
  const b = document.createElement("button");
  b.type = "button"; b.className = "xl-btn";
  b.innerHTML = `${XL_ICON}Excel`;
  b.title = "Download this chart as an Excel workbook: the chart, its numbers, and where the data come from";
  b.setAttribute("aria-label", "Download as an Excel workbook");
  b.addEventListener("click", () => {
    try {
      const book = xlCardBook(card, cfg);
      xlDownload(xlsxWorkbook(book), book.file);
    } catch (err) {
      console.error(err);
      b.textContent = "Export failed";
      setTimeout(() => { b.innerHTML = `${XL_ICON}Excel`; }, 4000);
    }
  });
  if (cfg.anchor) cfg.anchor.appendChild(b);
  else {
    const first = card.querySelector("h3") || card.firstElementChild;
    const head = document.createElement("div");
    head.className = "card-head";
    first.replaceWith(head);
    head.append(first, b);
  }
  return b;
}
