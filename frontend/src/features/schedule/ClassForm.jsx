import { Form, Select, Input, TimePicker, InputNumber, Switch, Button, Card, Typography, Space, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createClass } from '../../api/classes';
import { listTeachers } from '../../api/teachers';
import { listStudents } from '../../api/students';

const { Title } = Typography;
const DAYS = [
  { label: 'Monday', value: 0 }, { label: 'Tuesday', value: 1 }, { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 }, { label: 'Friday', value: 4 }, { label: 'Saturday', value: 5 }, { label: 'Sunday', value: 6 },
];

export default function ClassForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();

  const { data: teachers } = useQuery({ queryKey: ['teachers'], queryFn: () => listTeachers().then((r) => r.data) });
  const { data: studentsData } = useQuery({ queryKey: ['students', { page_size: 100 }], queryFn: () => listStudents({ page_size: 100 }).then((r) => r.data) });

  const mutation = useMutation({
    mutationFn: (values) => {
      const payload = {
        name: values.name,
        teacher_id: values.teacher_id,
        day_of_week: values.day_of_week,
        start_time: values.start_time.format('HH:mm'),
        duration_minutes: values.duration_minutes,
        is_recurring: values.is_recurring,
        student_ids: values.student_ids || [],
      };
      return createClass(payload);
    },
    onSuccess: () => {
      messageApi.success(t('schedule.created'));
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      navigate('/schedule');
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail.conflicts) {
        messageApi.error(`${t('schedule.conflict')}: ${detail.conflicts.map((c) => c.message).join('; ')}`);
      } else {
        messageApi.error(detail || t('schedule.createError'));
      }
    },
  });

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>{t('common.back')}</Button>
        <Title level={3} style={{ margin: 0 }}>{t('schedule.createClass')}</Title>
      </Space>
      <Card style={{ maxWidth: 640 }}>
        <Form
          id="class-form"
          layout="vertical"
          onFinish={(v) => mutation.mutate(v)}
          initialValues={{ is_recurring: true, duration_minutes: 60 }}
        >
          <Form.Item name="name" label={t('schedule.name')} rules={[{ required: true, message: t('validation.required') }]}>
            <Input id="class-name-input" placeholder={t('schedule.namePlaceholder')} maxLength={200} />
          </Form.Item>
          <Form.Item name="teacher_id" label={t('schedule.teacher')} rules={[{ required: true }]}>
            <Select
              id="class-teacher-select"
              showSearch
              optionFilterProp="label"
              options={(teachers || []).map((teacher) => ({ label: teacher.full_name, value: teacher.id }))}
            />
          </Form.Item>
          <Form.Item name="day_of_week" label={t('schedule.dayOfWeek')} rules={[{ required: true }]}>
            <Select id="day-of-week-select" options={DAYS} />
          </Form.Item>
          <Form.Item name="start_time" label={t('schedule.startTime')} rules={[{ required: true }]}>
            <TimePicker id="class-start-time" format="HH:mm" minuteStep={15} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="duration_minutes"
            label={t('schedule.duration')}
            rules={[{ required: true, type: 'number', min: 1, message: t('validation.required') }]}
          >
            <InputNumber id="class-duration-input" min={1} max={600} step={15} style={{ width: '100%' }} addonAfter={t('schedule.minutes')} />
          </Form.Item>
          <Form.Item name="student_ids" label={t('schedule.students')}>
            <Select
              id="class-students-select"
              mode="multiple"
              showSearch
              optionFilterProp="label"
              options={(studentsData?.items || []).map((s) => ({ label: s.name, value: s.id }))}
            />
          </Form.Item>
          <Form.Item name="is_recurring" valuePropName="checked" label={t('schedule.recurring')}>
            <Switch />
          </Form.Item>
          <Button
            id="class-submit"
            type="primary"
            htmlType="submit"
            loading={mutation.isPending}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
          >
            {t('common.save')}
          </Button>
        </Form>
      </Card>
    </div>
  );
}
