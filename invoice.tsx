import React, { useState, useEffect, useCallback, ChangeEvent } from 'react';
import axios from 'axios';

interface Output {
    [key: string]: any;
}

const FileUploader: React.FC = () => {
    const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
    const [currentOutput, setCurrentOutput] = useState<Output | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [invoices, setInvoices] = useState<string[]>([]);
    const [selectedInvoice, setSelectedInvoice] = useState<string>("");

    useEffect(() => {
        fetchInvoices();
    }, []);

    const fetchInvoices = async () => {
        try {
            const response = await axios.get<{ invoices: string[] }>(
                "http://127.0.0.1:5000/list_invoices"
            );
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
        }

        try {
            setLoading(true);

            const response = await axios.post<Output[]>(
                "http://127.0.0.1:5000/extract_invoice_json",
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    }
                }
            );

            const newOutputs = response.data;
            if (newOutputs.length > 0) {
                setCurrentOutput(newOutputs[0]);
            }
            fetchInvoices();
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while uploading the file.");
        } finally {
            setLoading(false);
        }
    }, [selectedFiles]);

    const handleCopy = useCallback((json: Output): void => {
        navigator.clipboard.writeText(JSON.stringify(json, null, 3)).then(() => {
            alert("JSON copied to clipboard!");
        });
    }, []);

    const handleInvoiceChange = useCallback((event: ChangeEvent<HTMLSelectElement>): void => {
        const selectedFilename = event.target.value;
        setSelectedInvoice(selectedFilename);
        fetchInvoiceData(selectedFilename);
    }, []);

    const fetchInvoiceData = async (filename: string) => {
        try {
            const response = await axios.get<Output>(
                `http://127.0.0.1:5000/get_invoice_json?filename=${filename}`
            );
            setCurrentOutput(response.data);
        } catch (error) {
            console.error("Error fetching invoice data:", error);
            setCurrentOutput(null);
        }
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
                    <h3>Select an Invoice</h3>
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
                    
                    

                    <div>
                        {currentOutput && (
                            <div className='main'>
                                <h4 className='pdf_name'>{selectedInvoice || "Recently Converted"}</h4>
                                <pre>{JSON.stringify(currentOutput, null, 3)}</pre>
                                <button onClick={() => handleCopy(currentOutput)} className='copy'>Copy JSON</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FileUploader;
