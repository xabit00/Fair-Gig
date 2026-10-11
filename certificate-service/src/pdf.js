const PDFDocument = require("pdfkit");

function money(value) {
  return `PKR ${Number(value || 0).toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function renderPdf(data) {
  return new Promise((resolve, reject) => {
    const document = new PDFDocument({ size: "A4", margin: 54, info: { Title: "FairGig Income Certificate" } });
    const chunks = [];
    document.on("data", (chunk) => chunks.push(chunk));
    document.on("end", () => resolve(Buffer.concat(chunks)));
    document.on("error", reject);

    document.fillColor("#187453").fontSize(20).text("FairGig");
    document.fillColor("#17342b").fontSize(28).text("Income Certificate", { align: "left" });
    document.moveDown(0.5).strokeColor("#187453").lineWidth(2).moveTo(54, document.y).lineTo(541, document.y).stroke();
    document.moveDown(1.5).fontSize(11).fillColor("#40564e").text(
      "This certificate summarizes income records logged in FairGig for the stated reporting period."
    );

    const rows = [
      ["Worker", data.name],
      ["Worker ID", data.worker_id],
      ["Reporting period", data.period],
      ["Gross income", money(data.gross)],
      ["Deductions", money(data.deductions)],
      ["Net income", money(data.net)],
      ["Hours worked", `${Number(data.hours || 0).toFixed(1)} hrs`],
      ["Verification status", data.verified_status],
    ];
    document.moveDown(1.5);
    for (const [label, value] of rows) {
      document.fillColor("#667b73").fontSize(9).text(label.toUpperCase());
      document.fillColor("#17342b").fontSize(13).text(String(value || "Not supplied"));
      document.moveDown(0.8);
    }

    document.moveDown(1.5).fontSize(9).fillColor("#667b73").text(
      "Verification applies only to shifts marked confirmed in FairGig. Worker-reported records have not been independently verified."
    );
    document.text(`Generated ${new Date(data.generated_at).toLocaleString("en-PK")}.`);
    document.end();
  });
}

module.exports = renderPdf;
