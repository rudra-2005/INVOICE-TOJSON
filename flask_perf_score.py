from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
from openai import OpenAI
import json
from pymongo import MongoClient
import base64


app = Flask(__name__)
CORS(app)

api_key = "YOUR_API_KEY"
client = MongoClient('mongodb://localhost:27017/')
db = client['invoiceDB']
collection = db['invoices']


def pdf_pages_to_images(pdf_stream, dpi=300):
    images = []
    try:
        doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
        doc.close()
    except Exception as e:
        print(f"Error converting PDF pages to images: {e}")
        return None
    return images


def extract_data_with_vlm(api_key, images):
    openai_client = OpenAI(api_key=api_key)
    try:
        base64_images = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(img).decode()}"
                }
            } for img in images
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an assistant that ONLY replies with valid JSON matching the specified schema, "
                            "with no extra text or explanations."},

                {"role": "user", "content": base64_images},
                {"role": "user",
                 "content": "Extract invoice data and format as specified with all values as strings and dates in "
                            "YYYY-MM-DD format."},
                {"role": "user", "content": """
                {
                  "IRN": {"value": "string", "conf": 0.0},
                  "invoice_number": {"value": "string", "conf": 0.0},
                  "invoice_date": {"value": "YYYY-MM-DD", "conf": 0.0},
                  "invoice_header": {"value": "string", "conf": 0.0},
                  "po_number": {"value": "string", "conf": 0.0},
                  "po_date": {"value": "YYYY-MM-DD", "conf": 0.0},
                  "vendor_name": {"value": "string", "conf": 0.0},
                  "vendor_address": {"value": "string", "conf": 0.0},
                  "vendor_gst": {"value": "string", "conf": 0.0},
                  "vendor_pan": {"value": "string", "conf": 0.0},
                  "bill_to_name": {"value": "string", "conf": 0.0},
                  "billing_address": {"value": "string", "conf": 0.0},
                  "billing_gst": {"value": "string", "conf": 0.0},
                  "billing_pan": {"value": "string", "conf": 0.0},
                  "ship_to_address": {"value": "string", "conf": 0.0},
                  "total_invoice_amount": {"value": "string", "conf": 0.0},
                  "line_items": [
                    {
                      "item_description": {"value": "string", "conf": 0.0},
                      "hsn_sac_code": {"value": "string", "conf": 0.0},
                      "unit_of_measurement": {"value": "string", "conf": 0.0},
                      "quantity": {"value": "string", "conf": 0.0},
                      "base_amount": {"value": "string", "conf": 0.0},
                      "total_amount": {"value": "string", "conf": 0.0}
                    }
                  ],
                  "taxes": [
                    {
                      "category": {"value": "IGST", "conf": 1.0},
                      "rate": {"value": "string", "conf": 0.0},
                      "amount": {"value": "string", "conf": 0.0}
                    },
                    {
                      "category": {"value": "CGST", "conf": 1.0},
                      "rate": {"value": "string", "conf": 0.0},
                      "amount": {"value": "string", "conf": 0.0}
                    },
                    {
                      "category": {"value": "SGST", "conf": 1.0},
                      "rate": {"value": "string", "conf": 0.0},
                      "amount": {"value": "string", "conf": 0.0}
                    }
                  ],
                  "additional_data": []
                }
            """},

                {"role": "user", "content": "STRICT FORMATTING RULES:"},
                {"role": "user", "content": "1. ALL values must be strings (including numbers, amounts, quantities)"},
                {"role": "user", "content": "2. Dates MUST be in YYYY-MM-DD format"},
                {"role": "user", "content": "3. Empty fields should use empty string (\"\") not null or N/A"},
                {"role": "user",
                 "content": "4. Currency amounts should be strings without symbols (e.g. '2500.00' not '₹2,500')"},
                {"role": "user", "content": "5. Maintain the exact JSON structure with all fields present"},
                {"role": "user", "content": "6. For missing dates, use empty string (\"\") not 0000-00-00"},
                {"role": "user", "content": "7. For tax amounts/rates, use string formatted numbers ('18.00' not 18)"},
                {"role": "user",
                 "content": "8. Use confidence scores. They are not  binary values and are scaled between 0 and 1 "},


                {"role": "user",
                 "content": "9. Provide ONLY the raw JSON output with no additional text or explanations"},
                {"role": "user", "content": "10. For tax categories, keep the hardcoded values (IGST/CGST/SGST)"},
                {"role": "user",
                 "content": "11. Provide ONLY the raw JSON output with no additional text, explanations, "
                            "or formatting outside the JSON structure."},
                {"role": "user",
                 "content": " 12. Some of the text may be handwritten and there is a good chance that you may confose some letters with numbers. Make sure you are precise. Also these handwritten texts may be present in middle of typed out text so ensure that you read and understand everything before providing me with an output"},
                {"role": "user",
                 "content": " 13.  In [{key1:val1,key2:val2}], key is the heading while the value is the value for that heading .There is no restriction for the number of key values.But make sure that only important aspects are taken in the key value section wrt the invoice"},
                {"role": "user", "content": "14. the values shown in the above format have conf: 0.0. These are the defsult confidence scores which you update once you have generated the json output"},

            ],
            temperature=0,
            max_tokens=4000,

        )

        return response.choices[0]

    except Exception as e:
        print(f"Error in Vision-Language extraction: {e}")
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

        # Convert PDF to images
        images = pdf_pages_to_images(uploaded_file)
        if images:
            output = extract_data_with_vlm(api_key, images)
            if output:
                try:
                    json_data = json.loads(output.message.content)
                    json_data['filename'] = uploaded_file.filename  # Ensure filename is included
                    insertion_result = collection.insert_one(json_data)
                    results.append({uploaded_file.filename: {**json_data, '_id': str(insertion_result.inserted_id)}})
                except json.JSONDecodeError:
                    results.append({uploaded_file.filename: {'error': 'Error converting response to JSON'}})
            else:
                results.append({uploaded_file.filename: {'error': 'Could not extract data using VLM'}})
        else:
            results.append({uploaded_file.filename: {'error': 'Could not convert PDF pages to images'}})

    return jsonify(results)


@app.route('/list_invoices', methods=['GET'])
def list_invoices():
    try:
        filenames = [doc['filename'] for doc in collection.find({}, {'filename': 1, '_id': 0})]
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
    app.run(host='127.0.0.1', port=5000, debug=True)
