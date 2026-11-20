import os, fitz

fig_dir = "writing_paper/figures"
for f in os.listdir(fig_dir):
    if f.endswith(".pdf"):
        pdf_path = os.path.join(fig_dir, f)
        png_path = os.path.join(fig_dir, f.replace(".pdf", ".png"))
        doc = fitz.open(pdf_path)
        page = doc[0]
        # Render at 600 DPI (zoom = 600/72 = 8.333)
        zoom = 600 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(png_path)
        print(f"Rendered {png_path} ({pix.width}x{pix.height}) at 600 DPI")
