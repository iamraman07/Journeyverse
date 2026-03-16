import os
from google import genai

if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key.strip()] = value.strip('"\'')

api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("API Key not found.")
else:
    print(f"API Key found ending in: {api_key[-4:]}")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say hello.'
        )
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)
