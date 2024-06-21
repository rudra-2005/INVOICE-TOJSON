import React from 'react'
import ReactDOM from 'react-dom/client'

import './invoice.css'
import FileUploader from './invoice'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
  <FileUploader/>
  </React.StrictMode>,
)
