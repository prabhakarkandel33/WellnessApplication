from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

print("Loading documents from knowledge_base/...")

documents = []
for root, dirs, files in os.walk('knowledge_base'):
    for file in files:
        if file.endswith('.txt'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'page_content': content,
                        'metadata': {'source': file_path}
                    })
                    print(f"Loaded: {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

print(f"\nLoaded {len(documents)} documents")

from langchain.docstore.document import Document
docs = [Document(page_content=d['page_content'], metadata=d['metadata']) for d in documents]

print("Splitting documents into chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)
print(f"Created {len(chunks)} chunks")

print("Creating embeddings (this takes 5-10 minutes, be patient)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Building vectorstore...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="vectorstore"
)

print("DONE! Vectorstore saved to ./vectorstore")