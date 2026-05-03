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
        tuition_fee_per_lesson: values.tuition_fee_per_lesson,
        lesson_kind_name: values.lesson_kind_name,
        student_ids: values.student_ids || [],
      };
      if (isEdit) {
        return updateClass(id, payload);
      }
      return createClass(payload);
    },
    onSuccess: () => {
      messageApi.success(isEdit ? t('common.updated') : t('classes.created', 'Class created'));
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['class'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['student'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate(isEdit ? `/classes/${id}` : '/classes');
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      messageApi.error(detail || (isEdit ? t('common.updateError') : t('common.createError', 'Failed to create')));
    },
  });

  if (isEdit && isClassLoading) return <Spin size="large" />;

  const initialValues = isEdit && classData ? {
    ...classData,
    student_ids: classData.enrolled_students?.map(s => s.id) || [],
  } : {};

  const lessonKindOptions = (lessonKindsData || []).map(k => ({ value: k.name }));
  if (lessonKindSearch && !lessonKindsData?.some(k => k.name.toLowerCase() === lessonKindSearch.toLowerCase())) {
    lessonKindOptions.push({ value: lessonKindSearch, label: t('classes.createKindOption', { kind: lessonKindSearch }) });
  }

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>{t('common.back')}</Button>
        <Title level={3} style={{ margin: 0 }}>{isEdit ? t('classes.editClass', 'Edit Class') : t('classes.createClass')}</Title>
      </Space>
      <Card style={{ maxWidth: 640 }}>
        <Form
          form={form}
          id="class-form"
          layout="vertical"
          onFinish={(v) => mutation.mutate(v)}
          initialValues={initialValues}
        >
          <Form.Item name="name" label={t('classes.className', 'Class Name')} rules={[{ required: true, message: t('validation.required') }]}>
            <Input id="class-name-input" placeholder={t('classes.classNamePlaceholder', 'e.g. Piano Beginner Group A')} maxLength={200} />
          </Form.Item>
          <Form.Item name="teacher_id" label={t('schedule.teacher')} rules={[{ required: true }]}>
            <Select
              id="class-teacher-select"
              showSearch
              optionFilterProp="label"
              options={(teachers || []).map((teacher) => ({ label: teacher.full_name, value: teacher.id }))}
            />
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
