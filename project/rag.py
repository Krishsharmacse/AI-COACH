import sys
from pathlib import Path

PDF_PATH = Path(r"C:\Users\Krish Sharma\Downloads\zenodo.12752414.pdf")
DB_PATH = Path("./rag_faiss_db")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    try:
        import importlib

        PyPDFLoader = importlib.import_module("langchain_community.document_loaders").PyPDFLoader
        RecursiveCharacterTextSplitter = importlib.import_module("langchain.text_splitter").RecursiveCharacterTextSplitter
        HuggingFaceEmbeddings = importlib.import_module("langchain_huggingface").HuggingFaceEmbeddings
        FAISS = importlib.import_module("langchain_community.vectorstores").FAISS
    except Exception as e:
        print("Missing optional dependencies for RAG:", e)
        print("Install required packages, e.g. `pip install langchain langchain-huggingface langchain-community faiss-cpu sentence-transformers` and try again.")
        sys.exit(1)

    if not PDF_PATH.exists():
        print(f"PDF not found at {PDF_PATH}. Update PDF_PATH and retry.")
        sys.exit(1)

    loader = PyPDFLoader(str(PDF_PATH))
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    docs = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    db = FAISS.from_documents(docs, embeddings)
    DB_PATH.mkdir(parents=True, exist_ok=True)
    db.save_local(str(DB_PATH))

    query = "What is the main research objective?"
    results = db.similarity_search(query, k=3)

    for i, doc in enumerate(results, 1):
        print(doc.page_content[:700])


if __name__ == "__main__":
    main()