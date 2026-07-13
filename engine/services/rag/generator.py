import ollama
from engine.services.rag.retriever import retrieve_context


def build_prompt(recommendation_data: dict, context: str) -> str:
    """
    Builds a structured three-part prompt covering primary,
    secondary, and tertiary pathway recommendations.
    """
    return f"""You are an academic counselor writing a personalized pathway recommendation report for a student.

Write a structured report with THREE clearly labeled sections as shown below.
Each section should be 2-3 paragraphs. Do not mention numerical scores.
Be encouraging but honest — clearly explain why the primary pathway suits the student best,
and what limitations exist for the secondary and tertiary options.

ASSESSMENT RESULTS:
Primary Recommendation: {recommendation_data['primary_pathway']}
Secondary Option: {recommendation_data['secondary_pathway']}
Tertiary Option: {recommendation_data['tertiary_pathway']}
Strengths: {', '.join(recommendation_data['strengths'])}
Areas for Improvement: {', '.join(recommendation_data['improvements'])}

PATHWAY INFORMATION:
{context}

Write the report using EXACTLY this structure:

PRIMARY RECOMMENDATION: {recommendation_data['primary_pathway']}
[Your explanation here — why this pathway suits the student, what they will excel at,
career opportunities aligned with their strengths]

SECONDARY OPTION: {recommendation_data['secondary_pathway']}
[Your explanation here — why this is viable, BUT clearly highlight what the student
currently lacks for this pathway and why primary is the better fit]

TERTIARY OPTION: {recommendation_data['tertiary_pathway']}
[Your explanation here — acknowledge this pathway is possible, but be honest about
the gap between the student's current profile and what this pathway demands]

Write the report now:"""


def build_query(recommendation_data: dict) -> str:
    """
    Builds a search query from recommendation data
    to retrieve relevant chunks from ChromaDB.
    """
    return f"""
    student recommended for {recommendation_data['primary_pathway']} pathway,
    also considering {recommendation_data['secondary_pathway']} and {recommendation_data['tertiary_pathway']},
    strengths in {', '.join(recommendation_data['strengths'])},
    improvements needed in {', '.join(recommendation_data['improvements'])}
    """


def generate_explanation(recommendation_data: dict) -> str:
    """
    Takes structured recommendation data, retrieves relevant context,
    builds a structured three-part prompt, and generates a human readable
    report using Ollama. Returns the explanation as a string.
    """
    # retrieve relevant context from ChromaDB
    query = build_query(recommendation_data)
    context = retrieve_context(query)

    # build the prompt
    prompt = build_prompt(recommendation_data, context)

    # call Ollama locally
    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response['message']['content']