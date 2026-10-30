import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authService } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('truthlens_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('truthlens_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('truthlens_token');
      if (storedToken) {
        try {
          const profile = await authService.getMe();
          setUser(profile);
        } catch {
          authService.logout();
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };
    verifyUser();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authService.login({ email, password });
    setToken(res.access_token);
    const profile = await authService.getMe();
    setUser(profile);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    await authService.register({ email, password, full_name: fullName });
    await login(email, password);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
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

