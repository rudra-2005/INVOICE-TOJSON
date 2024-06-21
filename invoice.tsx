import React, { useState, useCallback, ChangeEvent } from 'react';
import axios from 'axios';

interface Output {
    [key: string]: any;
}

const FileUploader: React.FC = () => {
    const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
    const [output, setOutput] = useState<Output[]>([]);
    const [loading, setLoading] = useState<boolean>(false);


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

            setOutput(response.data);
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

    return (
        <div>
            <div className='header'>
                <h1>INVOICE PROCESSING</h1>
            </div>
            <div className='header2'>
                <h3>This application will convert uploaded PDFs to JSON files</h3>
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
};

export default FileUploader;
