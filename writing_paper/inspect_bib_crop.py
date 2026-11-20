import fitz

doc = fitz.open(r"e:\_PROJECTS\visiocrypto\writing_paper\figures\bib_standalone.pdf")
page = doc.load_page(0)
# Find bounding box of text on page
text_instances = page.get_text("blocks")
print("Blocks on page:")
for b in text_instances:
    print(b)

# Render cropped bbox to PNG
# Column 1 rect is roughly x0=45, y0=45 to x1=300, y1=750
# Let's crop to exact bounding box of all text blocks!
rects = [fitz.Rect(b[:4]) for b in text_instances if b[4].strip()]
if rects:
    union_rect = rects[0]
    for r in rects[1:]:
        union_rect |= r
    print("Union bounding box:", union_rect)
    
    # We can render the column or page at 600 DPI
    mat = fitz.Matrix(600 / 72, 600 / 72)
    pix = page.get_pixmap(matrix=mat, clip=union_rect, alpha=False)
    pix.save(r"e:\_PROJECTS\visiocrypto\writing_paper\figures\references_column.png")
    print("Saved references_column.png!")
doc.close()
