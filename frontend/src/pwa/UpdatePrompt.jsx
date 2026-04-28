import { useEffect } from 'react';
import { Button, notification } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export default function UpdatePrompt() {
  const { t } = useTranslation();

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
      });

      // Listen for waiting service worker
      navigator.serviceWorker.ready.then((registration) => {
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                notification.info({
                  key: 'pwa-update',
                  message: t('pwa.updateAvailable'),
                  description: t('pwa.updateMessage'),
                  btn: (
                    <Button
                      type="primary"
                      size="small"
                      icon={<SyncOutlined />}
                      onClick={() => {
                        newWorker.postMessage({ type: 'SKIP_WAITING' });
                        notification.destroy('pwa-update');
                      }}
                    >
                      {t('pwa.update')}
                    </Button>
                  ),
                  duration: 0,
                });
              }
            });
          }
        });
      });
    }
  }, [t]);

  return null;
}
