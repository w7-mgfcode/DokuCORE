import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [userRoles, setUserRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Check if user is authenticated on initial load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await axios.get(`${API_BASE_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setCurrentUser(response.data);
          // Extract roles from JWT token scopes
          const tokenData = parseJwt(token);
          if (tokenData && tokenData.scopes) {
            const roles = extractRolesFromScopes(tokenData.scopes);
            setUserRoles(roles);
          }
        } catch (err) {
          console.error('Auth check failed:', err);
          localStorage.removeItem('token');
          setCurrentUser(null);
          setUserRoles([]);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post(`${API_BASE_URL}/auth/token`, formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      // Get user details
      const userResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      setCurrentUser(userResponse.data);
      
      // Extract roles from JWT token scopes
      const tokenData = parseJwt(access_token);
      if (tokenData && tokenData.scopes) {
        const roles = extractRolesFromScopes(tokenData.scopes);
        setUserRoles(roles);
      }
      
      navigate('/'); // Redirect to home page after login
      return true;
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
    setUserRoles([]);
    navigate('/login');
  };

  const parseJwt = (token) => {
    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
      return null;
    }
  };

  const extractRolesFromScopes = (scopes) => {
    if (!scopes || !Array.isArray(scopes)) return [];
    
    const roles = new Set();
    
    // Extract roles from scope patterns
    scopes.forEach(scope => {
      if (scope === 'documents:approve') {
        roles.add('approver');
      }
      if (scope === 'documents:write') {
        roles.add('editor');
      }
      if (scope === 'admin') {
        roles.add('admin');
      }
    });
    
    return Array.from(roles);
  };

  const value = {
    currentUser,
    userRoles,
    loading,
    error,
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;