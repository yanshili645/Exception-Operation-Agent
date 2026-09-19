import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectDir = process.env.POWERWASH_PROJECT_DIR || process.cwd();
const dataDir = `${projectDir}/outputs/demo`;
const outputPath = `${projectDir}/outputs/PowerWash_Daily_Exception_Report_v0.1.xlsx`;
const summary = JSON.parse(await fs.readFile(`${dataDir}/management_summary.json`, "utf8"));
const exceptions = JSON.parse(await fs.readFile(`${dataDir}/exceptions.json`, "utf8"));
const rules = JSON.parse(await fs.readFile(`${projectDir}/config/rules.json`, "utf8"));
const wb = Workbook.create();
const overview = wb.worksheets.add("Daily Summary");
const detail = wb.worksheets.add("Exceptions");
const settings = wb.worksheets.add("Rule Settings");
const font = "Arial";
const navy = "#17365D";
const blue = "#2F75B5";
const lightBlue = "#D9EAF7";
const amber = "#FFF2CC";
const red = "#FCE4D6";
const green = "#E2F0D9";
const grey = "#667085";

for (const sheet of [overview, detail, settings]) {
  sheet.showGridLines = false;
  sheet.getRange("A1:Q80").format.font = { name: font, size: 10, color: "#1F2937" };
}
overview.tabColor = navy;
settings.tabColor = "#9DC3E6";

overview.getRange("A2:I2").merge();
overview.getRange("A2").values = [["PowerWash Daily Operations Exception Report"]];
overview.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
overview.getRange("A3:I3").merge();
overview.getRange("A3").values = [[`Reporting date ${summary.report_date} · Read-only MVP`]];
overview.getRange("A3").format.font = { name: font, size: 10, italic: true, color: grey };
overview.getRange("A4:I4").format.borders = { bottom: { style: "thin", color: blue } };

overview.getRange("A6:B6").values = [["Operational status", "Value"]];
overview.getRange("D6:E6").values = [["Workforce", "Value"]];
overview.getRange("G6:H6").values = [["Exception severity", "Count"]];
for (const range of ["A6:B6", "D6:E6", "G6:H6"]) {
  overview.getRange(range).format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
}
overview.getRange("A7:A11").values = [["Overall status"], ["Jobs scheduled"], ["Jobs completed"], ["Jobs incomplete"], ["Completion rate"]];
overview.getRange("B7").formulas = [["=IF(H7>0,\"Red\",IF(H8>0,\"Amber\",\"Green\"))"]];
overview.getRange("B8:B10").values = [[summary.jobs_scheduled], [summary.jobs_completed], [summary.jobs_incomplete]];
overview.getRange("B11").formulas = [["=IF(B8=0,0,B9/B8)"]];
overview.getRange("B11").format.numberFormat = "0%";

overview.getRange("D7:D11").values = [["Staff rostered"], ["Timesheets received"], ["Scheduled hours"], ["Actual hours"], ["Hours variance"]];
overview.getRange("E7:E11").values = [[summary.staff_rostered], [summary.timesheets_received], [summary.scheduled_hours], [summary.actual_hours], [summary.labour_variance_hours]];
overview.getRange("E9:E11").format.numberFormat = "0.00";

overview.getRange("G7:G11").values = [["Critical"], ["High"], ["Medium"], ["Low"], ["Total"]];
overview.getRange("H7").formulas = [["=COUNTIF(Exceptions!$B$2:$B$200,\"Critical\")"]];
overview.getRange("H8").formulas = [["=COUNTIF(Exceptions!$B$2:$B$200,\"High\")"]];
overview.getRange("H9").formulas = [["=COUNTIF(Exceptions!$B$2:$B$200,\"Medium\")"]];
overview.getRange("H10").formulas = [["=COUNTIF(Exceptions!$B$2:$B$200,\"Low\")"]];
overview.getRange("H11").formulas = [["=SUM(H7:H10)"]];
overview.getRange("A7:H11").format.borders = { preset: "outside", style: "thin", color: "#D0D5DD" };

overview.getRange("A14:I14").merge();
overview.getRange("A14").values = [["Suggested interpretation"]];
overview.getRange("A14").format = { fill: lightBlue, font: { name: font, size: 11, bold: true, color: navy } };
overview.getRange("A15:I16").merge();
overview.getRange("A15").values = [[summary.ai_narrative.suggested_interpretation]];
overview.getRange("A15").format = { wrapText: true, verticalAlignment: "top" };

overview.getRange("A18:D18").merge();
overview.getRange("A18").values = [["Management attention"]];
overview.getRange("F18:I18").merge();
overview.getRange("F18").values = [["Recommended actions"]];
for (const cell of ["A18", "F18"]) overview.getRange(cell).format = { fill: amber, font: { name: font, size: 11, bold: true, color: navy } };
const attention = summary.ai_narrative.management_attention.slice(0, 3);
const actions = summary.ai_narrative.recommended_actions.slice(0, 3);
for (let i = 0; i < 3; i++) {
  overview.getRange(`A${19+i}:D${19+i}`).merge();
  overview.getRange(`A${19+i}`).values = [[attention[i] ? `${i+1}. ${attention[i]}` : ""]];
  overview.getRange(`F${19+i}:I${19+i}`).merge();
  overview.getRange(`F${19+i}`).values = [[actions[i] ? `${i+1}. ${actions[i]}` : ""]];
}
overview.getRange("A19:I21").format.wrapText = true;
overview.getRange("A24:I24").merge();
overview.getRange("A24").values = [["All exception codes and severities are rule-generated. AI content is advisory and cannot change source evidence."]];
overview.getRange("A24").format.font = { name: font, size: 9, italic: true, color: grey };
overview.getRange("A1:I26").format.verticalAlignment = "center";
overview.getRange("A:A").format.columnWidth = 20;
overview.getRange("B:B").format.columnWidth = 13;
overview.getRange("C:C").format.columnWidth = 3;
overview.getRange("D:D").format.columnWidth = 20;
overview.getRange("E:E").format.columnWidth = 13;
overview.getRange("F:F").format.columnWidth = 20;
overview.getRange("G:G").format.columnWidth = 20;
overview.getRange("H:H").format.columnWidth = 12;
overview.getRange("I:I").format.columnWidth = 20;
overview.getRange("15:16").format.rowHeight = 28;
overview.getRange("19:21").format.rowHeight = 36;

const headers = ["Report date", "Severity", "Code", "Category", "Job", "Customer", "Truck", "Employee", "Planned", "Actual", "Variance", "Evidence", "Owner", "Recommended action", "Source", "Status", "Resolution"];
detail.getRange("A1:Q1").values = [headers];
const rows = exceptions.map(x => [x.report_date, x.severity, x.code, x.category, x.job_number, x.customer, x.truck, x.employee, x.planned, x.actual, x.variance, x.evidence, x.owner, x.recommended_action, x.source, x.status, x.resolution]);
if (rows.length) detail.getRange(`A2:Q${rows.length+1}`).values = rows;
detail.getRange("A1:Q1").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", wrapText: true };
detail.getRange(`A2:Q${rows.length+1}`).format.verticalAlignment = "top";
detail.getRange(`A2:Q${rows.length+1}`).format.wrapText = true;
detail.getRange(`A1:Q${rows.length+1}`).format.borders = { preset: "inside", style: "thin", color: "#E4E7EC" };
const table = detail.tables.add(`A1:Q${rows.length+1}`, true, "ExceptionRegister");
table.style = "TableStyleMedium2";
detail.freezePanes.freezeRows(1);
detail.freezePanes.freezeColumns(3);
detail.getRange(`B2:B${rows.length+1}`).conditionalFormats.add("containsText", { text: "Critical", format: { fill: red, font: { bold: true, color: "#9C0006" } } });
detail.getRange(`B2:B${rows.length+1}`).conditionalFormats.add("containsText", { text: "High", format: { fill: amber, font: { bold: true, color: "#9C5700" } } });
detail.getRange(`B2:B${rows.length+1}`).conditionalFormats.add("containsText", { text: "Medium", format: { fill: "#FFFBE6", font: { color: "#7F6000" } } });
detail.getRange(`P2:P200`).dataValidation = { rule: { type: "list", values: ["Open", "Investigating", "Resolved", "Accepted exception"] } };
const widths = [13,11,10,19,10,25,12,20,20,20,16,34,20,42,14,18,34];
widths.forEach((w, i) => detail.getRangeByIndexes(0, i, rows.length+1, 1).format.columnWidth = w);
detail.getRange("A:A").format.numberFormat = "yyyy-mm-dd";

settings.getRange("A2:D2").merge();
settings.getRange("A2").values = [["Proposed exception thresholds"]];
settings.getRange("A2").format.font = { name: font, size: 14, bold: true, color: navy };
settings.getRange("A4:D4").values = [["Setting", "Value", "Unit", "Approval status"]];
const ruleRows = [
  ["Late job becomes high", rules.late_job_high_minutes, "minutes", "Manager approval required"],
  ["Late job becomes critical", rules.late_job_critical_minutes, "minutes", "Manager approval required"],
  ["Late clock-on", rules.late_clock_medium_minutes, "minutes", "Manager approval required"],
  ["High late clock-on", rules.late_clock_high_minutes, "minutes", "Manager approval required"],
  ["No-show threshold", rules.no_show_minutes, "minutes", "Manager approval required"],
  ["Overtime threshold", rules.overtime_minutes, "minutes", "Manager approval required"],
  ["Duration overrun", rules.duration_overrun_percent / 100, "percent", "Manager approval required"],
  ["Minimum meal break", rules.minimum_meal_break_minutes, "minutes", "Manager approval required"],
  ["Maximum paid day", rules.maximum_paid_day_hours, "hours", "Manager approval required"],
];
settings.getRange(`A5:D${4+ruleRows.length}`).values = ruleRows;
settings.getRange("A4:D4").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
settings.getRange(`B5:B${4+ruleRows.length}`).format.fill = "#FFF2CC";
settings.getRange("B11").format.numberFormat = "0%";
settings.getRange("A16:D16").values = [["Priority first sites", rules.priority_first_sites.join(", "), "", "Existing routing rule"]];
settings.getRange("A17:D17").values = [["After-noon sites", rules.after_noon_sites.join(", "), "", "Existing routing rule"]];
settings.getRange("A18:D18").values = [["Depot exclusion", rules.depot_address, "", "Existing routing rule"]];
settings.getRange("A4:D18").format.borders = { preset: "inside", style: "thin", color: "#E4E7EC" };
settings.getRange("A:D").format.verticalAlignment = "top";
settings.getRange("A:D").format.wrapText = true;
settings.getRange("A:A").format.columnWidth = 28;
settings.getRange("B:B").format.columnWidth = 48;
settings.getRange("C:C").format.columnWidth = 14;
settings.getRange("D:D").format.columnWidth = 28;
settings.freezePanes.freezeRows(4);

wb.recalculate();
const summaryInspect = await wb.inspect({ kind: "table", range: "Daily Summary!A1:I24", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 10 });
console.log(summaryInspect.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);
for (const [sheetName, range, file] of [
  ["Daily Summary", "A1:I24", "summary_preview.png"],
  ["Exceptions", `A1:Q${rows.length+1}`, "exceptions_preview.png"],
  ["Rule Settings", "A1:D18", "settings_preview.png"],
]) {
  const preview = await wb.render({ sheetName, range, scale: 1.2, format: "png" });
  await fs.writeFile(`${dataDir}/${file}`, new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(outputPath);
console.log(outputPath);
