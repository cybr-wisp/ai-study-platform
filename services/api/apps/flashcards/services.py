import json
from openai import OpenAI
from .models import Flashcard

class FlashcardService:
    @staticmethod
    def generate_and_save_flashcards(notes_content: str):
        # Initialize the OpenAI client (assumes API key is in environment variables)
        client = OpenAI()
        
        # Call the OpenAI API using the system and user prompts from the tutorial
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": """You are an educational content creator who specializes in making flashcards.
Rules for creating flashcards:
1. Answers must be two sentences max.
2. Only extract content that seems important.

CRITICAL: Only respond with valid JSON in this exact format:
[
  {"question": "...", "answer": "..."}
]

Do not include any text before or after the JSON. Do not use markdown formatting."""
                },
                {
                    "role": "user",
                    "content": f"Create educational flashcards from this content:\n\n{notes_content}"
                }
            ]
        )
        
        output_text = response.output_text
        
        # Parse the JSON response and save each flashcard to the database
        try:
            flashcards_data = json.loads(output_text)
            created_flashcards = []
            for item in flashcards_data:
                flashcard = Flashcard.objects.create(
                    question=item.get("question"),
                    answer=item.get("answer")
                )
                created_flashcards.append(flashcard)
            return created_flashcards
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from OpenAI response: {e}\nResponse was: {output_text}")