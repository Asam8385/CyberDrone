import pymupdf
import json

doc = pymupdf.open("ANET_Investment_Identification_Report.pdf")
page = doc[2]

data = page.get_text("dict", sort=True, flags=pymupdf.TEXTFLAGS_TEXT)

with open("text.json", "w" , encoding="utf-8") as file:
   json.dump(data, file , indent=2, ensure_ascii=False )
   