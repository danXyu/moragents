import {
  useEffect,
  createContext,
  useContext,
  ReactNode,
  useState,
} from "react";
import { useAccount, useSignMessage } from "wagmi";
import axios from "axios";

// Types
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: number | null;
  authToken: string | null;
  authenticate: () => Promise<void>;
  logout: () => Promise<void>;
  apiClient: () => any;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const { address, isConnected } = useAccount();
  const { signMessageAsync } = useSignMessage();

  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Check if token exists on mount
  useEffect(() => {
    const token = localStorage.getItem("authToken");
    const storedUserId = localStorage.getItem("userId");

    if (token && storedUserId && isConnected) {
      setAuthToken(token);
      setUserId(parseInt(storedUserId));
      setIsAuthenticated(true);
    }
  }, [isConnected]);

  // Handle wallet disconnection
  useEffect(() => {
    if (!isConnected && isAuthenticated) {
      // User disconnected wallet, log them out
      logout();
    }
  }, [isConnected]);

  const authenticate = async () => {
    if (!address || !isConnected) return;

    try {
      setIsLoading(true);

      // 1. Request challenge from server
      const challengeResponse = await axios.post("/api/auth/challenge", {
        wallet_address: address,
      });

      const challenge = challengeResponse.data.challenge;

      // 2. Sign the challenge with user's wallet
      const signature = await signMessageAsync({
        message: challenge,
      });

      // 3. Verify signature on the server
      const verifyResponse = await axios.post("/api/auth/verify", {
        wallet_address: address,
        signature,
      });

      // 4. Store authentication data
      const { access_token, user_id } = verifyResponse.data;
      localStorage.setItem("authToken", access_token);
      localStorage.setItem("userId", user_id.toString());

      setAuthToken(access_token);
      setUserId(user_id);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Authentication error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (authToken) {
        // Call logout endpoint to invalidate token on server
        await axios.post(
          "/api/auth/logout",
          {},
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          }
        );
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local storage and state regardless of server response
      localStorage.removeItem("authToken");
      localStorage.removeItem("userId");
      setAuthToken(null);
      setUserId(null);
      setIsAuthenticated(false);
    }
  };

  // Create authenticated API client
  const apiClient = () => {
    return axios.create({
      headers: authToken
        ? {
            Authorization: `Bearer ${authToken}`,
          }
        : {},
    });
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        userId,
        authToken,
        authenticate,
        logout,
        apiClient,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
