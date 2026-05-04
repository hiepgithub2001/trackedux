import { useState } from 'react';
import { Card, Form, Input, Button, message, Typography, Select } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from './useAuth';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

export default function ProfilePage() {
  const { user, updateProfile, updatePassword } = useAuth();
  const { t, i18n } = useTranslation();
  
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const handleProfileSubmit = async (values) => {
    setProfileLoading(true);
    try {
      await updateProfile(values);
      message.success(t('profile.updateSuccess', 'Profile updated successfully'));
      if (values.language && values.language !== i18n.language) {
        i18n.changeLanguage(values.language);
      }
    } catch {
      message.error(t('profile.updateError', 'Failed to update profile'));
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (values) => {
    setPasswordLoading(true);
    try {
      await updatePassword({
        current_password: values.current_password,
        new_password: values.new_password,
      });
      message.success(t('profile.passwordSuccess', 'Password updated successfully'));
      passwordForm.resetFields();
    } catch (error) {
      const errMsg = error.response?.data?.detail || t('profile.passwordError', 'Failed to update password');
      message.error(errMsg);
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 0' }}>
      <Title level={3} style={{ marginBottom: 24 }}>{t('profile.title', 'My Profile')}</Title>

      <Card style={{ marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 16 }}>{t('profile.basicInfo', 'Basic Information')}</Title>
        <Form
          form={profileForm}
          layout="vertical"
          initialValues={{
            full_name: user?.full_name,
            email: user?.email,
            language: user?.language || 'vi',
          }}
          onFinish={handleProfileSubmit}
        >
          <Form.Item
            label={t('profile.fullName', 'Full Name')}
            name="full_name"
            rules={[{ required: true, message: t('validation.required', 'This field is required') }]}
          >
            <Input prefix={<UserOutlined />} />
          </Form.Item>
          
          <Form.Item
            label={t('profile.email', 'Email')}
            name="email"
            rules={[
              { type: 'email', message: t('validation.email', 'Please enter a valid email') }
            ]}
          >
            <Input prefix={<MailOutlined />} />
          </Form.Item>
          
          <Form.Item
            label={t('profile.language', 'Language')}
            name="language"
          >
            <Select>
              <Select.Option value="vi">Tiếng Việt</Select.Option>
              <Select.Option value="en">English</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={profileLoading}>
              {t('common.save', 'Save Changes')}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Title level={4} style={{ marginBottom: 16 }}>{t('profile.changePassword', 'Change Password')}</Title>
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordSubmit}
        >
          <Form.Item
            label={t('profile.currentPassword', 'Current Password')}
            name="current_password"
            rules={[{ required: true, message: t('validation.required', 'This field is required') }]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          
          <Form.Item
            label={t('profile.newPassword', 'New Password')}
            name="new_password"
            rules={[
              { required: true, message: t('validation.required', 'This field is required') },
              { min: 6, message: t('validation.minLen', 'Must be at least 6 characters') }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          
          <Form.Item
            label={t('profile.confirmPassword', 'Confirm New Password')}
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: t('validation.required', 'This field is required') },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error(t('validation.passwordMatch', 'The two passwords do not match')));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={passwordLoading}>
              {t('profile.updatePassword', 'Update Password')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
