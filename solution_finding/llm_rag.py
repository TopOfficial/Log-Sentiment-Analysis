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
from langchain_core.messages import HumanMessage, AIMessage
from typing import List
from datetime import datetime

# Globals
conversation_history_store = {}
llm = None
vector_store = None
conversational_rag_chain = None

# Load environment variables
def load_environment_variables():
    load_dotenv()
    os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "false")
    os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")


# Initialize the Large Language Model (LLM)
def initialize_llm():
    return init_chat_model("llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0.3)


# Initialize embeddings and the FAISS store
def initialize_embeddings_and_store(docs):
    faiss_folder = 'faiss'
    faiss_index_path = os.path.join(faiss_folder, 'index.faiss')
    faiss_metadata_path = os.path.join(faiss_folder, 'index.pkl')

    if os.path.exists(faiss_index_path) and os.path.exists(faiss_metadata_path):
        print("Loading existing FAISS index...")
        vector_store = FAISS.load_local(faiss_folder, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
                                        allow_dangerous_deserialization=True)
    else:
        print("Creating new FAISS index...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(docs, embeddings)
        vector_store.save_local(faiss_folder)

    return vector_store


# Load documents from PDFs
def load_documents_from_pdfs(folder_path):
    documents = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                loader = PyMuPDFLoader(file_path)
                documents.extend(loader.load())
    return documents


# Split documents into chunks
def split_documents(docs, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    return text_splitter.split_documents(docs)


# Create a history-aware retriever
def create_history_aware_retriever_chain(llm, retriever):
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    return create_history_aware_retriever(llm, retriever, contextualize_q_prompt)


# Create a RAG chain (Retrieval-Augmented Generation)
def create_rag_chain(llm, retriever):
    system_prompt = """Use the following context to answer the user's question. 

    - If the answer is clear from the context, respond confidently and concisely. 
    - If the answer is not explicitly available, provide the most reasonable answer based on the context and state that you are unsure. 
    - Keep the answer clear, concise, natural, and professional.

    **Context**:
    {context}
    """
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


# Manage chat history
def get_conversation_history(conversation_id):
    if conversation_id not in conversation_history_store:
        conversation_history_store[conversation_id] = ChatMessageHistory()
    return conversation_history_store[conversation_id]


# Create a conversational chain with stateful history
def initialize_conversational_chain(rag_chain, store):
    return RunnableWithMessageHistory(
        rag_chain,
        lambda conversation_id: get_conversation_history(conversation_id),
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )


# Generate a secure UUID for the session
def generate_uuid_session_id():
    return str(uuid.uuid4())


# Preload chat history
def preload_history(conversation_id: str, messages: List[dict]):
    history = get_conversation_history(conversation_id)
    for msg in messages:
        if msg["Role"] == 0:  # AI message
            history.add_ai_message(msg["Content"])
        elif msg["Role"] == 1:  # Human message
            history.add_user_message(msg["Content"])
    return {"status": "success", "conversation_id": conversation_id}


# Query the chatbot
def query_bot(conversation_id: str, query: str):
    if conversation_id not in conversation_history_store:
        conversation_history_store[conversation_id] = ChatMessageHistory()

    response = conversational_rag_chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": conversation_id}},
    )["answer"]

    return response


# Retrieve chat history
def get_chat_history(conversation_id: str):
    if conversation_id not in conversation_history_store:
        raise ValueError("Conversation not found")
    
    history = get_conversation_history(conversation_id)
    messages = []

    for msg in history.messages:
        role = 1 if isinstance(msg, HumanMessage) else 0
        messages.append(
            {
                "SentDate": datetime.now(),  # Use current time or store actual timestamp if available
                "Role": role,
                "Content": msg.content,
                "MessageId": str(uuid.uuid4()),  # Generate unique ID for each message
                "ConversationId": conversation_id,
            }
        )

    return messages


# Main function to test the chatbot workflow
def main():
    global llm, vector_store, conversational_rag_chain

    # Load environment variables
    load_environment_variables()

    # Initialize LLM
    llm = initialize_llm()

    # Load and process documents
    pdf_folder = "./data"  # Replace with your actual PDF folder path
    docs = load_documents_from_pdfs(pdf_folder)
    all_splits = split_documents(docs)

    # Initialize vector store
    vector_store = initialize_embeddings_and_store(all_splits)

    # Create retriever and conversational RAG chain
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    history_aware_retriever = create_history_aware_retriever_chain(llm, retriever)
    rag_chain = create_rag_chain(llm, history_aware_retriever)
    conversational_rag_chain = initialize_conversational_chain(rag_chain, conversation_history_store)

    # Simulate a session
    session_id = generate_uuid_session_id()
    print(f"New session started with ID: {session_id}")

    while True:
        query = input("Enter your question (or type 'exit' to quit): ")
        if query.lower() == "exit":
            break
        response = query_bot(session_id, query)
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
