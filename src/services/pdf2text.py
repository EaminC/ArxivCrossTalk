from arxiv2text import arxiv_to_text


def _normalize_arxiv_url(url: str) -> str:
    url = url.strip()
    if "/abs/" in url:
        paper_id = url.split("/abs/", 1)[-1].strip("/")
        return f"https://arxiv.org/pdf/{paper_id}.pdf"
    if "/pdf/" in url and not url.endswith(".pdf"):
        return url + ".pdf"
    return url


def pdf_to_text(arxiv_url: str, max_chars: int = 32000) -> str:
    pdf_url = _normalize_arxiv_url(arxiv_url)
    text = arxiv_to_text(pdf_url)
    return text[:max_chars]
