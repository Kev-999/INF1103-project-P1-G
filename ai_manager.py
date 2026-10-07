import os, json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

load_dotenv()
logging.getLogger("google_genai").setLevel(logging.ERROR)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def categorize_expense(expense):
    prompt = f"""Categorize this expense. Return ONLY valid JSON with keys:
    category (one of Food, Drinks, Transport, Entertainment, Education Materials, Other).

    Description: "{expense['description']}"
    """
    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    except (json.JSONDecodeError, AttributeError) as e:
        logging.error(f"Failed to parse AI response: {e}")
        return None

    except Exception as e:
        logging.error(f"AI API call failed: {e}")
        return None


# if __name__ == "__main__":
#     test_expense = {"description": "Bubble tea at NEX"}
#     result = categorize_expense(test_expense)
#     print(result)