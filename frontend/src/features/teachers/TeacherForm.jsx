import { Form, Input, Button, Card, Space, message, Spin, Select } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createTeacher, getTeacher, updateTeacher } from '../../api/teachers';
import { useEffect } from 'react';

const COLORS = [
  "#f5222d", "#fa541c", "#fa8c16", "#faad14", "#fadb14",
  "#a0d911", "#52c41a", "#13c2c2", "#1677ff", "#2f54eb",
  "#722ed1", "#eb2f96", "#ff4d4f", "#ff7a45", "#ffa940",
  "#ffc53d", "#ffec3d", "#bae637", "#73d13d", "#36cfc9"
];

const colorOptions = COLORS.map(c => ({
  value: c,
  label: (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: c }} />
      <span>{c}</span>
    </div>
  )
}));

export default function TeacherForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  const { data: teacher, isLoading } = useQuery({
    queryKey: ['teacher', id],
    queryFn: () => getTeacher(id).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (isEdit && teacher) {
      form.setFieldsValue(teacher);
    }
  }, [isEdit, teacher, form]);

  const mutation = useMutation({
    mutationFn: (values) => isEdit ? updateTeacher(id, values) : createTeacher(values),
    onSuccess: () => {
      messageApi.success(isEdit ? 'Teacher updated' : 'Teacher created');
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      if (isEdit) queryClient.invalidateQueries({ queryKey: ['teacher', id] });
      navigate(isEdit ? `/teachers/${id}` : '/teachers');
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  if (isEdit && isLoading) return <Spin />;

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>{t('common.back')}</Button>
      </Space>
      <Card style={{ maxWidth: 560 }}>
        <Form form={form} id="teacher-form" layout="vertical" onFinish={(v) => mutation.mutate(v)} size="large">
          <Form.Item name="full_name" label={t('teachers.teacherName')} rules={[{ required: true }]}>
            <Input id="teacher-name" />
          </Form.Item>
          <Form.Item name="phone" label={t('common.phone')}><Input id="teacher-phone" /></Form.Item>
          <Form.Item name="email" label={t('common.email')}><Input id="teacher-email" /></Form.Item>
          <Form.Item name="color" label={t('teachers.themeColor', 'Theme Color')}>
            <Select options={colorOptions} placeholder="Select a color" />
          </Form.Item>
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
