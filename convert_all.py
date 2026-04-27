from pathlib import Path
from main import md_to_pdf, OUTPUT_DIR

DOCS_DIR = Path(__file__).parent / "docs"

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    files = sorted(DOCS_DIR.glob("*.md"))
    if not files:
        print("No markdown files found in docs/")
        raise SystemExit(1)
    for md_file in files:
        out = OUTPUT_DIR / md_file.with_suffix(".pdf").name
        print(f"Generating PDF for: {md_file.name}")
        md_to_pdf(md_file, out)