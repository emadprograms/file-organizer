import fitz
doc = fitz.open('510.pdf')
doc_new = fitz.open()
doc_new.insert_pdf(doc, from_page=0, to_page=0)
doc_new.save('single_page.pdf')
doc_new.close()
doc.close()
print("Saved single_page.pdf")
