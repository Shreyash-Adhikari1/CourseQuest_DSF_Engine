import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# same paths as indexer
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CHROMA_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'chroma_db'))
COLLECTION_NAME = "coursequest_knowledge"


def get_retriever():
    """
    Loads the existing ChromaDB index and returns a retriever object.
    The index must already exist — run indexer.build_index() first.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )


def retrieve_context(query: str) -> str:
    """
    Takes a query string, searches ChromaDB for the most relevant chunks,
    and returns them as one combined context string.
    """
    retriever = get_retriever()
    docs = retriever.invoke(query)

    context = "\n\n".join([doc.page_content for doc in docs])
    return context