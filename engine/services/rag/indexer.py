import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# get the project root directory (where manage.py lives)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# path to your knowledge base folder
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, 'rag_knowledge_base')

# path where ChromaDB will persist the embeddings
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'chroma_db')

# path where ChromaDB will persist the embeddings
CHROMA_DB_PATH = os.path.abspath(os.path.join)(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'chroma_db'
)

COLLECTION_NAME = "coursequest_knowledge"


def build_index():
    """
    Reads all markdown files from the knowledge base,
    splits them into chunks, embeds them using sentence-transformers,
    and stores them in ChromaDB.
    Run this once to build the index.
    """
    print(f"Knowledge base path: {KNOWLEDGE_BASE_PATH}")
    print(f"Path exists: {os.path.exists(KNOWLEDGE_BASE_PATH)}")
    print("Loading knowledge base documents...")

    loader = DirectoryLoader(
        KNOWLEDGE_BASE_PATH,
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")

    print("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    print("Storing embeddings in ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME
    )

    print(f"Index built successfully. {len(chunks)} chunks stored in ChromaDB.")
    vectorstore.persist()
    print(f"ChromaDB persisted to: {CHROMA_DB_PATH}")
    return vectorstore