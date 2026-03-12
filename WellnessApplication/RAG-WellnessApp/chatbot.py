from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from safety import check_crisis, get_crisis_response


print("Loading vectorstore...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = Chroma(
    persist_directory="vectorstore",
    embedding_function=embeddings
)

print("Loading LLM...")
llm = Ollama(
    model="llama3.2:3b",
    temperature=0.2
)

template = """You are a helpful wellness chatbot. Answer based ONLY on the context below.

RULES:
- If you don't know the answer from the context, say "I don't have information about that."
- Never make up information
- Never use knowledge outside the provided context
- Be friendly and supportive

Context:
{context}

Question: {question}

Answer:"""

prompt = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={"prompt": prompt}
)

print("\n" + "="*50)
print("WELLNESS CHATBOT READY")
print("="*50)
print("Type 'quit' to exit\n")

while True:
    question = input("You: ")
    if question.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        break
    
    if check_crisis(question):
        print(f"\nBot: {get_crisis_response()}\n")
        continue
    
    print("\nThinking...\n")
    response = qa_chain.invoke({"query": question})
    print(f"Bot: {response['result']}\n")
