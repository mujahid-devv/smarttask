import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Login failed");
      localStorage.setItem("token", data.token);
      navigate("/home");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
<div className="min-h-screen flex items-center justify-center bg-zinc-50 px-4 font-sans">
  <div className="bg-white p-10 rounded-none shadow-[0_10px_40px_-15px_rgba(0,0,0,0.1)] w-full max-w-sm border border-zinc-100">

    <header className="mb-10 text-center">
      <h2 className="text-3xl font-black uppercase tracking-tighter text-zinc-900">
        Login
      </h2>
      <p className="text-zinc-400 text-xs mt-2 uppercase tracking-widest">
        Enter your credentials
      </p>
    </header>

    {error && (
      <div className="bg-zinc-900 text-white text-[10px] uppercase tracking-widest py-2 px-4 mb-6 text-center">
        {error}
      </div>
    )}

    <div className="space-y-6">
      <div>
        <label className="block text-[10px] uppercase font-bold tracking-widest text-zinc-500 mb-2">
          Email Address
        </label>
        <input
          type="email"
          name="email"
          value={form.email}
          onChange={handleChange}
          placeholder="name@domain.com"
          className="w-full bg-zinc-50 border-b border-zinc-200 px-0 py-3 text-sm focus:outline-none focus:border-black transition-colors duration-300 placeholder:text-zinc-300"
        />
      </div>

      <div>
        <label className="block text-[10px] uppercase font-bold tracking-widest text-zinc-500 mb-2">
          Password
        </label>
        <input
          type="password"
          name="password"
          value={form.password}
          onChange={handleChange}
          placeholder="••••••••"
          className="w-full bg-zinc-50 border-b border-zinc-200 px-0 py-3 text-sm focus:outline-none focus:border-black transition-colors duration-300 placeholder:text-zinc-300"
        />
      </div>
    </div>

    <div className="mt-10 space-y-3">
      <button
        onClick={handleLogin}
        disabled={loading}
        className="w-full bg-zinc-900 text-white py-4 text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98] disabled:opacity-50"
      >
        {loading ? "Authenticating..." : "Sign In"}
      </button>

      <button
        onClick={() => navigate("/register")}
        className="w-full bg-transparent text-zinc-900 py-4 text-xs font-bold uppercase tracking-widest border border-zinc-200 hover:border-zinc-900 transition-all active:scale-[0.98]"
      >
        Create Account
      </button>
    </div>

    <footer className="mt-8 text-center">
      <button className="text-[10px] text-zinc-400 uppercase tracking-widest hover:text-black transition-colors">
        Forgot password?
      </button>
    </footer>
  </div>
</div>
  );
}
