import { useEffect, useState } from 'react';
import { Form, Input, Select, DatePicker, InputNumber, Button, Card, Typography, Space, message, Collapse } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createStudent, getStudent, updateStudent } from '../../api/students';
import { listClasses } from '../../api/classes';
import dayjs from 'dayjs';

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
  const [activeKeys, setActiveKeys] = useState([]);

  const { data: student } = useQuery({
    queryKey: ['student', id],
    queryFn: () => getStudent(id).then((r) => r.data),
    enabled: isEdit,
  });

  const { data: classes, isLoading: isLoadingClasses } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
  });

  useEffect(() => {
    if (student && isEdit) {
      form.setFieldsValue({
        ...student,
        contact: student.contact || {},
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
      queryClient.invalidateQueries({ queryKey: ['student'] });
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['class'] });
      navigate(isEdit ? `/students/${id}` : '/students');
    },
    onError: (err) => {
      messageApi.error(err.response?.data?.detail || 'Error saving student');
    },
  });

  const onFinishFailed = ({ errorFields }) => {
    const hasContactError = errorFields.some(field => field.name[0] === 'contact');
    if (hasContactError && !activeKeys.includes('contact')) {
      setActiveKeys(['contact']);
    }
  };

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
          onFinishFailed={onFinishFailed}
          initialValues={{ enrollment_status: 'trial', contact: {}, class_ids: [] }}
        >
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

          <Form.Item name="class_ids" label={t('schedule.title')}>
            <Select
              id="student-classes-select"
              mode="multiple"
              allowClear
              placeholder={t('common.select')}
              loading={isLoadingClasses}
              options={classes?.map(c => ({
                label: `${c.display_id} - ${c.name}`,
                value: c.id
              })) || []}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
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
            <TextArea id="personality-notes" rows={3} placeholder={t('students.notesPlaceholder')} />
          </Form.Item>

          <Form.Item name="current_issues" label={t('students.currentIssues')}>
            <TextArea id="current-issues" rows={3} />
          </Form.Item>

          <Collapse 
            activeKey={activeKeys} 
            onChange={setActiveKeys}
            style={{ marginBottom: 24 }}
            items={[
              {
                key: 'contact',
                label: t('students.contactInfo'),
                children: (
                  <>
                    <Form.Item name={['contact', 'name']} label={t('students.contactName')}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={['contact', 'relationship']} label={t('students.relationship')}>
                      <Select
                        allowClear
                        options={[
                          { label: t('students.relationshipParent'), value: 'parent' },
                          { label: t('students.relationshipGuardian'), value: 'guardian' },
                          { label: t('students.relationshipSelf'), value: 'self' },
                          { label: t('students.relationshipOther'), value: 'other' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name={['contact', 'phone']} label={t('common.phone')}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={['contact', 'phone_secondary']} label={t('common.phone') + ' 2'}>
                      <Input />
                    </Form.Item>
                    <Form.Item name={['contact', 'email']} label={t('common.email')}>
                      <Input type="email" />
                    </Form.Item>
                    <Form.Item name={['contact', 'address']} label={t('common.address')}>
                      <TextArea rows={2} />
                    </Form.Item>
                    <Form.Item name={['contact', 'zalo_id']} label="Zalo ID">
                      <Input />
                    </Form.Item>
                    <Form.Item name={['contact', 'notes']} label={t('common.notes')}>
                      <TextArea rows={2} />
                    </Form.Item>
                  </>
                )
              }
            ]}
          />

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
    </div>
  );
}
