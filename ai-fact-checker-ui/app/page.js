"use client";

import { motion } from "framer-motion";
import { SignIn, useAuth } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { useTheme } from "next-themes";
import Link from "next/link";
import { ShieldCheck, Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function LandingPage() {
  const { isLoaded, isSignedIn } = useAuth();
  const { theme, systemTheme } = useTheme();
  
  const currentTheme = theme === "system" ? systemTheme : theme;

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -30 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { type: "spring", stiffness: 100, damping: 20 },
    },
  };

  return (
    <div className="min-h-screen flex font-sans bg-[#F8FAFC] dark:bg-[#0F172A] relative overflow-hidden">
      
      {/* Theme Toggle */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>
      
      {/* Dynamic Background Pattern */}
      <div 
        className="absolute inset-0 z-0 opacity-[0.4] pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(#94A3B8 1px, transparent 1px)",
          backgroundSize: "24px 24px"
        }}
      />

      {/* Left side - Login Form */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-8 sm:px-12 lg:px-20 relative z-10 bg-white/50 dark:bg-[#1E293B]/50 backdrop-blur-3xl border-r border-white/20 dark:border-slate-800/50 shadow-2xl">
        
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="w-full max-w-md mx-auto"
        >
          {/* Logo & Header */}
          <motion.div variants={itemVariants} className="mb-10">
            <div className="w-14 h-14 bg-[#1E3A8A] rounded-full flex items-center justify-center mb-6 shadow-lg shadow-blue-900/20">
              <ShieldCheck className="w-7 h-7 text-white" />
            </div>
            <h1 className="font-serif text-4xl lg:text-5xl font-semibold text-[#0F172A] dark:text-white mb-3">
              Veritas
            </h1>
            <p className="text-[#475569] dark:text-slate-400 text-sm font-medium tracking-wide uppercase">
              Your trusted source for facts
            </p>
          </motion.div>

          {/* Auth Card */}
          <motion.div
            variants={itemVariants}
          >
            <div className="w-full flex justify-center">
              {!isLoaded ? (
                 <div className="p-8 text-center"><Sparkles className="w-8 h-8 text-[#3B82F6] animate-pulse mx-auto" /></div>
              ) : !isSignedIn ? (
                <SignIn 
                  routing="hash" 
                  forceRedirectUrl="/dashboard"
                  fallbackRedirectUrl="/dashboard"
                  appearance={{
                    baseTheme: currentTheme === 'dark' ? dark : undefined,
                    elements: {
                      rootBox: "w-full",
                      card: "shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-[#E2E8F0]/50 dark:border-slate-700/50 rounded-[2rem] w-full",
                      headerTitle: "font-serif text-[#0F172A] dark:text-white",
                      headerSubtitle: "hidden",
                      socialButtonsBlockButton: "border-[#E2E8F0] dark:border-slate-700 hover:bg-[#F8FAFC] dark:hover:bg-slate-800",
                      formButtonPrimary: "bg-[#1E3A8A] hover:bg-[#0F172A] dark:bg-[#3B82F6] dark:hover:bg-[#2563EB]",
                      footerActionLink: "text-[#1E3A8A] hover:text-[#0F172A] dark:text-[#3B82F6] dark:hover:text-blue-400"
                    }
                  }} 
                />
              ) : (
                <div className="bg-white dark:bg-[#1E293B] p-8 rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-[#E2E8F0]/50 dark:border-slate-700/50 w-full text-center">
                  <h3 className="font-serif text-2xl font-semibold text-[#0F172A] dark:text-white mb-2">Welcome Back!</h3>
                  <p className="text-[#475569] dark:text-slate-400 text-sm mb-6">You are already signed in to Veritas.</p>
                  <Link href="/dashboard" className="inline-flex items-center justify-center w-full bg-[#1E3A8A] dark:bg-[#3B82F6] text-white py-3.5 rounded-xl font-semibold hover:bg-[#0F172A] dark:hover:bg-[#2563EB] shadow-md transition-all gap-2 group">
                    Continue to Chat
                  </Link>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Right side - Abstract Graphic / Text */}
      <div className="hidden lg:flex lg:w-[55%] relative p-6 items-center justify-center z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, x: 20 }}
          animate={{ opacity: 1, scale: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="w-full h-full max-h-[850px] relative rounded-[2.5rem] overflow-hidden shadow-2xl bg-gradient-to-br from-[#1E3A8A] via-[#1e40af] to-[#0F172A] flex flex-col justify-center p-16 border border-white/10"
        >
          {/* Abstract decorative glowing orbs */}
          <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] bg-[#3B82F6]/30 rounded-full blur-[100px] pointer-events-none" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none" />
          
          <div className="relative z-10 space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-blue-100 font-medium text-sm">
              <Sparkles className="w-4 h-4 text-blue-300" />
              AI-Powered Verification
            </div>
            
            <h2 className="text-6xl font-serif text-white leading-tight font-bold tracking-tight">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-indigo-200">Fact Checker</span>
            </h2>
            
            <p className="text-xl text-blue-100/80 font-medium max-w-lg leading-relaxed">
              Check your facts here. Don't let misinformation spread. Get instant, accurate, and AI-verified answers to any question.
            </p>

            {/* Decorative Mockup Elements */}
            <div className="mt-16 space-y-4">
              <div className="p-5 bg-white/10 backdrop-blur-md rounded-2xl border border-white/10 w-3/4 transform -rotate-2 hover:rotate-0 transition-transform duration-500 shadow-xl">
                <div className="flex gap-2 items-center mb-3">
                  <div className="w-2 h-2 rounded-full bg-rose-400"></div>
                  <div className="h-2 w-24 bg-white/30 rounded-full"></div>
                </div>
                <div className="h-2 w-3/4 bg-white/20 rounded-full"></div>
              </div>
              
              <div className="p-5 bg-white/10 backdrop-blur-md rounded-2xl border border-white/10 w-4/5 transform rotate-2 hover:rotate-0 transition-transform duration-500 ml-8 shadow-xl">
                <div className="flex gap-2 items-center mb-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                  <div className="h-2 w-16 bg-white/30 rounded-full"></div>
                </div>
                <div className="h-2 w-full bg-white/20 rounded-full mb-2.5"></div>
                <div className="h-2 w-1/2 bg-white/20 rounded-full"></div>
              </div>
            </div>

          </div>
        </motion.div>
      </div>
    </div>
  );
}