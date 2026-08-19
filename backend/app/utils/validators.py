"""Question validation utilities."""

from typing import List, Set

from app.models.quiz import QuizQuestion


def validate_question_uniqueness(questions: List[QuizQuestion]) -> List[QuizQuestion]:
    """
    Remove duplicate questions based on text similarity.

    Args:
        questions: List of questions to deduplicate

    Returns:
        List of unique questions
    """
    seen_texts: Set[str] = set()
    unique_questions: List[QuizQuestion] = []

    for q in questions:
        # Normalize question text for comparison
        normalized = q.question.lower().strip()
        normalized = " ".join(normalized.split())  # Remove extra whitespace

        # Check for similarity with existing questions
        is_duplicate = False
        for seen in seen_texts:
            if _text_similarity(normalized, seen) > 0.8:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_texts.add(normalized)
            unique_questions.append(q)

    return unique_questions


def _text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity based on word overlap.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def validate_all_questions(questions: List[QuizQuestion]) -> List[QuizQuestion]:
    """
    Validate all questions and filter out invalid ones.

    Args:
        questions: List of questions to validate

    Returns:
        List of valid questions
    """
    valid_questions = []

    for i, q in enumerate(questions, start=1):
        # Check question text
        if not q.question or len(q.question.strip()) < 10:
            continue

        # Check options
        if not q.validate_options():
            continue

        # Check correct answers
        if not q.correct_answers:
            continue

        if not q.validate_correct_answers():
            continue

        # Ensure ID is set
        if not q.id:
            q.id = i

        valid_questions.append(q)

    return valid_questions
