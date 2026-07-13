"""
PDF Ingestor for Islamic RAG
Handles: Tafseer, Fiqh books, Husnul Muslim, any PDF
Usage:  python3 ingest_pdf.py yourbook.pdf "Book Title" bookkey
"""

import sys, os, json
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH  = "./chroma_db"
COLLECTION   = "islamic_texts"
BATCH_SIZE   = 50
MAX_CHUNK    = 800
MIN_CHUNK    = 40

def install_deps():
    os.system("pip install pymupdf pytesseract pillow --break-system-packages -q")
    os.system("sudo apt-get install -y tesseract-ocr 2>/dev/null")

def extract_text_pymupdf(pdf_path):
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if len(text) < 50:  # likely scanned — try OCR
            import pytesseract
            from PIL import Image
            import io
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="eng")
        if text.strip():
            pages.append((i + 1, text.strip()))
    return pages

def chunk_page(text, page_num, max_chars=MAX_CHUNK):
    chunks = []
    sentences, temp = [], ""
    for ch in text:
        temp += ch
        if ch in ".!?\n" and len(temp) > 15:
            sentences.append(temp.strip())
            temp = ""
    if temp.strip():
        sentences.append(temp.strip())

    current = ""
    for s in sentences:
        if len(current) + len(s) <= max_chars:
            current += " " + s
        else:
            if current.strip():
                chunks.append(current.strip())
            current = s
    if current.strip():
        chunks.append(current.strip())
    return [(f"p{page_num}_c{i}", c) for i, c in enumerate(chunks) if len(c) >= MIN_CHUNK]

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 ingest_pdf.py file.pdf 'Book Name' bookkey")
        sys.exit(1)

    pdf_path   = sys.argv[1]
    book_name  = sys.argv[2]
    book_key   = sys.argv[3]

    print(f"📖 Processing: {book_name}")
    install_deps()
    pages = extract_text_pymupdf(pdf_path)
    print(f"   Extracted {len(pages)} pages")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    try:
        col = client.get_collection(COLLECTION, embedding_function=ef)
    except:
        col = client.create_collection(COLLECTION, embedding_function=ef,
                                        metadata={"hnsw:space": "cosine"})

    all_texts, all_ids, all_metas = [], [], []
    for page_num, page_text in pages:
        for chunk_id, chunk in chunk_page(page_text, page_num):
            uid = f"{book_key}_{chunk_id}"
            all_texts.append(chunk)
            all_ids.append(uid)
            all_metas.append({
                "source": book_name, "book_key": book_key,
                "type": "book", "hadith_number": str(page_num),
                "arabic_number": "", "book_number": "",
                "grade": "", "chunk_index": chunk_id, "total_chunks": "0"
            })

    print(f"   Total chunks: {len(all_texts)}")
    for start in range(0, len(all_texts), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(all_texts))
        col.add(documents=all_texts[start:end],
                ids=all_ids[start:end],
                metadatas=all_metas[start:end])
        print(f"   Embedded {end}/{len(all_texts)}")

    print(f"✅ Done! Collection now has {col.count():,} docs")

if __name__ == "__main__":
    main()
