import { createContext, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "fairgig.language";

const translations = {
  en: {
    dashboard: "Dashboard",
    earningsLogger: "Earnings logger",
    grievances: "My grievances",
    incomeCertificate: "Income certificate",
    verificationQueue: "Verification queue",
    pendingReviews: "Pending reviews",
    reviewHistory: "Review history",
    analyticsDashboard: "Analytics dashboard",
    grievanceBoard: "Grievance board",
    incomeTrends: "Income trends",
    signOut: "Sign out",
    workspace: "workspace",
    welcomeBack: "Welcome back",
    signInDescription: "Sign in to manage your income record and workplace concerns.",
    createRecord: "Create your record",
    createDescription: "Start a private, portable history of your gig income.",
    email: "Email address",
    password: "Password",
    fullName: "Full name",
    signIn: "Sign in",
    signingIn: "Signing in",
    createAccount: "Create account",
    creatingAccount: "Creating account",
  },
  ur: {
    dashboard: "ڈیش بورڈ",
    earningsLogger: "آمدنی درج کریں",
    grievances: "میری شکایات",
    incomeCertificate: "آمدنی کا سرٹیفکیٹ",
    verificationQueue: "تصدیقی قطار",
    pendingReviews: "زیر التوا جانچ",
    reviewHistory: "جانچ کی تاریخ",
    analyticsDashboard: "تجزیاتی ڈیش بورڈ",
    grievanceBoard: "شکایات بورڈ",
    incomeTrends: "آمدنی کے رجحانات",
    signOut: "سائن آؤٹ",
    workspace: "ورک اسپیس",
    welcomeBack: "خوش آمدید",
    signInDescription: "اپنی آمدنی اور کام سے متعلق شکایات منظم کرنے کے لیے سائن ان کریں۔",
    createRecord: "اپنا ریکارڈ بنائیں",
    createDescription: "اپنی کام کی آمدنی کا نجی اور قابل منتقلی ریکارڈ شروع کریں۔",
    email: "ای میل ایڈریس",
    password: "پاس ورڈ",
    fullName: "پورا نام",
    signIn: "سائن ان",
    signingIn: "سائن ان ہو رہا ہے",
    createAccount: "اکاؤنٹ بنائیں",
    creatingAccount: "اکاؤنٹ بن رہا ہے",
  },
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem(STORAGE_KEY) === "ur" ? "ur" : "en");

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ur" ? "rtl" : "ltr";
  }, [language]);

  const value = useMemo(() => ({
    language,
    setLanguage,
    t: (key) => translations[language][key] || translations.en[key] || key,
  }), [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
