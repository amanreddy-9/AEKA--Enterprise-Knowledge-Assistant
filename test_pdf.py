import fitz
import os

pdf_path = r"C:\Users\Aman Reddy\Documents\Aeka TechM\backend\History of Mahindra Cars.pdf"

print("File exists:", os.path.exists(pdf_path))
print("File size:", os.path.getsize(pdf_path), "bytes")

doc = fitz.open(pdf_path)
print("Page count:", len(doc))

for i, page in enumerate(doc):
    text = page.get_text("text")
    print(f"Page {i}: chars={len(text)}")
    if text.strip():
        print("  Preview:", text[:100])
    else:
        print("  NO TEXT on this page")

doc.close()