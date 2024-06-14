from openai import OpenAI
client = OpenAI(api_key = "YOUR_API_KEY")
client.models.delete("ft:gpt-3.5-turbo-0125:dcc::9UtLTl79")
