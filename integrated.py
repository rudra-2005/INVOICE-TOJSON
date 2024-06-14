import fitz
from openai import OpenAI
import json
import os

def read_text_from_pdf(pdf_path):
    try:
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error in reading pdf: {e}")
        return None

def read_text_from_pdfs_in_folder(pdf_folder_path):
    pdf_texts = {}
    try:
        for filename in os.listdir(pdf_folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(pdf_folder_path, filename)
                text = read_text_from_pdf(pdf_path)
                if text:    
                    pdf_texts[filename] = text
                else:
                    print(f"Could not read text from PDF '{filename}'")
        return pdf_texts
    except Exception as e:
        print(f"Error in processing folder: {e}")
        return None

def chat_with_AI(api_key, text):
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

def convert_txt_to_json(json_text, json_folder, filename):
    try:
        json_data = json.loads(json_text)
        json_path = os.path.join(json_folder, filename)
        with open(json_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        print(f"Successfully converted to {json_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    try:
        api_key = "YOUR_API_KEY"
        pdf_folder_path =r"C:\Users\RUDRA\Desktop\INVOICE PROCESSING\invoices_in_pdf"
        json_folder_path =r"C:\Users\RUDRA\Desktop\INVOICE PROCESSING\invoices_in_json"
        
        pdf_texts = read_text_from_pdfs_in_folder(pdf_folder_path)
        
        for filename, pdf_text in pdf_texts.items():
            output = chat_with_AI(api_key, pdf_text)
            if output:
                json_filename = filename.replace('.pdf', '.json')
                convert_txt_to_json(output.message.content, json_folder_path, json_filename)
                
            else:
                print(f"Could not get response for PDF")
    except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()