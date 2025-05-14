import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Button,
  Container,
  Divider,
  Paper,
  Tab,
  Tabs,
  Typography,
  CircularProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import MarkdownDisplay from './MarkdownDisplay';
import DocumentVersioning from './DocumentVersioning';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Document details component
 * Displays document content and version history
 */
const DocumentDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentUser, userRoles } = useAuth();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  // Check if user has edit permissions
  const canEdit = userRoles && (userRoles.includes('editor') || userRoles.includes('admin'));

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/documents/${id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(response.data);
      } catch (err) {
        setError('Error loading document');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchDocument();
    }
  }, [id]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleEdit = () => {
    navigate(`/documents/${id}/edit`);
  };

  const handleBack = () => {
    navigate('/documents');
  };

  if (loading) {
    return (
      <Container sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Typography color="error">{error}</Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Documents
        </Button>
      </Container>
    );
  }

  if (!document) {
    return (
      <Container sx={{ mt: 4 }}>
        <Typography>Document not found</Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Documents
        </Button>
      </Container>
    );
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
            Back
          </Button>
        </Box>
        {canEdit && (
          <Button
            variant="contained"
            color="primary"
            startIcon={<EditIcon />}
            onClick={handleEdit}
            disabled={document.approval_status === 'under_review'}
          >
            Edit
          </Button>
        )}
      </Box>

      <Paper sx={{ mb: 4 }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {document.title}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            Path: {document.path}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last modified: {new Date(document.last_modified).toLocaleString()}
          </Typography>
        </Box>
      </Paper>

      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="document tabs">
            <Tab label="Content" id="document-tab-0" />
            <Tab label="Version History" id="document-tab-1" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <MarkdownDisplay content={document.content} />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <DocumentVersioning 
            documentId={parseInt(id)} 
            currentUser={currentUser}
            userRoles={userRoles}
          />
        </TabPanel>
      </Box>
    </Container>
  );
};

export default DocumentDetails;