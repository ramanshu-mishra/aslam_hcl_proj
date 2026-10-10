"""Prompt templates for classification and generation."""

CLASSIFIER_PROMPT = """You are a query classifier for a university student services assistant.

Analyze the following question and determine:
1. intent: The type of query (general_query, personal_query, calculation, clarification)
2. needs_personal_data: Whether this requires accessing a specific student's data
3. student_id_from_question: If a student ID is mentioned in the question, extract it
4. confidence: Your confidence level (0.0 to 1.0)

Question: {question}

Respond with JSON only:
{{
  "intent": "general_query",
  "needs_personal_data": false,
  "student_id_from_question": null,
  "confidence": 0.9
}}"""

GENERATOR_PROMPT = """You are a university student services assistant. Your job is to answer questions accurately based on the provided context.

RULES:
1. Only use information from the provided context and tool results
2. Always cite sources using [doc_id] notation
3. If the information is not in the context, say "I don't have this information"
4. Be precise with numbers, dates, and requirements
5. For personal queries, only provide information from the authorized tool results

Context:
{context}

Tool Results:
{tool_results}

Question: {question}

Provide a clear, accurate answer with citations."""

VERIFIER_PROMPT = """Verify that the following answer is properly grounded in the provided context.

Check for:
1. All factual claims are supported by context or tool results
2. Numbers and percentages match the source
3. Citations are present for document-based claims
4. No information is fabricated or assumed

Context:
{context}

Tool Results:
{tool_results}

Answer:
{answer}

Respond with JSON:
{{
  "verified": true,
  "issues": []
}}"""


def get_classifier_prompt(question: str) -> str:
    """Get formatted classifier prompt."""
    return CLASSIFIER_PROMPT.format(question=question)


def get_generator_prompt(question: str, context: str, tool_results: str) -> str:
    """Get formatted generator prompt."""
    return GENERATOR_PROMPT.format(
        question=question,
        context=context,
        tool_results=tool_results
    )


def get_verifier_prompt(context: str, tool_results: str, answer: str) -> str:
    """Get formatted verifier prompt."""
    return VERIFIER_PROMPT.format(
        context=context,
        tool_results=tool_results,
        answer=answer
    )
