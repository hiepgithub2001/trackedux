import { useEffect, useState } from 'react';
import { Form, Input, Select, DatePicker, InputNumber, Button, Card, Typography, Space, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createStudent, getStudent, updateStudent } from '../../api/students';
import { listParents } from '../../api/parents';
import dayjs from 'dayjs';
import ParentFormModal from './ParentFormModal';
import { PlusOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { TextArea } = Input;

export default function StudentForm() {
  const { id } = useParams();
  const isEdit = !!id;
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const [isParentModalOpen, setIsParentModalOpen] = useState(false);

  const { data: student } = useQuery({
    queryKey: ['student', id],
    queryFn: () => getStudent(id).then((r) => r.data),
    enabled: isEdit,
  });

  const { data: parentsData } = useQuery({
    queryKey: ['parents'],
    queryFn: () => listParents().then((r) => r.data),
  });

  useEffect(() => {
    if (student && isEdit) {
      form.setFieldsValue({
        ...student,
        date_of_birth: student.date_of_birth ? dayjs(student.date_of_birth) : null,
      });
    }
  }, [student, isEdit, form]);

  const mutation = useMutation({
    mutationFn: (values) => {
      const payload = {
        ...values,
        date_of_birth: values.date_of_birth?.format('YYYY-MM-DD') || null,
      };
      return isEdit ? updateStudent(id, payload) : createStudent(payload);
    },
    onSuccess: () => {
      messageApi.success(isEdit ? 'Student updated' : 'Student created');
      queryClient.invalidateQueries({ queryKey: ['students'] });
      navigate(isEdit ? `/students/${id}` : '/students');
    },
    onError: (err) => {
      messageApi.error(err.response?.data?.detail || 'Error saving student');
    },
  });

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          {t('common.back')}
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          {isEdit ? t('common.edit') : t('students.addStudent')}
        </Title>
      </Space>

      <Card style={{ maxWidth: 720 }}>
        <Form
          id="student-form"
          form={form}
          layout="vertical"
          onFinish={(values) => mutation.mutate(values)}
          initialValues={{ enrollment_status: 'trial', skill_level: 'Beginner' }}
        >
          <Form.Item
            name="parent_id"
            label={t('students.parent')}
            rules={[{ required: true, message: t('validation.required') }]}
          >
            <Space.Compact style={{ width: '100%' }}>
              <Select
                id="parent-select"
                placeholder={t('students.parent')}
                showSearch
                optionFilterProp="label"
                options={(parentsData || []).map((p) => ({
                  label: `${p.full_name} (${p.phone})`,
                  value: p.id,
                }))}
                style={{ width: '100%' }}
              />
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setIsParentModalOpen(true)}
              />
            </Space.Compact>
          </Form.Item>

          <Form.Item
            name="name"
            label={t('students.studentName')}
            rules={[{ required: true, message: t('validation.required') }]}
          >
            <Input id="student-name" />
          </Form.Item>

          <Form.Item name="nickname" label={t('students.nickname')}>
            <Input id="student-nickname" />
          </Form.Item>

          <Space size="large">
            <Form.Item name="date_of_birth" label={t('students.dateOfBirth')}>
              <DatePicker id="student-dob" />
            </Form.Item>

            <Form.Item name="age" label={t('students.age')}>
              <InputNumber id="student-age" min={1} max={99} />
            </Form.Item>
          </Space>

          <Form.Item
            name="skill_level"
            label={t('students.skillLevel')}
            rules={[{ required: true, message: t('validation.required') }]}
          >
            <Select
              id="skill-level-select"
              options={[
                { label: t('students.skillBeginner'), value: 'Beginner' },
                { label: t('students.skillElementary'), value: 'Elementary' },
                { label: t('students.skillIntermediate'), value: 'Intermediate' },
                { label: t('students.skillAdvanced'), value: 'Advanced' },
              ]}
            />
          </Form.Item>

          <Form.Item name="learning_speed" label={t('students.learningSpeed')}>
            <Select
              id="learning-speed-select"
              allowClear
              options={[
                { label: t('students.speedFast'), value: 'Fast' },
                { label: t('students.speedNormal'), value: 'Normal' },
                { label: t('students.speedSlow'), value: 'Slow' },
              ]}
            />
          </Form.Item>

          <Form.Item name="personality_notes" label={t('students.personalityNotes')}>
            <TextArea id="personality-notes" rows={3} />
          </Form.Item>

          <Form.Item name="current_issues" label={t('students.currentIssues')}>
            <TextArea id="current-issues" rows={3} />
          </Form.Item>

          {!isEdit && (
            <Form.Item name="enrollment_status" label={t('students.enrollmentStatus')}>
              <Select
                id="enrollment-status-select"
                options={[
                  { label: t('students.statusTrial'), value: 'trial' },
                  { label: t('students.statusActive'), value: 'active' },
                ]}
              />
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button
                id="student-submit"
                type="primary"
                htmlType="submit"
                loading={mutation.isPending}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                }}
              >
                {t('common.save')}
              </Button>
              <Button onClick={() => navigate(-1)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <ParentFormModal
        open={isParentModalOpen}
        onCancel={() => setIsParentModalOpen(false)}
        onSuccess={(newParentId) => {
          setIsParentModalOpen(false);
          form.setFieldValue('parent_id', newParentId);
        }}
      />
    </div>
  );
}
