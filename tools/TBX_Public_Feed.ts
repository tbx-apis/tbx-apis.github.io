interface SyncPart { title: string; body: string; }

function main(workbook: ExcelScript.Workbook, csv: string): SyncPart[] {
  // Public (customer) feed: keeps ONLY customer-safe columns. No prices, codes, docs or vendor data.
  const KEEP: string[] = ["TBX API Name", "API Status", "Category", "Sub-Category", "Detailed Description",
    "Use-Case", "Target Customers", "Target Industry"];
  const rows: string[][] = [];
  let row: string[] = [], f = "", inQ = false;
  for (let i = 0; i < csv.length; i++) {
    const ch = csv.charAt(i);
    if (inQ) { if (ch === "\"") { if (csv.charAt(i + 1) === "\"") { f += "\""; i++; } else { inQ = false; } } else { f += ch; } }
    else if (ch === "\"") { inQ = true; }
    else if (ch === ",") { row.push(f); f = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && csv.charAt(i + 1) === "\n") { i++; }
      row.push(f); f = ""; if (row.join("") !== "") { rows.push(row); } row = [];
    } else { f += ch; }
  }
  if (f !== "" || row.length > 0) { row.push(f); if (row.join("") !== "") { rows.push(row); } }
  if (rows.length < 21) { throw new Error("Feed has only " + (rows.length - 1) + " APIs - public site not updated."); }
  const head: string[] = rows[0].map(x => x.trim());
  const idx: number[] = KEEP.map(k => head.indexOf(k));
  if (idx.some(i => i < 0)) { throw new Error("Feed is missing a public column."); }
  const q = (s: string): string => (s.indexOf(",") >= 0 || s.indexOf("\"") >= 0) ? "\"" + s.split("\"").join("\"\"") + "\"" : s;
  const header = KEEP.map(k => q(k)).join(",");
  const lines: string[] = [];
  for (let r = 1; r < rows.length; r++) {
    lines.push(idx.map(i => q(((rows[r][i] || "").replace(/[\r\n]+/g, " ")).trim())).join(","));
  }
  // GitHub issues hold up to 65,536 characters: split into parts of max 60,000.
  const chunks: string[] = [];
  let cur = header;
  for (const l of lines) {
    if (cur.length + l.length + 1 > 60000) { chunks.push(cur); cur = header; }
    cur += "\n" + l;
  }
  chunks.push(cur);
  const now = new Date();
  const batch = now.getUTCFullYear() + ("0" + (now.getUTCMonth() + 1)).slice(-2) + ("0" + now.getUTCDate()).slice(-2) + "T" +
    ("0" + now.getUTCHours()).slice(-2) + ("0" + now.getUTCMinutes()).slice(-2) + ("0" + now.getUTCSeconds()).slice(-2);
  return chunks.map((c, i) => ({ title: "tbx-sync " + batch + " " + (i + 1) + "/" + chunks.length, body: c }));
}
