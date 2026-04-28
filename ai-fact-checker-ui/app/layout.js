import { Inter, Playfair_Display } from "next/font/google";
import { ClerkProvider } from '@clerk/nextjs';
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
});

export const metadata = {
  title: "AI Fact Checker",
  description: "A serene, minimalist AI-powered fact-checking companion.",
};

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html
        lang="en"
        className={`${inter.variable} ${playfair.variable} h-full antialiased`}
      >
        <body className="min-h-full flex flex-col font-sans bg-background text-foreground">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
