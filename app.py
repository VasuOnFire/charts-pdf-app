import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from flask import Flask, request, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/generate", methods=["POST"])
def generate_pdf():
    email = request.form.get("email")
    chart_type = request.form.get("chart_type")
    file = request.files.get("file")

    if not email or not chart_type or not file:
        return jsonify({"error": "email, chart_type, file required"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    # Load data
    if filename.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    df = df.dropna()

    x = df.iloc[:, 0]
    y = df.iloc[:, 1]

    plt.figure(figsize=(6, 4))

    # ===== CHART TYPES =====
    if chart_type == "bar":
        plt.bar(x, y)

    elif chart_type == "line":
        plt.plot(x, y, marker="o")

    elif chart_type == "area":
        plt.fill_between(x, y, alpha=0.6)

    elif chart_type == "pie":
        plt.pie(y, labels=x, autopct="%1.1f%%")

    elif chart_type == "donut":
        plt.pie(y, labels=x)
        centre = plt.Circle((0, 0), 0.70, fc="white")
        plt.gca().add_artist(centre)

    elif chart_type == "histogram":
        plt.hist(y, bins=10)

    elif chart_type == "scatter":
        plt.scatter(x, y)

    elif chart_type == "heatmap":
        sns.heatmap(df.select_dtypes("number"), annot=True, cmap="coolwarm")

    elif chart_type == "treemap":
        import squarify
        sizes = df.iloc[:, 1]
        labels = df.iloc[:, 0]
        squarify.plot(sizes=sizes, label=labels, alpha=0.8)
        plt.axis("off")

    elif chart_type == "dashboard":
        fig, axs = plt.subplots(2, 2, figsize=(8, 6))
        axs[0, 0].bar(x, y)
        axs[0, 1].plot(x, y)
        axs[1, 0].pie(y, labels=x)
        axs[1, 1].hist(y)
        plt.tight_layout()

    else:
        return jsonify({"error": "Unsupported chart type"}), 400

    plt.title(f"{chart_type.upper()} Chart")
    chart_img = os.path.join(OUTPUT_DIR, "chart.png")
    plt.savefig(chart_img)
    plt.close()

    # ===== CREATE PDF =====
    pdf_path = os.path.join(OUTPUT_DIR, "chart.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.drawImage(chart_img, 50, 300, width=500, height=300)
    c.save()

    # ✅ RETURN PDF (THIS IS WHAT MAKE.COM MUST ATTACH)
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="chart.pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
