import os
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from models import create_table
from langchain_groq import ChatGroq

load_dotenv()
API_key=os.getenv("GROQ_API_KEY")

create_table()

# files_dir = "files/"
# os.makedirs(files_dir, exist_ok=True)

persist_directory = "./chromaDB"
os.makedirs(persist_directory, exist_ok=True)

def create_file(file_path, collection_name):
    try:
        print("file_name:",file_path)
        print("collection_name",collection_name)
        print("DEBUG: Starting create_file function")
        # Load PDF
        loader = PyPDFLoader(file_path)
        print("loader",loader)
        documents = loader.load()
        print("documents",documents)
        print(f"DEBUG: Loaded documents {len(documents)} pages")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        print("text_spliter",text_splitter)
        # Split into chunks
        chunks = text_splitter.split_documents(documents)
        print("chunks",chunks)
        print(f"DEBUG: Split into {len(chunks)} chunks")

        embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        print("embedding",embedding)
        # Initialize Chroma (loads existing collection if already created)
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=persist_directory
            )
        print("vector_store",vector_store)

        # Add to vector store
        vector_store.add_documents(chunks)
        # vector_store.persist()

        # Get all documents
        data = vector_store.get()

        print("Total stored chunks:", len(data["documents"]))
        print("data",data)

        # Print file names
        for metadata in data["metadatas"]:
            print(metadata.get("source"))

        print("DEBUG: Successfully stored in chromaDB")

        return {"uploaded_file": file_path, "collection": collection_name}
 
    except Exception as e:
        print(f"DEBUG: Exception caught: {e}")
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")


def process_file(query: str, collection_name: str):
    try:
        print("query",query)
        print("collection_name",collection_name)

        embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

        # Load existing collection
        vector_store = Chroma(
            embedding_function=embedding,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        print("vector_store",vector_store)

        docs = vector_store.similarity_search(query, k=5) 
        
        print(f"dubug:{docs}")

        context = "\n".join([doc.page_content for doc in docs])
        #print("Context___:", context)

        prompt = f"""
        You are a Retrieval-Augmented Question Answering Assistant.

        You must answer the retrieved context provided below.

        RULES:

        1. Use ONLY the retrieved context.
        2. Do NOT use external knowledge.
        3. Do NOT guess, assume, or infer missing details.
        4. If the answer is not  present in the context, respond exactly:
        "Information not found in the provided context."
        5. Keep the answer short, precise and complete.
        6. Do NOT add explanations, summaries, or extra information.

        
        Question:
        {query}

        Retrieved Context:
        {context}

        """
        
        # LLM
        llm = ChatGroq(
            api_key=API_key,
            model_name="llama-3.3-70b-versatile"
        )
        
        result = llm.invoke(prompt)
        print("result",result)

        return JSONResponse(content={
            'response': result.content,
            'collections_name': collection_name
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")


def get_all_documents(collection_name: str):
    try:
        embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=persist_directory
        )

        data = vector_store.get(include=["documents", "metadatas"])

        documents_list = []

        for i in range(len(data["ids"])):
            documents_list.append({
                "document_id": data["ids"][i],
                "content": data["documents"][i],
                "metadata": data["metadatas"][i]
            })

        return documents_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_document_by_id(collection_name: str, document_id: str):
    try:
        embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=persist_directory
        )

        data = vector_store.get(
            ids=[document_id],
            include=["documents", "metadatas"]
        )

        # Check if document exists
        if not data["ids"]:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return {
            "document_id": data["ids"][0],        
            "content": data["documents"][0],
            "metadata": data["metadatas"][0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

