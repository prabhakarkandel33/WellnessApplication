import time
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Test dataset
test_questions = [
    {"question": "What helps with anxiety?", "category": "mental_health"},
    {"question": "How do I improve sleep quality?", "category": "sleep"},
    {"question": "What are good breathing exercises?", "category": "exercise"},
    {"question": "How to manage stress?", "category": "mental_health"},
    {"question": "What causes insomnia?", "category": "sleep"},
    {"question": "Best exercises for beginners?", "category": "exercise"},
    {"question": "How to deal with depression?", "category": "mental_health"},
    {"question": "What is sleep hygiene?", "category": "sleep"},
    {"question": "Benefits of walking?", "category": "exercise"},
    {"question": "How to reduce worry?", "category": "mental_health"},
    {"question": "Tips for better sleep?", "category": "sleep"},
    {"question": "What is box breathing?", "category": "exercise"},
    {"question": "How to handle panic attacks?", "category": "mental_health"},
    {"question": "Why is sleep important?", "category": "sleep"},
    {"question": "How to start yoga?", "category": "exercise"},
    {"question": "What helps with sadness?", "category": "mental_health"},
    {"question": "How much sleep do I need?", "category": "sleep"},
    {"question": "What is meditation?", "category": "exercise"},
    {"question": "How to cope with loneliness?", "category": "mental_health"},
    {"question": "What affects sleep quality?", "category": "sleep"},
    {"question": "Benefits of stretching?", "category": "exercise"},
    {"question": "What is mindfulness?", "category": "mental_health"},
    {"question": "How to fix sleep schedule?", "category": "sleep"},
    {"question": "What is progressive muscle relaxation?", "category": "exercise"},
    {"question": "How to manage work stress?", "category": "mental_health"},
    {"question": "What helps with hangovers?", "category": "wellness"},
    {"question": "How to maintain skincare routine?", "category": "wellness"},
    {"question": "What causes headaches?", "category": "wellness"},
    {"question": "How to stay hydrated?", "category": "wellness"},
    {"question": "Benefits of good posture?", "category": "wellness"}
]

print("Initializing RAG system...")

# Load components
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="vectorstore",
    embedding_function=embeddings
)

llm = Ollama(
    model="llama3.2:3b",
    temperature=0.2
)

template = """You are a helpful wellness chatbot. Answer based ONLY on the context below.

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
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True
)

print("Starting evaluation...\n")

# Metrics storage
retrieval_scores = []
latencies = []
response_lengths = []
token_counts = []
successes = 0
failures = 0
detailed_results = []

# Run evaluation
for idx, test in enumerate(test_questions, 1):
    print(f"[{idx}/{len(test_questions)}] Testing: {test['question'][:50]}...")
    
    try:
        # Measure retrieval quality
        retrieval_start = time.time()
        retrieved_docs = vectorstore.similarity_search_with_score(
            test["question"], k=3
        )
        retrieval_time = time.time() - retrieval_start
        
        # Get similarity score of top result
        top_similarity = retrieved_docs[0][1] if retrieved_docs else 0
        retrieval_scores.append(top_similarity)
        
        # Measure generation latency
        gen_start = time.time()
        response = qa_chain.invoke({"query": test["question"]})
        total_time = time.time() - gen_start
        
        latencies.append(total_time)
        response_text = response['result']
        response_lengths.append(len(response_text))
        
        # Estimate tokens (rough: ~4 chars per token)
        token_counts.append(len(response_text) // 4)
        
        successes += 1
        
        # Store detailed result
        detailed_results.append({
            "question": test["question"],
            "category": test["category"],
            "similarity_score": float(top_similarity),
            "latency": float(total_time),
            "response_length": len(response_text),
            "response": response_text[:200] + "..." if len(response_text) > 200 else response_text
        })
        
        print(f"  ✓ Success | Latency: {total_time:.2f}s | Similarity: {top_similarity:.3f}")
        
    except Exception as e:
        failures += 1
        print(f"  ✗ Failed: {str(e)}")
        detailed_results.append({
            "question": test["question"],
            "category": test["category"],
            "error": str(e)
        })

print("\n" + "="*70)
print("EVALUATION COMPLETE")
print("="*70)

# Calculate metrics
total_queries = len(test_questions)
avg_similarity = sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0
avg_latency = sum(latencies) / len(latencies) if latencies else 0
min_latency = min(latencies) if latencies else 0
max_latency = max(latencies) if latencies else 0
avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
success_rate = successes / total_queries

# Compile results
results = {
    "evaluation_summary": {
        "total_queries": total_queries,
        "successful_queries": successes,
        "failed_queries": failures,
        "success_rate": success_rate
    },
    "retrieval_metrics": {
        "avg_similarity_score": avg_similarity,
        "max_similarity_score": max(retrieval_scores) if retrieval_scores else 0,
        "min_similarity_score": min(retrieval_scores) if retrieval_scores else 0
    },
    "generation_metrics": {
        "avg_latency_seconds": avg_latency,
        "min_latency_seconds": min_latency,
        "max_latency_seconds": max_latency,
        "avg_response_length_chars": avg_response_length,
        "avg_response_tokens": avg_tokens
    },
    "detailed_results": detailed_results
}

# Print summary
print(f"\nRetrieval Performance:")
print(f"  Average Similarity Score: {avg_similarity:.3f}")
print(f"  Similarity Range: {min(retrieval_scores) if retrieval_scores else 0:.3f} - {max(retrieval_scores) if retrieval_scores else 0:.3f}")

print(f"\nGeneration Performance:")
print(f"  Average Latency: {avg_latency:.2f}s")
print(f"  Latency Range: {min_latency:.2f}s - {max_latency:.2f}s")
print(f"  Average Response Length: {avg_response_length:.0f} characters")
print(f"  Average Response Tokens: {avg_tokens:.0f} tokens")

print(f"\nReliability:")
print(f"  Success Rate: {success_rate:.1%}")
print(f"  Successful Queries: {successes}/{total_queries}")
print(f"  Failed Queries: {failures}/{total_queries}")

# Save results
with open('rag_evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to 'rag_evaluation_results.json'")
print("="*70)

