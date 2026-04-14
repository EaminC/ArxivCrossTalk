from arxiv2text import arxiv_to_text

pdf_url = "https://arxiv.org/pdf/1706.03762"
text = arxiv_to_text(pdf_url)
print(text)