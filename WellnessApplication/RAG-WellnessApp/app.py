import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

st.title("🌿 Wellness Chatbot")

@st.cache_resource
def load_chatbot():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = Chroma(
        persist_directory="vectorstore",
        embedding_function=embeddings
    )
    llm = Ollama(model="llama3.2:3b", temperature=0.2)
    
    template = """You are a helpful wellness chatbot. Answer based ONLY on the context below.

    Context: {context}
    Question: {question}
    Answer:"""
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain

qa_chain = load_chatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything about wellness..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = qa_chain.invoke({"query": prompt})
            response = result['result']
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})