import { Translate } from "@phosphor-icons/react";
import { useLanguage } from "../i18n/LanguageContext";

export default function LanguageToggle({ className = "" }) {
  const { language, setLanguage } = useLanguage();
  return (
    <div className={`language-toggle ${className}`.trim()} aria-label="Language selection">
      <Translate size={17} aria-hidden="true" />
      <button type="button" className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")} aria-pressed={language === "en"}>EN</button>
      <button type="button" className={language === "ur" ? "active" : ""} onClick={() => setLanguage("ur")} aria-pressed={language === "ur"}>اردو</button>
    </div>
  );
}
