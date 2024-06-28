from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
from openai import OpenAI
import json
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)
api_key = "YOUR_OPEN_AI_KEY"
client = MongoClient('mongodb://localhost:27017/')

db = client['invoiceDB']
collection = db['invoices']


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
                {"role": "user", "content": "6. PAN ID"},
                {"role": "user", "content": "7. GST number"},
                {"role": "user", "content": "8. List of items"},
                {"role": "user", "content": "9. Total amount including GST"},
                {"role": "user",
                 "content": "Output the results as a single JSON object with the following structure, ensuring no backslashes are present:"},
                {"role": "user", "content": """
            {
              "Details": {
              "invoice_details":{
                "invoice_number": "string"
                "invoices_date": "YYYY-MM-DD",
                "purchase_order_number": "string",
                "purchases_date": "YYYY-MM-DD"
                
                }
                 "tax_details":{
                 "pan_id": "string",
                 "gst_number": "string",
                 },
                "purchaser_address": "string",
              },
              
              
             
              
              "purchase_details":{"items": [
              ],
              "total_amount_with_gst": number
              }
            }
                """},
                {"role": "user", "content": "Ensure all attributes are included even if they have a value of 0."},
                {"role": "user",
                 "content": "If the invoice spans multiple pages or there are multiple invoices in one PDF but share the same address and ID, merge them into a single invoice."},
                {"role": "user",
                 "content": "For all price and quantity values, ensure they are in number format (not string format). For example, 'quantity': 2 and 'unit_price': 100.00."},
                {"role": "user",
                 "content": "Replace any special characters or symbols such as '\\u20b9' with 'Rs.' throughout the document."},
                {"role": "user",
                 "content": "Here is an example of the expected JSON format: {\"Details\":{\"invoice_details\":{ \"invoice_number\": \"INV123456\",\"invoices_date\": \"2023-05-21\", \"purchase_order_number\": \"PO654321\",\"purchases_date\": \"2023-05-20\"},  \"tax_details\":{\"pan_id\": \"ABCDE1234F\", \"gst_number\": \"12ABCDE3456F1Z1\"},\"purchaser_address\": \"123 Street Name, City, State, ZIP\"}, \"purchase_details\":{\"items\": [{\"name\": \"Item1\", \"quantity\": 2, \"unit_price\": 100, \"total_price\": 200}, {\"name\": \"Item2\", \"quantity\": 0, \"unit_price\": 0, \"total_price\": 0}], \"total_amount_with_gst\": 230.50}}."},
                {"role": "user", "content": "Provide only the JSON output in the specified format."},
                {"role": "user", "content": "If any required fields are missing or empty, set their values to 'N/A'."},
                {"role": "user",
                 "content": "Sum the 'total_price' of all items to verify it matches the 'total_amount_with_gst'."}
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
    print(request.files)
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
                    json_data['filename'] = uploaded_file.filename  # Ensure filename is included
                    insertion_result = collection.insert_one(json_data)
                    results.append({uploaded_file.filename: {**json_data, '_id': str(insertion_result.inserted_id)}})
                except json.JSONDecodeError:
                    results.append({uploaded_file.filename: {'error': 'Error converting response to JSON'}})
            else:
                results.append({uploaded_file.filename: {'error': 'Could not get response from AI'}})
        else:
            results.append({uploaded_file.filename: {'error': 'Could not read text from PDF'}})

    return jsonify(results)


@app.route('/list_invoices', methods=['GET'])
def list_invoices():
    try:
        filenames = [doc['filename']
        for doc in collection.find({}, {'filename': 1,'_id': 0})]
        return jsonify({'invoices': filenames})
    except Exception as e:
        print(f"Error fetching invoices from MongoDB: {e}")
        return jsonify({'error': 'Failed to fetch invoices'}), 500


@app.route('/get_invoice_json', methods=['GET'])
def get_invoice_json():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': 'Filename not provided'}), 400

    invoice = collection.find_one({'filename': filename}, {'_id': 0})
    if invoice:
        return jsonify(invoice)
    else:
        return jsonify({'error': 'Invoice not found'}), 404

@app.route('/update_invoice', methods=['PUT'])
def update_invoice():
    data = request.get_json()

    if not data or 'filename' not in data:
        return jsonify({'error': 'Invalid data. Filename is required.'}), 400

    filename = data.pop('filename', None)
    if not filename:
        return jsonify({'error': 'Filename is missing.'}), 400

    try:
        result = collection.update_one({'filename': filename}, {'$set': data})
        if result.matched_count > 0:
            return jsonify({'success': 'Invoice updated successfully'})
        else:
            return jsonify({'error': 'Invoice not found'}), 404
    except Exception as e:
        print(f"Error updating invoice in MongoDB: {e}")
        return jsonify({'error': 'Failed to update invoice'}), 500




if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)
