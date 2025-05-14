import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  CircularProgress,
  Divider,
  Alert,
} from '@mui/material';
import {
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Document edit page
 * Allows editing document content
 */
const DocumentEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [document, setDocument] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/documents/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(response.data);
        setContent(response.data.content);
      } catch (err) {
        setError('Error loading document');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (id && id !== 'new') {
      fetchDocument();
    } else {
      setLoading(false);
    }
  }, [id]);

  const handleContentChange = (e) => {
    setContent(e.target.value);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      if (id && id !== 'new') {
        // Update existing document
        const response = await axios.put(
          `${API_BASE_URL}/documents/${id}`,
          {
            content: content,
            changed_by: currentUser.username
          },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        );
        setSuccess(true);
        setTimeout(() => {
          navigate(`/documents/${id}`);
        }, 1500);
      } else {
        // Create new document - this would require a form with more fields
        setError('Creating new documents is not implemented in this demo');
      }
    } catch (err) {
      setError('Error saving document: ' + (err.response?.data?.detail || err.message));
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (id && id !== 'new') {
      navigate(`/documents/${id}`);
    } else {
      navigate('/documents');
    }
  };

  if (loading) {
    return (
      <Container sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error && !document) {
    return (
      <Container sx={{ mt: 4 }}>
        <Typography color="error">{error}</Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back
        </Button>
      </Container>
    );
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
          Back
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={saving ? <CircularProgress size={24} /> : <SaveIcon />}
          onClick={handleSave}
          disabled={saving}
        >
          Save
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Document saved successfully! Redirecting...
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Editing: {document?.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Path: {document?.path}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Version: {document?.version}
        </Typography>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <TextField
          fullWidth
          multiline
          label="Document Content (Markdown)"
          value={content}
          onChange={handleContentChange}
          minRows={20}
          maxRows={40}
          variant="outlined"
          disabled={saving}
        />
      </Paper>
    </Container>
  );
};

export default DocumentEdit;