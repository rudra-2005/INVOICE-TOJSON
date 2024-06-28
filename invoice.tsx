import React, { useState, useEffect, useCallback, ChangeEvent } from 'react';
import axios from 'axios';

interface Output {
  [key: string]: any;
}

const FileUploader: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [output, setOutput] = useState<Output[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [invoices, setInvoices] = useState<string[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<string>("");
  const [invoiceData, setInvoiceData] = useState<Output | null>(null);
  const [showUploadedFiles, setShowUploadedFiles] = useState<boolean>(false);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await axios.get<{ invoices: string[] }>("http://127.0.0.1:5000/list_invoices");
      setInvoices(response.data.invoices);
    } catch (error) {
      console.error("Error fetching invoices:", error);
    }
  };

  const handleFileChange = useCallback((event: ChangeEvent<HTMLInputElement>): void => {
    setSelectedFiles(event.target.files);
  }, []);

  const handleUpload = useCallback(async (): Promise<void> => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append("files", selectedFiles[i]);
      formData.append("filename", selectedFiles[i].name);
    }

    try {
      setLoading(true);
      setInvoiceData(null);

      const response = await axios.post<Output[]>("http://127.0.0.1:5000/extract_invoice_json", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setOutput(response.data);
      setShowUploadedFiles(true);
      setSelectedInvoice("");
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while uploading the file.");
    } finally {
      setLoading(false);
      fetchInvoices();
    }
  }, [selectedFiles, fetchInvoices]);

  const handleSubmit = useCallback(async (json: Output): Promise<void> => {
    if (!json || !json.filename) {
      alert("Invalid data. Filename is required.");
      return;
    }

    try {
      const response = await axios.put("http://127.0.0.1:5000/update_invoice", json, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        alert("Invoice updated successfully!");
        fetchInvoices();  // Refresh the invoice list
      } else {
        alert(response.data.error || "Failed to update invoice.");
      }
    } catch (error) {
      console.error("Error updating invoice:", error);
      alert("An error occurred while updating the invoice.");
    }
  }, [fetchInvoices]);

  const handleInvoiceChange = useCallback((event: ChangeEvent<HTMLSelectElement>): void => {
    const selectedFilename = event.target.value;

    setSelectedInvoice(selectedFilename);
    fetchInvoiceData(selectedFilename);
    setShowUploadedFiles(false);
    setOutput([]);
  }, []);

  const fetchInvoiceData = async (filename: string) => {
    try {
      const response = await axios.get<Output>(`http://127.0.0.1:5000/get_invoice_json?filename=${filename}`);
      if (response.data) {
        setInvoiceData({ ...response.data, filename });  // Ensure filename is part of the invoice data
      }
    } catch (error) {
      console.error("Error fetching invoice data:", error);
      setInvoiceData(null);
    }
  };

  const renderFormFields = (data: Output, onChange: (newValue: any, key: string) => void) => {
    return Object.keys(data).map((key, index) => {
      if (key === "_id" || key === "filename") return null;

      const value = data[key];

      if (key === "invoiceDetails") {
        // Render invoice details as nested form
        return (
          <div key={index} className='form-group'>
            <label>{key}</label>
            <div className='nested-form'>
              {Object.keys(value).map((subKey, subIndex) => (
                <div key={subIndex} className='form-group'>
                  <label>{subKey}</label>
                  <input
                    className='form-control'
                    type='text'
                    value={value[subKey] ?? ''}
                    onChange={(e) => onChange(e.target.value, `${key}.${subKey}`)}
                  />
                </div>
              ))}
            </div>
          </div>
        );
      }
      else if (key === "taxDetails") {
        // Render invoice details as nested form
        return (
          <div key={index} className='form-group'>
            <label>{key}</label>
            <div className='nested-form'>
              {Object.keys(value).map((subKey, subIndex) => (
                <div key={subIndex} className='form-group'>
                  <label>{subKey}</label>
                  <input
                    className='form-control'
                    type='text'
                    value={value[subKey] ?? ''}
                    onChange={(e) => onChange(e.target.value, `${key}.${subKey}`)}
                  />
                </div>
              ))}
            </div>
          </div>
        );
       }
        else if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          return (
            <div key={index} className='form-group'>
              <label>{key}</label>
              {value.map((item: any, idx: number) => (
                <div key={idx} className='nested-form'>
                  {renderFormFields(item, (newValue: any, nestedKey: string) => onChange(newValue, `${key}.${idx}.${nestedKey}`))}
                </div>
              ))}
            </div>
          );
        } else {
          return (
            <div key={index} className='form-group'>
              <label>{key}</label>
              {renderFormFields(value, (newValue: any, nestedKey: string) => onChange(newValue, `${key}.${nestedKey}`))}
            </div>
          );
        }
      } else {
        return (
          <div key={index} className='form-group'>
            <label>{key}</label>
            <input
              className='form-control'
              type='text'
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value, key)}
            />
          </div>
        );
      }
    });
  };

  return (
    <div>
      <div className='header'>
        <h1>INVOICE PROCESSOR</h1>
      </div>
      <div className='header2'>
        <h3>Convert your PDF invoices into JSON format</h3>
      </div>
      <div className='loading'>
        {loading && <p>Loading... Please wait while your files are being processed.</p>}
      </div>
      <div className='filehandler'>
        <input
          type="file"
          onChange={handleFileChange}
          accept="application/pdf"
          multiple
          className='a1'
        />
        <button onClick={handleUpload} className='a2'>Upload and Process</button>
      </div>

      <div className='mainbox'>
        <div className='invoice-list'>
          <h3>List of Invoices</h3>
          <select
            className='select'
            id="invoiceDropdown"
            value={selectedInvoice}
            onChange={handleInvoiceChange}
          >
            <option value="">Choose an invoice...</option>
            {invoices.map((filename, index) => (
              <option key={index} value={filename}>{filename}</option>
            ))}
          </select>
        </div>

        <div className='no-list-box'>
          {!showUploadedFiles && invoiceData && (
            <div className='main'>
              <h4 className='pdf_name'>{selectedInvoice}</h4>
              <form className='form2'>
                {renderFormFields(invoiceData, (newValue, key) => {
                  const updatedData = { ...invoiceData };
                  const keys = key.split('.');
                  let current = updatedData;
                  for (let i = 0; i < keys.length - 1; i++) {
                    current = current[keys[i]];
                  }
                  current[keys[keys.length - 1]] = newValue;
                  setInvoiceData(updatedData);
                })}
                <button type='button' onClick={() => handleSubmit(invoiceData)} className='submit'>Submit</button>
              </form>
            </div>
          )}

          {showUploadedFiles && output.map((result, index) => (
            <div key={index} className='main'>
              
              <form className='form1'>
                {renderFormFields(result, (newValue, key) => {
                  const updatedResult = { ...result };
                  const keys = key.split('.');
                  let current = updatedResult;
                  for (let i = 0; i < keys.length - 1; i++) {
                    current = current[keys[i]];
                  }
                  current[keys[keys.length - 1]] = newValue;
                  setOutput(prevOutput => {
                    const newOutput = [...prevOutput];
                    newOutput[index] = updatedResult;
                    return newOutput;
                  });
                })}
               
              </form>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FileUploader;
