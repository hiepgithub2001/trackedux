import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from './AuthContext';
import LanguageSwitcher from '../components/LanguageSwitcher';

const { Title, Text } = Typography;

export default function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [messageApi, contextHolder] = message.useMessage();

  const from = location.state?.from?.pathname || '/';

  const onFinish = async (values) => {
    try {
      const user = await login(values.username, values.password);
      if (user.role === 'parent') {
        navigate('/portal');
      } else if (user.role === 'superadmin') {
        navigate('/system/centers');
      } else {
        navigate(from);
      }
    } catch (error) {
      messageApi.error(
        error.response?.data?.detail || t('auth.loginFailed', 'Login failed'),
      );
    }
  };

  return (
    <div
      id="login-page"
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px',
      }}
    >
      {contextHolder}
      <Card
        style={{
          width: '100%',
          maxWidth: 420,
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}
        bodyStyle={{ padding: '40px 32px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 4, color: '#1a1a2e' }}>
              🎹 TrackEduX
            </Title>
            <Text type="secondary">{t('auth.subtitle', 'Piano Center Management')}</Text>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <LanguageSwitcher />
          </div>

          <Form name="login" onFinish={onFinish} layout="vertical" size="large">
            <Form.Item
              name="username"
              rules={[{ required: true, message: t('auth.usernameRequired', 'Please enter username') }]}
            >
              <Input
                id="login-username"
                prefix={<UserOutlined />}
                placeholder={t('auth.username', 'Username')}
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: t('auth.passwordRequired', 'Please enter password') }]}
            >
              <Input.Password
                id="login-password"
                prefix={<LockOutlined />}
                placeholder={t('auth.password', 'Password')}
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                id="login-submit"
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 48,
                  borderRadius: 8,
                  fontSize: 16,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                }}
              >
                {t('auth.login', 'Log In')}
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
