import { useState, useEffect } from 'react';
import { Button, Space, Typography } from 'antd';
import { DownloadOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

export default function InstallPrompt({ inline = false }) {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS] = useState(() => /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream);
  const [showPrompt, setShowPrompt] = useState(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    return inline ? true : (!dismissed && ios && !window.navigator.standalone); // if inline, always show but wait for deferredPrompt or iOS instructions
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
    if (!inline) setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  if (!showPrompt) return null;
  // If inline and no deferredPrompt and not iOS, we might not want to show it, or we can just show instructions
  // Usually, if not iOS and no deferredPrompt, PWA is already installed or unsupported.
  if (inline && !isIOS && !deferredPrompt) return null;

  return (
    <div
      id={inline ? "pwa-install-inline" : "pwa-install-prompt"}
      style={inline ? {
        background: '#f8f9fa',
        borderRadius: 8,
        padding: '16px',
        border: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        marginTop: 16
      } : {
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: 32, lineHeight: 1 }}>🎓</div>
        <div>
          <Text strong style={{ fontSize: 14 }}>
            TrackEduX
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {isIOS
              ? 'Tap Share → Add to Home Screen'
              : t('pwa.installMessage')}
          </Text>
        </div>
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
        {!inline && (
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleDismiss}
            size="small"
          />
        )}
      </Space>
    </div>
  );
}
