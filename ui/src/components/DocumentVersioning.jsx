import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  TextField,
  Typography,
  Chip,
} from '@mui/material';
import { 
  Restore as RestoreIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  History as HistoryIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { formatDistance } from 'date-fns';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Document versioning component
 * Displays version history and allows restoring previous versions
 */
const DocumentVersioning = ({ documentId, currentUser, userRoles }) => {
  const [versions, setVersions] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [approvalComments, setApprovalComments] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [document, setDocument] = useState(null);

  // Check if user has approval permissions
  const canApprove = userRoles && userRoles.includes('approver');
  
  // Load document data
  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(response.data);
      } catch (err) {
        setError('Error loading document details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchDocument();
    }
  }, [documentId]);

  // Load version history
  useEffect(() => {
    const fetchVersions = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/versions/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setVersions(response.data);
      } catch (err) {
        setError('Error loading version history');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchVersions();
    }
  }, [documentId]);

  // Load approval requests for this document
  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/versions/approvals?status=pending`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        // Filter approvals for this document
        const documentApprovals = response.data.filter(
          approval => approval.document_id === documentId
        );
        setApprovals(documentApprovals);
      } catch (err) {
        setError('Error loading approval requests');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchApprovals();
    }
  }, [documentId]);

  // Handle version restore
  const handleRestore = async () => {
    if (!selectedVersion) return;
    
    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/versions/documents/${documentId}/restore/${selectedVersion.version}`,
        {},
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      if (response.data.status === 'success') {
        // Refresh version history after restore
        const versionsResponse = await axios.get(`${API_BASE_URL}/versions/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setVersions(versionsResponse.data);
        
        // Refresh document data
        const documentResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(documentResponse.data);
      }
    } catch (err) {
      setError('Error restoring version');
      console.error(err);
    } finally {
      setLoading(false);
      setDialogOpen(false);
    }
  };

  // Handle approval request creation
  const handleRequestApproval = async () => {
    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/versions/approvals`,
        {
          document_id: documentId,
          version: document.version,
          comments: approvalComments
        },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      if (response.data.status === 'success') {
        // Refresh document data
        const documentResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(documentResponse.data);
        
        // Refresh approvals
        const approvalsResponse = await axios.get(`${API_BASE_URL}/versions/approvals?status=pending`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        const documentApprovals = approvalsResponse.data.filter(
          approval => approval.document_id === documentId
        );
        setApprovals(documentApprovals);
      }
    } catch (err) {
      setError('Error requesting approval');
      console.error(err);
    } finally {
      setLoading(false);
      setApprovalDialogOpen(false);
      setApprovalComments('');
    }
  };

  // Handle approval decision
  const handleApprovalDecision = async (approvalId, status) => {
    try {
      setLoading(true);
      const response = await axios.put(
        `${API_BASE_URL}/versions/approvals/${approvalId}`,
        {
          status: status, // 'approved' or 'rejected'
          comments: `${status} by ${currentUser.username}`
        },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      if (response.data.status === 'success') {
        // Refresh document data
        const documentResponse = await axios.get(`${API_BASE_URL}/documents/${documentId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setDocument(documentResponse.data);
        
        // Refresh approvals
        const approvalsResponse = await axios.get(`${API_BASE_URL}/versions/approvals?status=pending`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        const documentApprovals = approvalsResponse.data.filter(
          approval => approval.document_id === documentId
        );
        setApprovals(documentApprovals);
      }
    } catch (err) {
      setError(`Error ${status === 'approved' ? 'approving' : 'rejecting'} document`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Get approval status chip
  const getApprovalStatusChip = (status) => {
    switch (status) {
      case 'approved':
        return <Chip color="success" label="Approved" icon={<CheckCircle />} />;
      case 'rejected':
        return <Chip color="error" label="Rejected" icon={<Cancel />} />;
      case 'under_review':
        return <Chip color="warning" label="Under Review" icon={<History />} />;
      default:
        return <Chip color="default" label="Draft" />;
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {document && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" component="div">
              Document Status
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {getApprovalStatusChip(document.approval_status)}
              <Typography variant="body2" sx={{ ml: 2 }}>
                Current Version: {document.version}
                {document.approved_version && (
                  <span> (Approved Version: {document.approved_version})</span>
                )}
              </Typography>
            </Box>

            {document.approval_status !== 'under_review' && (
              <Button
                variant="outlined"
                startIcon={<SendIcon />}
                sx={{ mt: 2 }}
                onClick={() => setApprovalDialogOpen(true)}
                disabled={loading}
              >
                Request Approval
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pending approvals section */}
      {approvals.length > 0 && canApprove && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Pending Approval Requests
          </Typography>
          <List>
            {approvals.map((approval) => (
              <ListItem key={approval.id} divider>
                <ListItemText
                  primary={`Version ${approval.version} - Requested by ${approval.requested_by}`}
                  secondary={`Requested ${formatDistance(new Date(approval.requested_at), new Date(), { addSuffix: true })}`}
                />
                <Box>
                  <IconButton 
                    color="success" 
                    onClick={() => handleApprovalDecision(approval.id, 'approved')}
                    disabled={loading}
                  >
                    <ApproveIcon />
                  </IconButton>
                  <IconButton 
                    color="error" 
                    onClick={() => handleApprovalDecision(approval.id, 'rejected')}
                    disabled={loading}
                  >
                    <RejectIcon />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      <Typography variant="h6" gutterBottom>
        Version History
      </Typography>

      {loading && <Typography>Loading...</Typography>}

      {versions.length === 0 && !loading ? (
        <Typography>No version history available</Typography>
      ) : (
        <List>
          {versions.map((version) => (
            <ListItem key={version.id} divider>
              <ListItemText
                primary={`Version ${version.version}`}
                secondary={`Modified by ${version.changed_by} on ${new Date(version.changed_at).toLocaleString()}`}
              />
              <IconButton 
                onClick={() => {
                  setSelectedVersion(version);
                  setDialogOpen(true);
                }}
                disabled={loading}
              >
                <RestoreIcon />
              </IconButton>
            </ListItem>
          ))}
        </List>
      )}

      {/* Restore version dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Restore Version</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to restore version {selectedVersion?.version}? This will create a new version with the content from version {selectedVersion?.version}.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleRestore} disabled={loading} variant="contained" color="primary">
            Restore
          </Button>
        </DialogActions>
      </Dialog>

      {/* Request approval dialog */}
      <Dialog open={approvalDialogOpen} onClose={() => setApprovalDialogOpen(false)}>
        <DialogTitle>Request Approval</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Request approval for the current version of this document (version {document?.version}).
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="comments"
            label="Comments (optional)"
            type="text"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={approvalComments}
            onChange={(e) => setApprovalComments(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialogOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleRequestApproval} disabled={loading} variant="contained" color="primary">
            Request Approval
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentVersioning;