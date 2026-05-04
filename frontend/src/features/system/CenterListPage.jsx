import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Button, Input, Tag, Space, Typography, Card, Modal, message, Layout } from 'antd';
import { PlusOutlined, SearchOutlined, SafetyCertificateOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { centersApi } from '../../api/centers';
import { useAuth } from '../../auth/AuthContext';
import LanguageSwitcher from '../../components/LanguageSwitcher';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Header, Content } = Layout;

export default function CenterListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { logout, user } = useAuth();
  const [searchText, setSearchText] = useState('');

  const { data: centers, isLoading } = useQuery({
    queryKey: ['centers', { search: searchText }],
    queryFn: () => centersApi.listCenters({ search: searchText || undefined }),
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, isActive }) => centersApi.updateCenterStatus(id, isActive),
    onSuccess: () => {
      message.success(t('system.centers.statusUpdated', 'Status updated successfully'));
      queryClient.invalidateQueries({ queryKey: ['centers'] });
    },
    onError: () => {
      message.error(t('system.centers.statusUpdateFailed', 'Failed to update status'));
    },
  });

  const handleToggleStatus = (record) => {
    Modal.confirm({
      title: record.is_active 
        ? t('system.centers.deactivateConfirm', 'Deactivate this center?')
        : t('system.centers.activateConfirm', 'Activate this center?'),
      content: t('system.centers.statusWarning', 'This affects all users logging into this center.'),
      okText: t('common.yes', 'Yes'),
      cancelText: t('common.cancel', 'Cancel'),
      onOk: () => {
        toggleStatusMutation.mutate({ id: record.id, isActive: !record.is_active });
      },
    });
  };

  const columns = [
    {
      title: t('system.centers.code', 'Code'),
      dataIndex: 'code',
      key: 'code',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: t('system.centers.name', 'Center Name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('system.centers.adminUsername', 'Admin Username'),
      dataIndex: 'admin_username',
      key: 'admin_username',
      render: (text) => text || '-',
    },
    {
      title: t('system.centers.registeredAt', 'Registered Date'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: t('system.centers.status', 'Status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? t('common.active', 'Active') : t('common.inactive', 'Inactive')}
        </Tag>
      ),
    },
    {
      title: t('common.actions', 'Actions'),
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            danger={record.is_active}
            onClick={() => handleToggleStatus(record)}
          >
            {record.is_active 
              ? t('system.centers.deactivate', 'Deactivate') 
              : t('system.centers.reactivate', 'Reactivate')}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>System Console</Title>
        </Space>
        <Space>
          <LanguageSwitcher />
          <Text>{user?.full_name}</Text>
          <Button type="text" icon={<LogoutOutlined />} onClick={logout}>
            {t('auth.logout', 'Logout')}
          </Button>
        </Space>
      </Header>
      
      <Content style={{ padding: '24px 48px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Title level={2} style={{ marginBottom: 24 }}>{t('system.centers.title', 'Edu-Centers Management')}</Title>

        <Card bodyStyle={{ padding: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
            <Input
              placeholder={t('system.centers.search', 'Search centers by name or code...')}
              prefix={<SearchOutlined />}
              style={{ width: 300 }}
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/system/centers/new')}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
              {t('system.centers.addCenter', 'Register New Center')}
            </Button>
          </div>

          <Table
            columns={columns}
            dataSource={centers}
            rowKey="id"
            loading={isLoading}
            scroll={{ x: 'max-content' }}
            pagination={{ defaultPageSize: 10 }}
          />
        </Card>
      </Content>
    </Layout>
  );
}
