import { useState } from 'react';
import { Layout as AntLayout, Menu, Typography, Avatar, Dropdown, Space } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  CalendarOutlined,
  CheckSquareOutlined,
  TeamOutlined,
  DollarOutlined,
  BarChartOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';

const { Header, Sider, Content } = AntLayout;
const { Text } = Typography;

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: '/students', icon: <UserOutlined />, label: t('nav.students') },
    { key: '/schedule', icon: <CalendarOutlined />, label: t('nav.schedule') },
    { key: '/classes', icon: <AppstoreOutlined />, label: t('nav.classes') },
    { key: '/attendance', icon: <CheckSquareOutlined />, label: t('nav.attendance') },
    { key: '/teachers', icon: <TeamOutlined />, label: t('nav.teachers') },
    { key: '/tuition', icon: <DollarOutlined />, label: t('nav.tuition') },
    { key: '/reports', icon: <BarChartOutlined />, label: t('nav.reports') },
    { key: '/notifications', icon: <BellOutlined />, label: t('nav.notifications') },
  ].filter((item) => {
    // Admin sees everything; staff sees all but teachers and tuition management
    if (user?.role === 'admin') return true;
    if (user?.role === 'staff') {
      return !['/teachers', '/tuition', '/reports', '/notifications'].includes(item.key);
    }
    return false;
  });

  const userMenuItems = [
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

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  // Determine selected key from current path
  const selectedKey = '/' + location.pathname.split('/')[1] || '/';
  const currentMenuItem = menuItems.find(item => item.key === selectedKey);

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        breakpoint="lg"
        onBreakpoint={(broken) => setCollapsed(broken)}
        trigger={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        style={{
          background: '#001529',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <Text
            style={{
              color: '#fff',
              fontSize: collapsed ? 18 : 20,
              fontWeight: 700,
              letterSpacing: -0.5,
            }}
          >
            {collapsed ? '🎹' : '🎹 TrackEduX'}
          </Text>
        </div>
        <Menu
          id="main-nav"
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            zIndex: 10,
          }}
        >
          <Typography.Title level={4} style={{ margin: 0 }}>
            {currentMenuItem?.label}
          </Typography.Title>
          <Space size="middle">
            <LanguageSwitcher />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  style={{ backgroundColor: '#667eea' }}
                  icon={<UserOutlined />}
                  size="small"
                />
                <Text strong style={{ fontSize: 13 }}>
                  {user?.full_name || 'User'}
                </Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: 16,
            padding: 24,
            background: '#f5f5f5',
            borderRadius: 8,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
