import { Form, Select, Input, TimePicker, Switch, Button, Card, Typography, Space, message } from 'antd';
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
        ...values,
        start_time: values.time_range[0].format('HH:mm'),
        end_time: values.time_range[1].format('HH:mm'),
        student_ids: values.student_ids || [],
      };
      delete payload.time_range;
      return createClass(payload);
    },
    onSuccess: () => {
      messageApi.success('Class created');
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      navigate('/schedule');
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail.conflicts) {
        messageApi.error(`${t('schedule.conflict')}: ${detail.conflicts.map((c) => c.message).join('; ')}`);
      } else {
        messageApi.error(detail || 'Error creating class');
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
        <Form id="class-form" layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={{ is_recurring: true, class_type: 'individual' }}>
          <Form.Item name="class_type" label={t('schedule.classType')} rules={[{ required: true }]}>
            <Select id="class-type-select" options={[
              { label: t('schedule.individual'), value: 'individual' },
              { label: t('schedule.pair'), value: 'pair' },
              { label: t('schedule.group'), value: 'group' },
            ]} />
          </Form.Item>
          <Form.Item name="title" label="Title"><Input /></Form.Item>
          <Form.Item name="teacher_id" label={t('schedule.teacher')} rules={[{ required: true }]}>
            <Select id="class-teacher-select" showSearch optionFilterProp="label"
              options={(teachers || []).map((t) => ({ label: t.full_name, value: t.id }))} />
          </Form.Item>
          <Form.Item name="day_of_week" label={t('schedule.dayOfWeek')} rules={[{ required: true }]}>
            <Select id="day-of-week-select" options={DAYS} />
          </Form.Item>
          <Form.Item name="time_range" label={`${t('schedule.startTime')} - ${t('schedule.endTime')}`} rules={[{ required: true }]}>
            <TimePicker.RangePicker format="HH:mm" minuteStep={15} />
          </Form.Item>
          <Form.Item name="student_ids" label={t('schedule.students')}>
            <Select id="class-students-select" mode="multiple" showSearch optionFilterProp="label"
              options={(studentsData?.items || []).map((s) => ({ label: s.name, value: s.id }))} />
          </Form.Item>
          <Form.Item name="is_recurring" valuePropName="checked" label={t('schedule.recurring')}>
            <Switch />
          </Form.Item>
          <Button id="class-submit" type="primary" htmlType="submit" loading={mutation.isPending}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
            {t('common.save')}
          </Button>
        </Form>
      </Card>
    </div>
  );
}
