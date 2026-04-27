import { Form, Input, Button, Card, Typography, Space, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createTeacher } from '../../api/teachers';

const { Title } = Typography;

export default function TeacherForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();

  const mutation = useMutation({
    mutationFn: (values) => createTeacher(values),
    onSuccess: () => {
      messageApi.success('Teacher created');
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      navigate('/teachers');
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>{t('common.back')}</Button>
        <Title level={3} style={{ margin: 0 }}>{t('teachers.addTeacher')}</Title>
      </Space>
      <Card style={{ maxWidth: 560 }}>
        <Form id="teacher-form" layout="vertical" onFinish={(v) => mutation.mutate(v)} size="large">
          <Form.Item name="full_name" label={t('teachers.teacherName')} rules={[{ required: true }]}>
            <Input id="teacher-name" />
          </Form.Item>
          <Form.Item name="phone" label={t('common.phone')}><Input id="teacher-phone" /></Form.Item>
          <Form.Item name="email" label={t('common.email')}><Input id="teacher-email" /></Form.Item>
          <Form.Item name="notes" label={t('common.notes')}><Input.TextArea rows={3} /></Form.Item>
          <Button id="teacher-submit" type="primary" htmlType="submit" loading={mutation.isPending}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
            {t('common.save')}
          </Button>
        </Form>
      </Card>
    </div>
  );
}
