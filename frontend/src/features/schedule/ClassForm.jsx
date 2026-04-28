import { Form, Select, Input, InputNumber, Button, Card, Typography, Space, message, Spin, AutoComplete } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createClass, updateClass, getClass } from '../../api/classes';
import { listTeachers } from '../../api/teachers';
import { listStudents } from '../../api/students';
import { fetchLessonKinds } from '../../api/lessonKinds';
import { useState } from 'react';

const { Title } = Typography;
const DAYS = [
  { label: 'Monday', value: 0 }, { label: 'Tuesday', value: 1 }, { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 }, { label: 'Friday', value: 4 }, { label: 'Saturday', value: 5 }, { label: 'Sunday', value: 6 },
];

const TIME_OPTIONS = [];
for (let h = 7; h <= 21; h++) {
  for (let m = 0; m < 60; m += 15) {
    if (h === 21 && m > 0) continue;
    const hour = h.toString().padStart(2, '0');
    const min = m.toString().padStart(2, '0');
    TIME_OPTIONS.push({ label: `${hour}:${min}`, value: `${hour}:${min}` });
  }
}

export default function ClassForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();
  const [lessonKindSearch, setLessonKindSearch] = useState('');

  const { data: teachers } = useQuery({ queryKey: ['teachers'], queryFn: () => listTeachers().then((r) => r.data) });
  const { data: studentsData } = useQuery({ queryKey: ['students', { page_size: 100 }], queryFn: () => listStudents({ page_size: 100 }).then((r) => r.data) });

  const { data: classData, isLoading: isClassLoading } = useQuery({
    queryKey: ['class', id],
    queryFn: () => getClass(id).then((r) => r.data),
    enabled: isEdit,
  });

  const { data: lessonKindsData } = useQuery({
    queryKey: ['lessonKinds', lessonKindSearch],
    queryFn: () => fetchLessonKinds(lessonKindSearch).then((r) => r.data),
  });

  const mutation = useMutation({
    mutationFn: (values) => {
      const payload = {
        name: values.name,
        teacher_id: values.teacher_id,
        day_of_week: values.day_of_week,
        start_time: values.start_time,
        duration_minutes: values.duration_minutes,
        tuition_fee_per_lesson: values.tuition_fee_per_lesson,
        lesson_kind_name: values.lesson_kind_name,
        is_recurring: values.recurring_pattern !== 'none',
        recurring_pattern: values.recurring_pattern,
        student_ids: values.student_ids || [],
      };
      if (isEdit) {
        return updateClass(id, payload);
      }
      return createClass(payload);
    },
    onSuccess: () => {
      messageApi.success(isEdit ? t('common.updated') : t('schedule.created'));
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['class'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['student'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate(isEdit ? `/classes/${id}` : '/classes');
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail.conflicts) {
        messageApi.error(`${t('schedule.conflict')}: ${detail.conflicts.map((c) => c.message).join('; ')}`);
      } else {
        messageApi.error(detail || (isEdit ? t('common.updateError') : t('schedule.createError')));
      }
    },
  });

  if (isEdit && isClassLoading) return <Spin size="large" />;

  const initialValues = isEdit && classData ? {
    ...classData,
    start_time: classData.start_time?.substring(0, 5),
    student_ids: classData.enrolled_students?.map(s => s.id) || [],
    recurring_pattern: classData.recurring_pattern || (classData.is_recurring ? 'weekly' : 'none'),
  } : {
    recurring_pattern: 'weekly', 
    duration_minutes: 60,
  };

  const lessonKindOptions = (lessonKindsData || []).map(k => ({ value: k.name }));
  if (lessonKindSearch && !lessonKindsData?.some(k => k.name.toLowerCase() === lessonKindSearch.toLowerCase())) {
    lessonKindOptions.push({ value: lessonKindSearch, label: t('classes.createKindOption', { kind: lessonKindSearch }) });
  }

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>{t('common.back')}</Button>
        <Title level={3} style={{ margin: 0 }}>{isEdit ? t('common.edit') : t('schedule.createClass')}</Title>
      </Space>
      <Card style={{ maxWidth: 640 }}>
        <Form
          form={form}
          id="class-form"
          layout="vertical"
          onFinish={(v) => mutation.mutate(v)}
          initialValues={initialValues}
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
            <Select 
              id="class-start-time" 
              showSearch
              options={TIME_OPTIONS}
              style={{ width: '100%' }}
            />
          </Form.Item>
          <Form.Item
            name="duration_minutes"
            label={t('schedule.duration')}
            rules={[{ required: true, type: 'number', min: 1, message: t('validation.required') }]}
          >
            <InputNumber id="class-duration-input" min={1} max={600} step={15} style={{ width: '100%' }} addonAfter={t('schedule.minutes')} />
          </Form.Item>
          <Form.Item name="lesson_kind_name" label={t('classes.lessonKind', 'Lesson Kind')} rules={[{ required: true }]}>
            <AutoComplete
              options={lessonKindOptions}
              onSearch={setLessonKindSearch}
              placeholder={t('classes.lessonKind', 'Lesson Kind')}
            />
          </Form.Item>
          <Form.Item
            name="tuition_fee_per_lesson"
            label={t('classes.feePerLesson')}
            rules={[{ required: true, type: 'number', min: 1, message: t('validation.required') }]}
          >
            <InputNumber 
              id="class-form-tuition-fee-per-lesson" 
              min={1} 
              max={100000000} 
              style={{ width: '100%' }} 
              addonAfter="VND"
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value?.replace(/\$\s?|(,*)/g, '')}
            />
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
          <Form.Item name="recurring_pattern" label={t('schedule.recurringPattern', 'Recurring Pattern')}>
            <Select>
              <Select.Option value="none">{t('schedule.recurringNone', 'One-off (None)')}</Select.Option>
              <Select.Option value="weekly">{t('schedule.recurringWeekly', 'Weekly')}</Select.Option>
              <Select.Option value="bi-weekly">{t('schedule.recurringBiWeekly', 'Bi-weekly')}</Select.Option>
              <Select.Option value="monthly">{t('schedule.recurringMonthly', 'Monthly')}</Select.Option>
            </Select>
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
