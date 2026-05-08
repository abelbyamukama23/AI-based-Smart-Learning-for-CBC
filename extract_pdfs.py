import pdfplumber
import os

pdf_dir = r"c:\Users\user\Desktop\CBC\Project files"
out_dir = r"c:\Users\user\Desktop\CBC\Project files\extracted"
os.makedirs(out_dir, exist_ok=True)

pdfs = [
    "CBC_SRS_v1.0 (1) (2).pdf",
    "CBC_Stage_B_Use_Case_Modelling.pdf",
    "CBC_Stage_C_Domain_Modelling.pdf",
    "CBC_Stage_F_Database_Data_Design.pdf",
    "CBC_Stage_E_Architectural_Design.pdf",
]

for pdf_name in pdfs:
    path = os.path.join(pdf_dir, pdf_name)
    out_name = pdf_name.replace(".pdf", ".txt").replace(" ", "_").replace("(","").replace(")","")
    out_path = os.path.join(out_dir, out_name)
    print(f"\n{'='*60}")
    print(f"Extracting: {pdf_name}")
    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n{page_text}"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  -> Written {len(text)} chars to {out_name}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone!")
