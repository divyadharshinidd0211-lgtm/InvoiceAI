import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


def extract_invoice_details(customer_message):

    prompt = f"""
You are an invoice data extraction assistant.

Extract information from the customer's message.

Return ONLY valid JSON.

Use this exact structure:

{{
    "customer_name": "",
    "email": "",
    "services": [
        {{
            "service_name": "",
            "quantity": 0
        }}
    ],
    "notes": ""
}}

Rules:
1. Extract the customer's name.
2. Extract the customer's email.
3. Extract every requested service.
4. Extract the quantity for each service.
5. If quantity is not mentioned, use 1.
6. Do NOT create or guess prices.
7. Do NOT add services that the customer did not request.
8. Put additional requirements in notes.
9. Return only JSON.

Customer message:

{customer_message}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)