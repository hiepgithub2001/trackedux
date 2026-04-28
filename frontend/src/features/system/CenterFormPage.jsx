import { useState } from 'react';
import { Form, Input, Button, Card, Typography, Modal, Space, Layout, Alert, message } from 'antd';
import { ArrowLeftOutlined, CopyOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { centersApi } from '../../api/centers';
import LanguageSwitcher from '../../components/LanguageSwitcher';

const { Title, Text, Paragraph } = Typography;
const { Header, Content } = Layout;

export default function CenterFormPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [credentialsModalVisible, setCredentialsModalVisible] = useState(false);
  const [newCenterData, setNewCenterData] = useState(null);

  const createMutation = useMutation({
    mutationFn: (data) => centersApi.createCenter(data),
    onSuccess: (data) => {
      setNewCenterData(data);
      setCredentialsModalVisible(true);
      form.resetFields();
    },
    onError: (error) => {
      if (error.response?.status === 409) {
        message.error(t('system.centers.conflict', 'Username or email already exists.'));
        form.setFields([
          { name: 'admin_username', errors: [t('system.centers.conflict', 'Username or email already exists')] },
        ]);
      } else {
        message.error(t('system.centers.createFailed', 'Failed to register center'));
      }
    },
  });

  const onFinish = (values) => {
    createMutation.mutate(values);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    message.success(t('common.copied', 'Copied to clipboard'));
  };

  const handleModalDone = () => {
    setCredentialsModalVisible(false);
    navigate('/system/centers');
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', borderBottom: '1px solid #f0f0f0' }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/system/centers')} style={{ marginRight: 16 }} />
        <Space>
          <LanguageSwitcher />
          <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>System Console</Title>
        </Space>
      </Header>
      
      <Content style={{ padding: '24px 48px', display: 'flex', justifyContent: 'center' }}>
        <Card 
          style={{ width: '100%', maxWidth: 600, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}
          title={<Title level={3} style={{ margin: 0 }}>{t('system.centers.addCenter', 'Register New Center')}</Title>}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            size="large"
          >
            <Form.Item
              name="name"
              label={t('system.centers.name', 'Center Name')}
              rules={[{ required: true, message: t('system.centers.nameRequired', 'Please enter center name') }]}
            >
              <Input placeholder="E.g., Nhạc Viện ABC" />
            </Form.Item>

            <Form.Item
              name="admin_full_name"
              label={t('system.centers.adminFullName', 'Admin Full Name')}
              rules={[{ required: true, message: t('system.centers.adminFullNameRequired', 'Please enter admin full name') }]}
            >
              <Input placeholder="E.g., Nguyen Van A" />
            </Form.Item>

            <Form.Item
              name="admin_username"
              label={t('system.centers.adminUsername', 'Admin Username')}
              rules={[
                { required: true, message: t('system.centers.adminUsernameRequired', 'Please enter admin username') },
                { min: 3, message: 'Username must be at least 3 characters' }
              ]}
            >
              <Input placeholder="E.g., admin_abc" />
            </Form.Item>

            <Form.Item
              name="admin_email"
              label={t('system.centers.adminEmail', 'Admin Email (Optional)')}
              rules={[{ type: 'email', message: 'Please enter a valid email' }]}
            >
              <Input placeholder="E.g., admin@abc.edu.vn" />
            </Form.Item>

            <Form.Item style={{ marginTop: 32, marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => navigate('/system/centers')}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
                  {t('system.centers.register', 'Register Center')}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>

        <Modal
          title={
            <Space>
              <SafetyCertificateOutlined style={{ color: '#52c41a' }} />
              {t('system.centers.createdSuccess', 'Center Registered Successfully')}
            </Space>
          }
          open={credentialsModalVisible}
          onOk={handleModalDone}
          onCancel={handleModalDone}
          footer={[
            <Button key="done" type="primary" onClick={handleModalDone}>
              {t('common.done', 'Done')}
            </Button>,
          ]}
          closable={false}
          maskClosable={false}
          width={500}
        >
          {newCenterData && (
            <Space direction="vertical" size="large" style={{ width: '100%', marginTop: 16 }}>
              <div>
                <Text type="secondary">{t('system.centers.code', 'Center Code')}</Text>
                <Title level={4} style={{ margin: 0, color: '#1890ff' }}>{newCenterData.center.code}</Title>
              </div>
              
              <Alert
                message={t('system.centers.credentialsAlert', 'Important Credentials')}
                description={
                  <div style={{ marginTop: 8 }}>
                    <p style={{ margin: 0 }}>
                      <Text strong>Username:</Text> {newCenterData.admin_credentials.username}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', marginTop: 8 }}>
                      <Text strong style={{ marginRight: 8 }}>Password:</Text>
                      <Paragraph 
                        copyable={{ text: newCenterData.admin_credentials.temporary_password }} 
                        style={{ margin: 0, fontFamily: 'monospace', fontSize: 16, background: '#f5f5f5', padding: '4px 8px', borderRadius: 4 }}
                      >
                        {newCenterData.admin_credentials.temporary_password}
                      </Paragraph>
                    </div>
                  </div>
                }
                type="warning"
                showIcon
              />
              
              <Text type="danger" strong>
                {t('system.centers.credentialsNote', newCenterData.admin_credentials.note)}
              </Text>
            </Space>
          )}
        </Modal>
      </Content>
    </Layout>
  );
}
