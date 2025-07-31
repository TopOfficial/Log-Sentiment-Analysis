from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
faiss_folder = 'faiss'
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.load_local(faiss_folder, embeddings, allow_dangerous_deserialization=True)
print("Documents in FAISS index:")
for doc_id in vector_store.index_to_docstore_id.values():
    doc = vector_store.docstore._dict[doc_id]
    print(f"Document: {doc.metadata['file_path']}")