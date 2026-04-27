import { Table, Tag, Card, Typography, Select, Button, Space, Modal, Form, InputNumber, DatePicker, Input, message } from 'antd';
import { PlusOutlined, DollarOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { listPackages, createPackage, recordPayment } from '../../api/packages';
import { listStudents } from '../../api/students';
import dayjs from 'dayjs';

const { Title } = Typography;

export default function TuitionPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [createModal, setCreateModal] = useState(false);
  const [paymentModal, setPaymentModal] = useState(null);

  const { data: packages, isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: () => listPackages({}).then((r) => r.data),
  });

  const { data: studentsData } = useQuery({
    queryKey: ['students', { page_size: 100 }],
    queryFn: () => listStudents({ page_size: 100 }).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (values) => createPackage(values),
    onSuccess: () => {
      messageApi.success('Package created');
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      setCreateModal(false);
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  const paymentMutation = useMutation({
    mutationFn: ({ packageId, ...data }) => recordPayment(packageId, { ...data, payment_date: data.payment_date.format('YYYY-MM-DD') }),
    onSuccess: () => {
      messageApi.success('Payment recorded');
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      setPaymentModal(null);
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  const columns = [
    { title: t('students.studentName'), dataIndex: 'student_name', key: 'student_name' },
    { title: t('tuition.packageType'), dataIndex: 'package_type', key: 'package_type' },
    { title: t('tuition.totalSessions'), dataIndex: 'total_sessions', key: 'total_sessions' },
    {
      title: t('tuition.remainingSessions'), dataIndex: 'remaining_sessions', key: 'remaining_sessions',
      render: (val) => <Tag color={val <= 2 ? 'red' : val <= 5 ? 'orange' : 'green'}>{val}</Tag>,
    },
    {
      title: t('tuition.price'), dataIndex: 'price', key: 'price',
      render: (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val),
    },
    {
      title: t('tuition.paymentStatus'), dataIndex: 'payment_status', key: 'payment_status',
      render: (status) => <Tag color={status === 'paid' ? 'green' : 'red'}>{t(`tuition.${status}`)}</Tag>,
    },
    {
      title: t('common.actions'), key: 'actions',
      render: (_, record) => (
        <Button icon={<DollarOutlined />} size="small" onClick={(e) => { e.stopPropagation(); setPaymentModal(record.id); }}>
          {t('tuition.recordPayment')}
        </Button>
      ),
    },
  ];

  return (
    <div className="fade-in">
      {contextHolder}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>{t('tuition.title')}</Title>
        <Button id="create-package-btn" type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
          {t('tuition.createPackage')}
        </Button>
      </div>

      <Card>
        <Table id="tuition-table" columns={columns} dataSource={packages || []} rowKey="id" loading={isLoading} />
      </Card>

      <Modal title={t('tuition.createPackage')} open={createModal} onCancel={() => setCreateModal(false)} footer={null}>
        <Form layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="student_id" label={t('students.studentName')} rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={(studentsData?.items || []).map((s) => ({ label: s.name, value: s.id }))} />
          </Form.Item>
          <Form.Item name="package_type" label={t('tuition.packageType')} rules={[{ required: true }]}>
            <Select options={[
              { label: t('tuition.sessions12'), value: '12' }, { label: t('tuition.sessions24'), value: '24' },
              { label: t('tuition.sessions36'), value: '36' }, { label: t('tuition.custom'), value: 'custom' },
            ]} />
          </Form.Item>
          <Form.Item name="total_sessions" label={t('tuition.totalSessions')} rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="price" label={t('tuition.price')} rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createMutation.isPending}>{t('common.save')}</Button>
        </Form>
      </Modal>

      <Modal title={t('tuition.recordPayment')} open={!!paymentModal} onCancel={() => setPaymentModal(null)} footer={null}>
        <Form layout="vertical" onFinish={(v) => paymentMutation.mutate({ packageId: paymentModal, ...v })}>
          <Form.Item name="amount" label={t('tuition.amount')} rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
          </Form.Item>
          <Form.Item name="payment_date" label={t('tuition.paymentDate')} rules={[{ required: true }]} initialValue={dayjs()}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="payment_method" label={t('tuition.paymentMethod')}>
            <Select options={[{ label: 'Cash', value: 'cash' }, { label: 'Bank Transfer', value: 'bank' }, { label: 'MoMo', value: 'momo' }]} />
          </Form.Item>
          <Form.Item name="notes" label={t('common.notes')}><Input.TextArea rows={2} /></Form.Item>
          <Button type="primary" htmlType="submit" loading={paymentMutation.isPending}>{t('common.save')}</Button>
        </Form>
      </Modal>
    </div>
  );
}
