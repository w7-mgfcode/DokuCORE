import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Button,
  Container,
  Divider,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
  CircularProgress,
  Chip,
  IconButton,
  AppBar,
  Toolbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Logout as LogoutIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Documents list page
 * Displays all documents with approval status
 */
const DocumentsList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { currentUser, logout, userRoles } = useAuth();

  // Check if user has create permissions
  const canCreate = userRoles && (userRoles.includes('editor') || userRoles.includes('admin'));

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/documents`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocuments(response.data);
      } catch (err) {
        setError('Error loading documents');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  // Render approval status chip
  const renderStatusChip = (status) => {
    switch (status) {
      case 'approved':
        return <Chip size="small" color="success" label="Approved" />;
      case 'rejected':
        return <Chip size="small" color="error" label="Rejected" />;
      case 'under_review':
        return <Chip size="small" color="warning" label="Under Review" />;
      default:
        return <Chip size="small" color="default" label="Draft" />;
    }
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            DokuCORE
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {currentUser && (
              <Typography variant="body2" sx={{ mr: 2 }}>
                {currentUser.username}
              </Typography>
            )}
            <IconButton color="inherit" onClick={logout} edge="end">
              <LogoutIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Documents
          </Typography>
          {canCreate && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              component={RouterLink}
              to="/documents/new"
            >
              New Document
            </Button>
          )}
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : documents.length === 0 ? (
          <Typography>No documents found</Typography>
        ) : (
          <Paper elevation={2}>
            <List>
              {documents.map((doc, index) => (
                <React.Fragment key={doc.id}>
                  {index > 0 && <Divider />}
                  <ListItem 
                    button 
                    component={RouterLink} 
                    to={`/documents/${doc.id}`}
                    sx={{ py: 2 }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="h6" component="span">
                            {doc.title}
                          </Typography>
                          <Box sx={{ ml: 2 }}>
                            {renderStatusChip(doc.approval_status)}
                          </Box>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Path: {doc.path}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Version: {doc.version}
                            {doc.approved_version && ` (Approved: ${doc.approved_version})`}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Paper>
        )}
      </Container>
    </Box>
  );
};

export default DocumentsList;