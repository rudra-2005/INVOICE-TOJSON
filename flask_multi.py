from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)  
api_key = "YOUR_API_KEY"

def read_text_from_pdf(pdf_stream):
    try:
        text = ""
        doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error occurred in reading pdf: {e}")
        return None

def com_with_AI(api_key, text):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                  {"role": "user", "content": text},
                 {"role": "user", "content": "Please extract the following details from the invoice text:"},
                 {"role": "user", "content": "1. Invoice date (format: YYYY-MM-DD)"},
                 {"role": "user", "content": "2. Invoice number"},
                 {"role": "user", "content": "3. Purchase order number"},
                 {"role": "user", "content": "4. Purchase date (format: YYYY-MM-DD)"},
                 {"role": "user", "content": "5. Purchaser address"},
                 {"role": "user", "content": "6. List of items (name, quantity, unit price, total price)"},
                 {"role": "user", "content": "7. PAN ID"},
                 {"role": "user", "content": "8. GST number"},
                 {"role": "user", "content": "9. Total amount including GST"},
                 {"role": "user", "content": "Output the results as a single JSON object in one line without any backslashes. If an attribute has a value of 0, include it in the output with the value 0."},
                 {"role": "user", "content": "If the invoice spans multiple pages or there are multiple invoices in one PDF but share the same address and ID, merge them into a single invoice."},
                 {"role": "user", "content": "For all price and quantity values, ensure they are in number format (not string format). For example, \"quantity\": 2 and \"unit_price\": 100.00."},
                 {"role": "user", "content": "Replace any special characters or symbols such as '\u20b9' with 'Rs.' throughout the document."},
                 {"role": "user", "content": "The currency has to be mentioned seperately just before the list of items "},
                 {"role": "user", "content": "Here is an example of the expected JSON format: {\"invoice_date\": \"2023-05-21\", \"invoice_number\": \"INV123456\", \"purchase_order_number\": \"PO654321\", \"purchase_date\": \"2023-05-20\", \"purchaser_address\": \"123 Street Name, City, State, ZIP\", \"items\": [{\"name\": \"Item1\", \"quantity\": 2, \"unit_price\": 100, \"total_price\": 200}, {\"name\": \"Item2\", \"quantity\": 0, \"unit_price\": 0, \"total_price\": 0}], \"pan_id\": \"ABCDE1234F\", \"gst_number\": \"12ABCDE3456F1Z1\", \"total_amount_with_gst\": 230.50}."},
                 {"role": "user", "content": "Provide only the JSON output in the specified format."},
                 {"role": "user", "content": "If any required fields are missing or empty, set their values to 'N/A'."},
                 {"role": "user", "content": "Sum the 'total price' of all items to verify it matches the 'total amount with GST'."}
  
        ]
        )
        return response.choices[0]
    except Exception as e:
        print(f"Error in generating response from AI: {e}")
        return None

@app.route('/extract_invoice_json', methods=['POST'])
def extract_invoice_json():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files')
    results = []

    for uploaded_file in files:
        if not uploaded_file.filename.lower().endswith('.pdf'):
            results.append({uploaded_file.filename: {'error': 'Invalid file type. Only PDF files are supported'}})
            continue

        pdf_text = read_text_from_pdf(uploaded_file)
        if pdf_text:
            output = com_with_AI(api_key, pdf_text)
            if output:
                try:
                    json_data = json.loads(output.message.content)
                    results.append({uploaded_file.filename: json_data})
                except json.JSONDecodeError:
                    results.append({uploaded_file.filename: {'error': 'Error converting response to JSON'}})
            else:
                results.append({uploaded_file.filename: {'error': 'Could not get response from AI'}})
        else:
            results.append({uploaded_file.filename: {'error': 'Could not read text from PDF'}})

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
