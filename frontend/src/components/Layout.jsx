import { useState } from 'react';
import { Layout as AntLayout, Menu, Typography, Avatar, Dropdown, Space, Grid } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  DollarOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  BookOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/useAuth';
import LanguageSwitcher from './LanguageSwitcher';

const { Header, Sider, Content } = AntLayout;
const { Text } = Typography;
const { useBreakpoint } = Grid;

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const screens = useBreakpoint();
  const isMobile = screens.md === false; // true on small screens (<768px)

  const allMenuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    {
      key: 'academics',
      icon: <BookOutlined />,
      label: t('nav.academics', 'Academics'),
      children: [
        { key: '/classes', label: t('nav.classes') },
        { key: '/schedule', label: t('nav.schedule') },
        { key: '/attendance', label: t('nav.attendance') },
      ],
    },
    {
      key: 'people',
      icon: <TeamOutlined />,
      label: t('nav.people', 'People'),
      children: [
        { key: '/students', label: t('nav.students') },
        { key: '/teachers', label: t('nav.teachers'), adminOnly: true },
      ],
    },
    { key: '/tuition', icon: <DollarOutlined />, label: t('nav.tuition'), adminOnly: true },

    { key: '/notifications', icon: <BellOutlined />, label: t('nav.notifications'), adminOnly: true },
  ];

  const filterMenu = (items) => {
    return items
      .filter((item) => {
        if (user?.role === 'admin' || user?.role === 'superadmin') return true;
        if (user?.role === 'staff') return !item.adminOnly;
        return false;
      })
      .map((item) => {
        if (item.children) {
          const filteredChildren = filterMenu(item.children);
          return { ...item, children: filteredChildren };
        }
        return item;
      });
  };

  const menuItems = filterMenu(allMenuItems);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('nav.profile', 'My Profile'),
      onClick: () => {
        navigate('/profile');
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

  const handleMenuClick = ({ key }) => {
    navigate(key);
    if (isMobile) {
      setCollapsed(true);
    }
  };

  // Determine selected key from current path
  const selectedKey = '/' + location.pathname.split('/')[1] || '/';
  
  const flattenMenu = (items) => items.reduce((acc, item) => {
    if (item.children) return [...acc, ...flattenMenu(item.children)];
    return [...acc, item];
  }, []);
  const currentMenuItem = flattenMenu(menuItems).find(item => item.key === selectedKey);

  const findParentKey = (items, targetKey, parentKey = null) => {
    for (const item of items) {
      if (item.key === targetKey) return parentKey;
      if (item.children) {
        const found = findParentKey(item.children, targetKey, item.key);
        if (found) return found;
      }
    }
    return null;
  };
  const parentKey = findParentKey(menuItems, selectedKey);
  const defaultOpenKeys = parentKey ? [parentKey] : [];

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        breakpoint="lg"
        collapsedWidth={isMobile ? 0 : 80}
        onBreakpoint={(broken) => setCollapsed(broken)}
        trigger={null}
        style={{
          background: '#001529',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
          position: isMobile ? 'absolute' : 'relative',
          height: '100vh',
          zIndex: 100,
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
              whiteSpace: 'nowrap',
            }}
          >
            {collapsed ? '🎓' : '🎓 TrackEduX'}
          </Text>
        </div>
        <Menu
          id="main-nav"
          theme="dark"
          mode="inline"
          defaultOpenKeys={defaultOpenKeys}
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      
      {/* Overlay for mobile when sidebar is open */}
      {isMobile && !collapsed && (
        <div 
          style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            background: 'rgba(0,0,0,0.45)', 
            zIndex: 99 
          }} 
          onClick={() => setCollapsed(true)}
        />
      )}

      <AntLayout style={{ width: isMobile ? '100%' : 'auto' }}>
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            zIndex: 10,
          }}
        >
          {isMobile && (
            <div style={{ marginRight: 16, cursor: 'pointer' }} onClick={() => setCollapsed(!collapsed)}>
              {collapsed ? <MenuUnfoldOutlined style={{ fontSize: 18 }} /> : <MenuFoldOutlined style={{ fontSize: 18 }} />}
            </div>
          )}

          {!isMobile && (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
              <Typography.Title level={4} style={{ margin: 0 }}>
                {currentMenuItem?.label}
              </Typography.Title>
            </div>
          )}

          <div style={{ flex: isMobile ? 1 : 1, display: 'flex', justifyContent: isMobile ? 'flex-start' : 'center', alignItems: 'center', overflow: 'hidden' }}>
            {user?.center?.name && (
              <Typography.Text strong style={{ fontSize: isMobile ? '16px' : '18px', color: '#1a1a2e', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.center.name}
              </Typography.Text>
            )}
          </div>

          <div style={{ flex: isMobile ? 'none' : 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
            <Space size={isMobile ? 'small' : 'middle'}>
              <LanguageSwitcher />
              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar
                    style={{ backgroundColor: '#667eea' }}
                    icon={<UserOutlined />}
                    size="small"
                  />
                  {!isMobile && (
                    <Text strong style={{ fontSize: 13 }}>
                      {user?.full_name || 'User'}
                    </Text>
                  )}
                </Space>
              </Dropdown>
            </Space>
          </div>
        </Header>
        <Content
          style={{
            margin: isMobile ? '12px' : '16px',
            padding: isMobile ? '12px' : '24px',
            background: '#f5f5f5',
            borderRadius: 8,
            minHeight: 280,
            overflowX: 'hidden',
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
