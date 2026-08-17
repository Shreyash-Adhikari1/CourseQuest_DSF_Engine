import ollama
from engine.services.rag.retriever import retrieve_context

SYSTEM_PROMPT = """
You are an automated academic pathway recommendation system.

Generate professional, objective and evidence-based recommendation reports.

Follow these rules exactly:

- Never use first-person language.
- Never write: I, me, my, we, our, us.
- Address the student using "you" and "your".
- Base every statement ONLY on:
  - assessment responses
  - identified strengths
  - identified areas for improvement
  - pathway information provided

Never assume or invent information.

The system has NO information about:
- academic background
- academic history
- academic profile
- current profile
- educational profile
- student profile
- personal profile
- work experience
- employment history
- previous studies
- previous achievements
- qualifications
- GPA
- grades
- transcript
- certifications
- projects
- extracurricular activities

Never mention or imply any of these.

Instead, use expressions such as:
- Based on your assessment responses...
- The assessment indicates...
- The assessment findings suggest...
- Your identified strengths indicate...
- The assessment results support...

Do not use:
- Based on your academic background...
- Based on your profile...
- Your academic profile...
- Your current profile...
- Your educational history...
- Considering your work experience...
"""

DISPLAY_NAMES = {
    "security_interest": "Security Interest",
    "security_awareness": "Security Awareness",
    "ai_interest": "Artificial Intelligence Interest",
    "programming_interest": "Programming Interest",
    "logical_reasoning": "Logical Reasoning",
    "systems_interest": "Systems Interest",
}

def build_prompt(recommendation_data: dict, context: str) -> str:
    """
    Builds a structured three-part prompt covering primary,
    secondary, and tertiary pathway recommendations.
    """

    strengths = [
        DISPLAY_NAMES.get(item, item.replace("_", " ").title())
        for item in recommendation_data["strengths"]
    ]

    improvements = [
        DISPLAY_NAMES.get(item, item.replace("_", " ").title())
        for item in recommendation_data["improvements"]
    ]
    return f"""

    Strengths:
    {', '.join(strengths)}

    Areas for Improvement:
    {', '.join(improvements)}

Generate a professional recommendation report.

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
the gap between the student's current assessment results and the requirements of this pathway]

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
    print(context)

    # build the prompt
    prompt = build_prompt(recommendation_data, context)

    # call Ollama locally
    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {
        "role": "system",
        "content": SYSTEM_PROMPT
    },
            {"role": "user", "content": prompt}
        ],
        options={
        "temperature": 0.2,
    }
    ) 

    return response['message']['content']