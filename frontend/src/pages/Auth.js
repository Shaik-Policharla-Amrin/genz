import React, { useState } from "react";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Auth = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "", name: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? `${API}/auth/login` : `${API}/auth/register`;
      const payload = isLogin ? { email: formData.email, password: formData.password } : formData;
      const response = await axios.post(endpoint, payload);
      
      toast.success(isLogin ? "Welcome back!" : "Account created!");
      onLogin(response.data.token);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: '#FAFAFA' }}>
      <div className="w-full max-w-md neo-card p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-black tracking-tighter" style={{ fontFamily: 'Work Sans, sans-serif' }}>
            GenZ AI
          </h1>
          <p className="text-base text-[#4B5563] mt-2">Multi-Agent Productivity System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-bold mb-2" style={{ fontFamily: 'Work Sans, sans-serif' }}>NAME</label>
              <input
                type="text"
                data-testid="auth-name-input"
                className="neo-input w-full px-4 py-3"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required={!isLogin}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-bold mb-2" style={{ fontFamily: 'Work Sans, sans-serif' }}>EMAIL</label>
            <input
              type="email"
              data-testid="auth-email-input"
              className="neo-input w-full px-4 py-3"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-bold mb-2" style={{ fontFamily: 'Work Sans, sans-serif' }}>PASSWORD</label>
            <input
              type="password"
              data-testid="auth-password-input"
              className="neo-input w-full px-4 py-3"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>

          <button
            type="submit"
            data-testid="auth-submit-button"
            className="neo-button-primary w-full py-3 text-lg"
            disabled={loading}
          >
            {loading ? "..." : isLogin ? "LOGIN" : "REGISTER"}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            onClick={() => setIsLogin(!isLogin)}
            data-testid="auth-toggle-button"
            className="text-sm font-medium underline"
          >
            {isLogin ? "Need an account? Register" : "Have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;