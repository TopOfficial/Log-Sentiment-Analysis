from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader
from contextlib import asynccontextmanager
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from typing import List
from multiprocessing import Pool
import time
import pickle
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Generator, Optional
import time
import json

# Globals
conversation_history_store = {}
llm = None
vector_store = None
conversational_rag_chain = None

# Load environment variables
def load_environment_variables():
    load_dotenv()
    os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "true")  # Enable tracing
    os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

# Initialize LLM
def initialize_llm():
    return init_chat_model(
    "llama3.2:3b-instruct-q8_0",
    model_provider="ollama",
    temperature=0.3,
    # base_url="http://ollama:11434",
    mirostat=None,
    tfs_z=None,
    repeat_penalty=1.1,
)

# Load documents from PDFs (with a named function instead of lambda)
def load_pdf_document(file_path):
    return PyMuPDFLoader(file_path).load()

def load_documents_from_pdfs(folder_path):
    print(f"Scanning folder: {os.path.abspath(folder_path)}")
    pdf_files = [os.path.join(root, file) for root, _, files in os.walk(folder_path) for file in files if file.endswith(".pdf")]
    print(f"PDF files found: {pdf_files}")
    if not pdf_files:
        print("Warning: No PDF files found in the data folder")
    documents = []
    with Pool() as pool:
        documents = pool.map(load_pdf_document, pdf_files)
    documents = [doc for sublist in documents for doc in sublist]
    print(f"Loaded {len(documents)} documents")
    return documents

# Split documents
def split_documents(docs, chunk_size=1200, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True)
    splits_file = "document_splits.pkl"
    if os.path.exists(splits_file):
        with open(splits_file, "rb") as f:
            return pickle.load(f)
    splits = text_splitter.split_documents(docs)
    with open(splits_file, "wb") as f:
        pickle.dump(splits, f)
    return splits

# Initialize embeddings and vector store
def initialize_embeddings_and_store(docs=None):
    global vector_store
    faiss_folder = 'faiss'
    faiss_index_path = os.path.join(faiss_folder, 'index.faiss')
    faiss_metadata_path = os.path.join(faiss_folder, 'index.pkl')

    if vector_store is None:
        if os.path.exists(faiss_index_path) and os.path.exists(faiss_metadata_path):
            print("Loading existing FAISS index...")
            vector_store = FAISS.load_local(faiss_folder, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
            print(f"Loaded documents in FAISS index: {[doc.metadata['file_path'] for doc in vector_store.docstore._dict.values()]}")
        elif docs:
            print("Creating new FAISS index...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            print(f"Embedding documents: {[doc.metadata['file_path'] for doc in docs]}")
            vector_store = FAISS.from_documents(docs, embeddings)
            print("Saving new FAISS index...")
            vector_store.save_local(faiss_folder)
            print(f"Saved FAISS index with {len(vector_store.index_to_docstore_id)} documents")
        else:
            raise ValueError("No documents provided and no existing FAISS index found")
    return vector_store

def get_vector_store():
    global vector_store
    if vector_store is None:
        pdf_folder = "./data"
        docs = load_documents_from_pdfs(pdf_folder)
        all_splits = split_documents(docs)
        vector_store = initialize_embeddings_and_store(all_splits)
    return vector_store

# Create history-aware retriever
def create_history_aware_retriever_chain(llm, retriever):
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [("system", contextualize_q_system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")])
    return create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

# Create RAG chain
def create_rag_chain(llm, retriever):
    system_prompt = """Use the following context and chat history to answer the user's question.
    - Prioritize any solutions or relevant information provided in the chat history, especially those labeled as solutions.
    - If the answer is clear from the chat history or context, respond confidently and concisely.
    - If the answer is not explicitly available, provide the most reasonable answer based on the chat history and context, and state any uncertainties.
    - Limit your response to three sentences or less. Keep the answer clear, concise, and professional.
    **Retrieved Context:**
    {context}"""
    qa_prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

# Manage chat history
def get_conversation_history(conversation_id):
    if conversation_id not in conversation_history_store:
        conversation_history_store[conversation_id] = ChatMessageHistory()
    return conversation_history_store[conversation_id]

# Initialize conversational chain
def initialize_conversational_chain(rag_chain, store):
    return RunnableWithMessageHistory(
        rag_chain,
        lambda conversation_id: get_conversation_history(conversation_id),
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

# Generate UUID
def generate_uuid_session_id():
    return str(uuid.uuid4())

# API Models
class QueryInput(BaseModel):
    conversation_id: str
    query: str

class SessionOutput(BaseModel):
    session_id: str

class QueryResponse(BaseModel):
    answer: str

class MessageCreate(BaseModel):
    SentDate: datetime
    Role: int  # 0 = LLM, 1 = User
    Content: str

class PreloadInput(BaseModel):
    conversation_id: str
    messages: List[MessageCreate]

class MessageResponse(BaseModel):
    SentDate: datetime
    Role: int
    Content: str
    MessageId: str
    ConversationId: str

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, vector_store, conversational_rag_chain
    load_environment_variables()
    llm = initialize_llm()
    yield
    llm = None
    vector_store = None
    conversational_rag_chain = None

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello to the Error Analysis API! Visit /docs for API documentation."}

@app.post("/session", response_model=SessionOutput)
def create_session():
    session_id = generate_uuid_session_id()
    conversation_history_store[session_id] = ChatMessageHistory()
    return SessionOutput(session_id=session_id)

@app.post("/query", response_model=QueryResponse)
def query_bot(query_input: QueryInput):
    global conversational_rag_chain
    conversation_id = query_input.conversation_id
    query = query_input.query

    if conversation_id not in conversation_history_store:
        conversation_history_store[conversation_id] = ChatMessageHistory()
    
    if conversational_rag_chain is None:
        start_time = time.time()
        # Ensure vector_store is initialized before creating the chain
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": 5, "fetch_k": 10})
        history_aware_retriever = create_history_aware_retriever_chain(llm, retriever)
        rag_chain = create_rag_chain(llm, history_aware_retriever)
        conversational_rag_chain = initialize_conversational_chain(rag_chain, conversation_history_store)
        print(f"Chain initialization time: {time.time() - start_time}s")

    start_time = time.time()
    response = conversational_rag_chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": conversation_id}},
    )["answer"]
    # response = conversational_rag_chain.invoke(
    # {"input": query},
    # config={"configurable": {"session_id": conversation_id}},
    # )
    # print(f"Retrieved documents: {response.get('context', [])}")
    print(f"Query response time: {time.time() - start_time}s")

    return QueryResponse(answer=response)


# @app.post("/query")
# async def query_bot(query_input: QueryInput):
#     conversation_id = query_input.conversation_id
#     query = query_input.query

#     if conversation_id not in conversation_history_store:
#         conversation_history_store[conversation_id] = ChatMessageHistory()

#     # Lazily initialize the chain only when needed
#     global conversational_rag_chain
#     if conversational_rag_chain is None:
#         start_time = time.time()
#         vector_store = get_vector_store()
#         retriever = vector_store.as_retriever(search_kwargs={"k": 5, "fetch_k": 10})
#         history_aware_retriever = create_history_aware_retriever_chain(llm, retriever)
#         rag_chain = create_rag_chain(llm, history_aware_retriever)
#         conversational_rag_chain = initialize_conversational_chain(rag_chain, conversation_history_store)
#         print(f"Chain initialization time: {time.time() - start_time}s")

#     # Define a generator function to yield tokens incrementally
#     def generate_stream():
#         try:
#             for chunk in conversational_rag_chain.stream(
#                 {"input": query},
#                 config={"configurable": {"session_id": conversation_id}},
#             ):
#                 # Yield each chunk as it comes (e.g., {"answer": "Hello"}, then more chunks)
#                 if "answer" in chunk:
#                     yield f"data: {json.dumps({'response': chunk['answer']})}\n\n"
#         except Exception as e:
#             yield f"data: {json.dumps({'error': str(e)})}\n\n"

#     return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post("/preload-history")
def preload_history(data: PreloadInput):
    conversation_id = data.conversation_id
    history = get_conversation_history(conversation_id)
    for msg in data.messages:
        if msg.Role == 0:
            history.add_ai_message(msg.Content)
        elif msg.Role == 1:
            history.add_user_message(msg.Content)
    return {"status": "success", "conversation_id": conversation_id}

@app.get("/history/{conversation_id}", response_model=List[MessageResponse])
def get_chat_history(conversation_id: str):
    if conversation_id not in conversation_history_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = get_conversation_history(conversation_id)
    messages = []
    for msg in history.messages:
        message_id = str(uuid.uuid4())
        role = 1 if isinstance(msg, HumanMessage) else 0
        messages.append(
            MessageResponse(
                SentDate=datetime.now(),
                Role=role,
                Content=msg.content,
                MessageId=message_id,
                ConversationId=conversation_id,
            )
        )
    return messages

@app.post("/embed")
def reembed_data():
    global vector_store, conversational_rag_chain
    try:
        vector_store = None  # Reset vector store
        conversational_rag_chain = None  # Reset chain
        pdf_folder = "./data"
        print(f"Scanning folder: {os.path.abspath(pdf_folder)}")
        pdf_files = [os.path.join(root, file) for root, _, files in os.walk(pdf_folder) for file in files if file.endswith(".pdf")]
        print(f"Found PDF files: {pdf_files}")
        if not pdf_files:
            raise ValueError("No PDF files found in ./data folder")
        docs = load_documents_from_pdfs(pdf_folder)
        print(f"Loaded {len(docs)} documents: {[doc.metadata['file_path'] for doc in docs]}")
        all_splits = split_documents(docs)
        print(f"Created {len(all_splits)} document splits: {[split.metadata['file_path'] for split in all_splits]}")
        vector_store = initialize_embeddings_and_store(all_splits)
        print("Re-embedding successful")
        return {"message": "Data has been re-embedded successfully."}
    except Exception as e:
        print(f"Error during re-embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred during re-embedding: {str(e)}")