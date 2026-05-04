import { Layout, Typography, Space, Button, Dropdown, Avatar } from 'antd';
import { SafetyCertificateOutlined, LogoutOutlined, UserOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function SystemLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('nav.profile', 'My Profile'),
      onClick: () => {
        navigate('/system/profile');
      },
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('auth.logout'),
      onClick: async () => {
        await logout();
        navigate('/login');
      },
    },
  ];

  const isProfile = location.pathname.includes('/profile');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          {isProfile ? (
            <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/system/centers')} />
          ) : (
            <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          )}
          <Title level={4} style={{ margin: 0 }}>System Console</Title>
        </Space>
        <Space>
          <LanguageSwitcher />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar
                style={{ backgroundColor: '#1890ff' }}
                icon={<UserOutlined />}
                size="small"
              />
              <Text strong style={{ fontSize: 13 }}>
                {user?.full_name || 'System Admin'}
              </Text>
            </Space>
          </Dropdown>
        </Space>
      </Header>
      
      <Content style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
