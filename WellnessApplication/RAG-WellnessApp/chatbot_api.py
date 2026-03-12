from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from datetime import datetime
import os

app = FastAPI(title="Wellness Chatbot API")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class RAGChatbot:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGChatbot, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        print("Initializing RAG Chatbot...")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.vectorstore = Chroma(
            persist_directory="vectorstore",
            embedding_function=self.embeddings
        )
        
        self.llm = Ollama(
            model="llama3.2:3b",
            temperature=0.2,
            base_url="http://host.docker.internal:11434"
        )
        
        template = """You are a helpful wellness chatbot. Answer based ONLY on the context below.

        Context: {context}
        Question: {question}
        Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": prompt}
        )
        
        print("RAG Chatbot initialized successfully")
    
    def get_response(self, question: str):
        result = self.qa_chain.invoke({"query": question})
        return result['result']

chatbot = None

@app.on_event("startup")
async def startup_event():
    global chatbot
    chatbot = RAGChatbot()
    print("Chatbot API started on port 7999")

@app.get("/")
async def root():
    return {"message": "Wellness Chatbot API is running", "port": 7999}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if chatbot is None:
            raise HTTPException(status_code=503, detail="Chatbot not initialized")
        
        response = chatbot.get_response(request.message)
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))