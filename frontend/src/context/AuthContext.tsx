import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (firstName: string, lastName: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true); // Start with loading true
  const [error, setError] = useState<string | null>(null);

  // Check if token is valid on app start
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const response = await fetch('http://127.0.0.1:5000/verify-token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: storedToken }),
          });

          if (response.ok) {
            const data = await response.json();
            if (data.valid) {
              setUser(data.user);
              setToken(storedToken);
              console.log('Token verified successfully');
            } else {
              console.log('Token invalid, clearing auth state');
              localStorage.removeItem('token');
              setToken(null);
              setUser(null);
            }
          } else {
            console.log('Token verification failed with status:', response.status);
            // Don't clear token on server errors, just keep the current state
            setToken(storedToken);
          }
        } catch (err) {
          console.error('Token verification failed:', err);
          // On network errors, keep the token and don't log out
          // This prevents logout when backend is temporarily unavailable
          setToken(storedToken);
          console.log('Network error during token verification, keeping token');
        }
      } else {
        console.log('No token found in localStorage');
      }
      setIsLoading(false);
    };

    verifyToken();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setUser(data.user);
        setToken(data.token);
        localStorage.setItem('token', data.token);
        console.log('Login successful');
        return true;
      } else {
        setError(data.error || 'Login failed');
        return false;
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error. Please check your connection.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (firstName: string, lastName: string, email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5000/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ firstName, lastName, email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // After successful signup, automatically log in
        return await login(email, password);
      } else {
        setError(data.error || 'Signup failed');
        return false;
      }
    } catch (err) {
      console.error('Signup error:', err);
      setError('Network error. Please check your connection.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    console.log('Logout called');
    if (token) {
      try {
        // Call logout endpoint
        await fetch('http://127.0.0.1:5000/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }

    // Clear local state regardless of server response
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    console.log('Logout completed');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    signup,
    logout,
    isLoading,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 