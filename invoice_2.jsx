import React, { useState } from 'react';
import axios from 'axios';

function FileUploader() {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [output, setOutput] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleFileChange = (event) => {
        setSelectedFiles(event.target.files);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            alert("Please select a file first!");
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < selectedFiles.length; i++) {
            formData.append("files", selectedFiles[i]);
        }

        try {
            setLoading(true);
            const response = await axios.post("http://127.0.0.1:5000/extract_invoice_json", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });

            setOutput(response.data);
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while uploading the file.");
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = (json) => {
        navigator.clipboard.writeText(JSON.stringify(json, null, 3)).then(() => {
            alert("JSON copied to clipboard!");
        })
    };

    return (
        <div>
            <div className='header'>
                <h1>INVOICE PROCESSING</h1>
            </div>
            <div className='header2'>
                <h3>This application will convert uploaded PDF to JSON files</h3>
            </div>
            <div className='loading'>
                {loading && <p>Loading... Please wait while your files are being processed</p>}
            </div>
            <div className='filehandler'>
                <input type="file" onChange={handleFileChange} accept="application/pdf" multiple />
                <button onClick={handleUpload}>Upload and Process</button>
            </div>
            <div>
                {output.length > 0 && output.map((result, index) => (
                    <div key={index} className='main'>
                        <h4 className='pdf_name'>{Object.keys(result)[0]}</h4>
                        <pre>{JSON.stringify(result, null, 3)}</pre>
                        <button onClick={() => handleCopy(result)} className='copy'>Copy JSON</button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default FileUploader;
