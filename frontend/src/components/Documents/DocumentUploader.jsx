import React, { useState } from "react";
import { Box, Button, TextField, CircularProgress, Typography, Alert, List, ListItem, ListItemText } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import axios from "axios";

export default function DocumentUploader({ buildingId }) {
  const [files, setFiles] = useState([]);
  const [docType, setDocType] = useState("generic");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setFiles([...files, ...e.dataTransfer.files]);
  };

  const handleFileChange = (e) => {
    setFiles([...files, ...e.target.files]);
  };

  const handleUpload = async () => {
    if (!files.length) return;

    setLoading(true);
    setProgress(0);
    setMessage("");

    for (let file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("building_id", buildingId);
      formData.append("document_type", docType);

      try {
        await axios.post("/api/documents/upload", formData, {
          onUploadProgress: (progressEvent) => {
            setProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
          },
        });
        setMessage(`✓ ${file.name} caricato con successo`);
      } catch (error) {
        setMessage(`✗ Errore caricamento ${file.name}`);
      }
    }

    setLoading(false);
    setFiles([]);
  };

  return (
    <Box
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      sx={{
        border: "2px dashed #ccc",
        borderRadius: 2,
        p: 3,
        textAlign: "center",
        cursor: "pointer",
        backgroundColor: "#f5f5f5",
      }}
    >
      <CloudUploadIcon sx={{ fontSize: 48, mb: 2, color: "#1976d2" }} />
      <Typography variant="h6">Trascina documenti qui o clicca</Typography>
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: "none" }}
        id="file-input"
      />
      <label htmlFor="file-input" style={{ cursor: "pointer" }}>
        <Button variant="contained" component="span" sx={{ mt: 2 }}>
          Seleziona File
        </Button>
      </label>

      {files.length > 0 && (
        <>
          <List>
            {Array.from(files).map((f, i) => (
              <ListItem key={i}>
                <ListItemText primary={f.name} secondary={`${(f.size / 1024).toFixed(2)} KB`} />
              </ListItem>
            ))}
          </List>

          <TextField
            select
            label="Tipo Documento"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            sx={{ mt: 2, mr: 2 }}
            SelectProps={{
              native: true,
            }}
          >
            <option value="generic">Generico</option>
            <option value="plan">Piano</option>
            <option value="permit">Permesso</option>
            <option value="inspection">Ispezione</option>
          </TextField>

          <Button
            variant="contained"
            color="primary"
            onClick={handleUpload}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : "Carica"}
          </Button>

          {loading && <LinearProgress variant="determinate" value={progress} sx={{ mt: 2 }} />}
          {message && <Alert sx={{ mt: 2 }}>{message}</Alert>}
        </>
      )}
    </Box>
  );
}
