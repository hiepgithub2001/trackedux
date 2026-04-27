import { useState, useEffect } from 'react';
import { Alert } from 'antd';
import { WifiOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export default function ConnectionBanner() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const { t } = useTranslation();

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div
      id="connection-banner"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1001,
      }}
    >
      <Alert
        message={t('pwa.offline')}
        description={t('pwa.offlineMessage')}
        type="warning"
        showIcon
        icon={<WifiOutlined />}
        banner
      />
    </div>
  );
}
