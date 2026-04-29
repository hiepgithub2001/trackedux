import { useState, useEffect } from 'react';
import { Button, Space, Typography } from 'antd';
import { DownloadOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS] = useState(() => /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream);
  const [showPrompt, setShowPrompt] = useState(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    return !dismissed && ios && !window.navigator.standalone;
  });
  const { t } = useTranslation();

  useEffect(() => {

    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      setDeferredPrompt(null);
    }
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  if (!showPrompt) return null;

  return (
    <div
      id="pwa-install-prompt"
      style={{
        position: 'fixed',
        bottom: 16,
        left: 16,
        right: 16,
        background: '#fff',
        borderRadius: 12,
        padding: '16px 20px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
      }}
    >
      <div>
        <Text strong style={{ fontSize: 14 }}>
          {t('pwa.installTitle')}
        </Text>
        <br />
        <Text type="secondary" style={{ fontSize: 12 }}>
          {isIOS
            ? 'Tap Share → Add to Home Screen'
            : t('pwa.installMessage')}
        </Text>
      </div>
      <Space>
        {!isIOS && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleInstall}
            size="small"
          >
            {t('pwa.install')}
          </Button>
        )}
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={handleDismiss}
          size="small"
        />
      </Space>
    </div>
  );
}
