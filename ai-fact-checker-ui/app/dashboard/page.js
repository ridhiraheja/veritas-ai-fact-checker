"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { ShieldCheck, Send, Sparkles, ArrowLeft, ArrowRight, History, CheckCircle, XCircle, HelpCircle, LogOut, Trash2 } from "lucide-react";
import Link from "next/link";
import { useUser, UserButton, SignOutButton } from "@clerk/nextjs";

export default function Dashboard() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [backendStatus, setBackendStatus] = useState("checking"); // "checking", "online", "offline"
  const { isLoaded, user } = useUser();
  const chatRef = useRef(null);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:5000";

  // Check backend health
  const checkHealth = async () => {
    try {
      await axios.get(`${backendUrl}/health`);
      setBackendStatus("online");
    } catch (err) {
      setBackendStatus("offline");
    }
  };

  useEffect(() => {
    checkHealth();
    // Re-check every 10 seconds if offline
    const interval = setInterval(() => {
      if (backendStatus !== "online") checkHealth();
    }, 10000);
    return () => clearInterval(interval);
  }, [backendStatus]);

  // Auto scroll
  useEffect(() => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const fetchHistory = async () => {
    if (!isLoaded || !user) return;
    try {
      const email = user.primaryEmailAddress?.emailAddress || "anonymous";
      console.log("Fetching history from:", backendUrl);
      
      const res = await axios.get(`${backendUrl}/history?email=${encodeURIComponent(email)}`);
      if (Array.isArray(res.data)) {
        setHistory(res.data.reverse()); // latest first for sidebar
      }
    } catch (err) {
      console.error("Failed to fetch history");
    }
  };

  useEffect(() => {
    if (isLoaded && user) {
      fetchHistory();
    }
  }, [isLoaded, user]);

  const allSuggestions = [
    "Vaccines cause autism.",
    "The Earth is flat.",
    "Humans only use 10% of their brains.",
    "Albert Einstein failed math.",
    "Goldfish have a 3-second memory.",
    "The Great Wall of China is visible from space.",
    "Drinking 8 glasses of water a day is mandatory.",
    "Bulls are enraged by the color red.",
    "Napoleon was extremely short.",
    "Bananas grow on trees."
  ];

  const refreshSuggestions = () => {
    const shuffled = [...allSuggestions].sort(() => Math.random() - 0.5);
    setSuggestions(shuffled.slice(0, 4));
  };

  // Set random suggestions on mount
  useEffect(() => {
    refreshSuggestions();
  }, []);

  const startNewChat = () => {
    setMessages([]);
    refreshSuggestions();
  };

  const clearHistory = async () => {
    if (!confirm("Are you sure you want to clear your entire fact-check history?")) return;
    
    try {
      const email = user?.primaryEmailAddress?.emailAddress || "anonymous";
      await axios.post(`${backendUrl}/clear-history`, { email });
      setHistory([]);
    } catch (err) {
      alert("Failed to clear history");
    }
  };

  const sendMessage = async (overrideText, retryCount = 0) => {
    const textToSend = typeof overrideText === "string" ? overrideText : input;
    if (!textToSend.trim()) return;

    if (retryCount === 0) {
      const userMessage = { role: "user", text: textToSend };
      setMessages((prev) => [...prev, userMessage]);
      if (typeof overrideText !== "string") setInput("");
    }
    
    setLoading(true);

    try {
      const email = user?.primaryEmailAddress?.emailAddress || "anonymous";
      console.log("Sending fact-check to:", backendUrl);

      const res = await axios.post(`${backendUrl}/fact-check`, {
        statement: textToSend,
        email: email
      });

      const rawText = res.data.result || "";
      let errorMessage = res.data.error;

      const botMessage = {
        role: "bot",
        text: errorMessage ? `Error: ${errorMessage}` : rawText,
      };

      setMessages((prev) => [...prev, botMessage]);
      fetchHistory(); // Refresh history
      setBackendStatus("online");
    } catch (err) {
      const serverError = err.response?.data?.error;
      const isQuotaError = serverError?.toLowerCase().includes("quota") || err.response?.status === 429;

      // Silent retry for quota errors
      if (isQuotaError && retryCount < 1) {
        console.log("Quota hit, retrying in 3s...");
        setTimeout(() => sendMessage(textToSend, retryCount + 1), 3000);
        return;
      }

      let displayError = "Error connecting to server. Make sure the backend is running.";
      if (serverError) displayError = `Error: ${serverError}`;
      else if (err.message) displayError = `Network Error: ${err.message}`;

      setMessages((prev) => [
        ...prev,
        { role: "bot", text: displayError },
      ]);
      
      if (!err.response) setBackendStatus("offline");
    }

    setLoading(false);
  };

  // Calculate stats from history
  const stats = history.reduce(
    (acc, chat) => {
      const text = chat.response || "";
      if (text.includes("Verdict: True")) acc.trueCount++;
      else if (text.includes("Verdict: False")) acc.falseCount++;
      else if (text.includes("Verdict: Uncertain")) acc.uncertainCount++;
      return acc;
    },
    { trueCount: 0, falseCount: 0, uncertainCount: 0 }
  );

  return (
    <div className="h-screen flex vignette-bg font-sans overflow-hidden">
      
      {/* Sidebar */}
      <div className="w-80 bg-white/70 border-r border-[#E2E8F0] flex flex-col backdrop-blur-md hidden md:flex shrink-0 shadow-sm z-10">
        <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-[#1E3A8A] hover:text-[#0F172A] transition-colors">
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">Exit</span>
          </Link>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#3B82F6]" />
            <h1 className="font-serif text-xl font-semibold text-[#0F172A]">Veritas</h1>
          </div>
        </div>

        <div className="p-4 border-b border-[#E2E8F0]">
          <button 
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 bg-[#1E3A8A] text-white py-2.5 rounded-xl text-sm font-semibold hover:bg-[#0F172A] transition-all shadow-sm group"
          >
            <Sparkles className="w-4 h-4 text-blue-300 group-hover:rotate-12 transition-transform" />
            New Fact Check
          </button>
        </div>

        {/* Backend Status Indicator */}
        <div className="px-4 py-2 border-b border-[#E2E8F0]/50 flex items-center gap-2">
           <div className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-emerald-500 animate-pulse' : backendStatus === 'checking' ? 'bg-amber-400' : 'bg-rose-500'}`} />
           <span className="text-[10px] font-bold uppercase tracking-widest text-[#64748B]">
             System: {backendStatus === 'online' ? 'Connected' : backendStatus === 'checking' ? 'Connecting...' : 'Offline'}
           </span>
        </div>

        <div className="p-4 flex items-center justify-between text-[#475569] border-b border-[#E2E8F0]/50">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Fact-Check History</span>
          </div>
          {history.length > 0 && (
            <button 
              onClick={clearHistory}
              className="text-[#94A3B8] hover:text-rose-500 transition-colors p-1 rounded-md hover:bg-rose-50"
              title="Clear all history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <p className="text-sm text-[#94A3B8] text-center mt-4">No history yet.</p>
          ) : (
            history.map((item, idx) => (
              <div key={idx} className="p-3 bg-white rounded-xl shadow-sm border border-[#F1F5F9] hover:border-[#E2E8F0] transition-colors cursor-default">
                <div className="flex justify-between items-start mb-1">
                  <p className="text-sm text-[#0F172A] font-medium line-clamp-2">"{item.statement}"</p>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-1.5">
                    {item.response?.includes("Verdict: True") && <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3 h-3"/> True</span>}
                    {item.response?.includes("Verdict: False") && <span className="text-xs font-semibold text-rose-600 flex items-center gap-1"><XCircle className="w-3 h-3"/> False</span>}
                    {item.response?.includes("Verdict: Uncertain") && <span className="text-xs font-semibold text-amber-600 flex items-center gap-1"><HelpCircle className="w-3 h-3"/> Uncertain</span>}
                  </div>
                  {item.timestamp && (
                    <span className="text-[10px] text-[#94A3B8] font-medium">
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* User Profile Badge (Bottom Left) */}
        <div className="p-4 border-t border-[#E2E8F0] bg-white/50 mt-auto">
          {isLoaded && user ? (
            <div className="flex items-center justify-between group">
              <div className="flex items-center gap-3">
                <UserButton appearance={{ elements: { userButtonAvatarBox: "w-10 h-10 border border-[#E2E8F0]" } }} />
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-[#0F172A] leading-tight max-w-[120px] truncate">{user.fullName || "User"}</span>
                  <span className="text-xs text-[#64748B] truncate max-w-[120px]">{user.primaryEmailAddress?.emailAddress || ""}</span>
                </div>
              </div>
              <SignOutButton>
                <button className="text-[#64748B] hover:text-rose-600 transition-colors p-2 rounded-lg hover:bg-rose-50">
                  <LogOut className="w-4 h-4" />
                </button>
              </SignOutButton>
            </div>
          ) : (
            <Link href="/" className="flex items-center justify-center w-full py-2 text-sm font-medium text-[#1E3A8A] bg-[#DBEAFE]/50 hover:bg-[#DBEAFE] rounded-xl transition-colors">
              Log in
            </Link>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-white/30 relative">
        
        {/* Stats Header */}
        <div className="h-16 border-b border-[#E2E8F0] bg-white/50 backdrop-blur-sm flex items-center justify-center gap-6 px-4 shadow-sm">
          <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-100">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-semibold text-emerald-700">True: {stats.trueCount}</span>
          </div>
          <div className="flex items-center gap-2 bg-rose-50 px-3 py-1.5 rounded-full border border-rose-100">
            <XCircle className="w-4 h-4 text-rose-600" />
            <span className="text-sm font-semibold text-rose-700">False: {stats.falseCount}</span>
          </div>
          <div className="flex items-center gap-2 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-100">
            <HelpCircle className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-semibold text-amber-700">Uncertain: {stats.uncertainCount}</span>
          </div>
        </div>

        {/* Chat window */}
        <div
          ref={chatRef}
          className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6"
        >
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
              <div className="opacity-70 space-y-4 flex flex-col items-center">
                <Sparkles className="w-12 h-12 text-[#3B82F6]" />
                <p className="text-lg text-[#0F172A]">What would you like to verify today?</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl mt-8">
                {suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(suggestion)}
                    className="p-4 bg-white/60 border border-[#E2E8F0] rounded-xl text-sm text-[#475569] hover:bg-white hover:shadow-md hover:-translate-y-0.5 hover:border-[#3B82F6]/50 transition-all text-left flex items-center justify-between group"
                  >
                    <span>{suggestion}</span>
                    <ArrowRight className="w-4 h-4 text-[#94A3B8] group-hover:text-[#3B82F6] transition-colors opacity-0 group-hover:opacity-100" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 15, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] md:max-w-[75%] p-5 rounded-[2rem] whitespace-pre-wrap text-[15px] leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-[#DBEAFE] text-[#0F172A] rounded-br-md"
                      : "bg-white text-[#1E3A8A] rounded-bl-md border border-[#F1F5F9]"
                  }`}
                >
                  {msg.text}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-[#3B82F6] p-2"
            >
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-sm font-medium ml-2">Analyzing</span>
            </motion.div>
          )}

          {backendStatus === 'offline' && !loading && (
            <div className="flex justify-center mt-4">
              <div className="bg-rose-50 text-rose-600 px-4 py-2 rounded-full text-xs font-bold border border-rose-100 shadow-sm animate-pulse">
                Backend is currently offline. Please start the server.
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 md:p-6 w-full max-w-4xl mx-auto">
          <div className="relative flex items-center bg-white shadow-[0_8px_30px_rgb(0,0,0,0.06)] rounded-full p-2 border border-[#E2E8F0]">
            <input
              className="flex-1 px-6 py-3 bg-transparent outline-none text-[#0F172A] placeholder:text-[#94A3B8]"
              placeholder={backendStatus === 'online' ? "Enter a statement to verify..." : "Waiting for engine..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={backendStatus !== 'online'}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || backendStatus !== 'online'}
              className="bg-[#1E3A8A] text-white p-3 rounded-full hover:bg-[#0F172A] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mr-1"
            >
              <Send className="w-5 h-5 ml-1" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
