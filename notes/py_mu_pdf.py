import pymupdf4llm

md_text = pymupdf4llm.to_markdown("ANET_Investment_Identification_Report.pdf")

with open("output.md", "w", encoding="utf-8") as f:
    f.write(md_text)
