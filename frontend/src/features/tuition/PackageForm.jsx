import { Modal, Form, Select, AutoComplete, InputNumber, Button, Space, Typography, Alert, message } from 'antd';
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { listStudents } from '../../api/students';
import { listClasses } from '../../api/classes';
import { createPackage } from '../../api/packages';

const { Text } = Typography;

export default function PackageForm({ open, onCancel }) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();

  const [isManualFeeEdit, setIsManualFeeEdit] = useState(false);

  // Watch form values for auto-fill and validation
  const selectedStudentId = Form.useWatch('student_id', form);
  const selectedClassId = Form.useWatch('class_session_id', form);
  const numberOfLessons = Form.useWatch('number_of_lessons', form);

  const { data: studentsData } = useQuery({
    queryKey: ['students', { page_size: 100 }],
    queryFn: () => listStudents({ page_size: 100 }).then((r) => r.data),
    enabled: open,
  });

  const { data: classesData } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
    enabled: open,
  });

  const selectedClass = classesData?.find(c => c.id === selectedClassId);

  // Auto-fill logic
  useEffect(() => {
    if (!isManualFeeEdit && selectedClass?.tuition_fee_per_lesson && numberOfLessons) {
      const computedFee = selectedClass.tuition_fee_per_lesson * numberOfLessons;
      form.setFieldsValue({ tuition_fee: computedFee });
    }
  }, [selectedClassId, numberOfLessons, isManualFeeEdit, selectedClass, form]);

  const handleFeeChange = () => {
    setIsManualFeeEdit(true);
  };

  const resetAutoFill = () => {
    setIsManualFeeEdit(false);
    if (selectedClass?.tuition_fee_per_lesson && numberOfLessons) {
      form.setFieldsValue({ tuition_fee: selectedClass.tuition_fee_per_lesson * numberOfLessons });
    }
  };

  // Check enrollment
  const isStudentEnrolled = () => {
    if (!selectedStudentId || !selectedClass) return true;
    return selectedClass.enrolled_students?.some(s => s.id === selectedStudentId);
  };

  const createMutation = useMutation({
    mutationFn: (values) => createPackage(values),
    onSuccess: () => {
      messageApi.success(t('common.save'));
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      form.resetFields();
      setIsManualFeeEdit(false);
      onCancel();
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  // Prepare class options
  const classOptions = (classesData || []).map(c => ({
    value: c.id,
    label: `${c.display_id || c.name} - ${c.teacher_name} - ${c.start_time}`,
  }));

  return (
    <Modal
      title={t('package.assignPackage')}
      open={open}
      onCancel={() => {
        form.resetFields();
        setIsManualFeeEdit(false);
        onCancel();
      }}
      footer={null}
    >
      {contextHolder}
      <Form
        form={form}
        layout="vertical"
        onFinish={(v) => createMutation.mutate(v)}
        initialValues={{ number_of_lessons: 12 }}
      >
        <Form.Item name="student_id" label={t('students.studentName')} rules={[{ required: true }]}>
          <Select 
            showSearch 
            optionFilterProp="label" 
            options={(studentsData?.items || []).map((s) => ({ label: s.name, value: s.id }))} 
          />
        </Form.Item>

        <Form.Item name="class_session_id" label={t('package.class')} rules={[{ required: true }]}>
          <Select
            showSearch
            optionFilterProp="label"
            options={classOptions}
          />
        </Form.Item>

        {!isStudentEnrolled() && (
          <Alert 
            type="warning" 
            showIcon 
            style={{ marginBottom: 24 }}
            message={
              <span>
                {t('package.notEnrolled')} <Link to={`/classes/${selectedClassId}`}>{t('common.edit')}</Link>
              </span>
            } 
          />
        )}

        <Form.Item name="number_of_lessons" label={t('package.numberOfLessons')} rules={[{ required: true }]}>
          <InputNumber min={1} max={500} precision={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label={t('package.tuitionFee')} required>
          <Space.Compact style={{ width: '100%' }}>
            <Form.Item name="tuition_fee" noStyle rules={[{ required: true }]}>
              <InputNumber
                min={1}
                max={1000000000}
                style={{ width: '100%' }}
                addonAfter="VND"
                onChange={handleFeeChange}
                formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value?.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
            {isManualFeeEdit && (
              <Button onClick={resetAutoFill}>{t('package.resetAutoFill')}</Button>
            )}
          </Space.Compact>
        </Form.Item>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
          <Space>
            <Button onClick={onCancel}>{t('common.cancel')}</Button>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>{t('common.save')}</Button>
          </Space>
        </div>
      </Form>
    </Modal>
  );
}
