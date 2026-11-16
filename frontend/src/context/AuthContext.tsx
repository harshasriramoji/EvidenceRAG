import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'student' | 'admin';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<'student' | 'admin'>;
  register: (email: string, password: string, role?: string, adminCode?: string, fullName?: string) => Promise<'student' | 'admin'>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('evidencerag_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchUser = async () => {
      const storedToken = localStorage.getItem('evidencerag_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
        } catch {
          localStorage.removeItem('evidencerag_token');
          localStorage.removeItem('evidencerag_user');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    fetchUser();
  }, []);

  const login = async (email: string, password: string): Promise<'student' | 'admin'> => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user_id, full_name, role } = res.data;
    localStorage.setItem('evidencerag_token', access_token);
    setToken(access_token);
    const validRole = role === 'admin' ? 'admin' : 'student';
    setUser({ id: user_id, email, full_name, role: validRole });
    return validRole;
  };

  const register = async (
    email: string,
    password: string,
    role = 'student',
    adminCode?: string,
    fullName?: string
  ): Promise<'student' | 'admin'> => {
    const payload: Record<string, any> = {
      email,
      password,
      role
    };
    if (adminCode) payload.admin_code = adminCode;
    if (fullName) payload.full_name = fullName;

    const res = await api.post('/auth/register', payload);
    const { access_token, user_id, full_name: name, role: userRole } = res.data;
    localStorage.setItem('evidencerag_token', access_token);
    setToken(access_token);
    const validRole = userRole === 'admin' ? 'admin' : 'student';
    setUser({ id: user_id, email, full_name: name, role: validRole });
    return validRole;
  };

  const logout = () => {
    localStorage.removeItem('evidencerag_token');
    localStorage.removeItem('evidencerag_user');
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAdmin: user?.role === 'admin',
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
