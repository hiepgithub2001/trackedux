import { Button } from 'antd';
import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language;

  const toggleLanguage = () => {
    const newLang = currentLang === 'vi' ? 'en' : 'vi';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  return (
    <Button
      id="language-switcher"
      type="text"
      onClick={toggleLanguage}
      style={{
        fontWeight: 600,
        fontSize: 13,
        padding: '4px 8px',
        borderRadius: 6,
        color: '#555',
      }}
    >
      <span style={{ color: currentLang === 'vi' ? '#1677ff' : '#aaa' }}>VI</span>
      {' | '}
      <span style={{ color: currentLang === 'en' ? '#1677ff' : '#aaa' }}>EN</span>
    </Button>
  );
}
