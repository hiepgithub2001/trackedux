import { Table, Tag, Card, Typography, Button, Modal, Form, InputNumber, DatePicker, Input, message, Space, Select } from 'antd';
import { PlusOutlined, DollarOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { listPackages, recordPayment } from '../../api/packages';
import PackageForm from './PackageForm';
import dayjs from 'dayjs';
import { useAuth } from '../../auth/AuthContext';

const { Title } = Typography;

export default function TuitionPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [createModal, setCreateModal] = useState(false);
  const [paymentModal, setPaymentModal] = useState(null);
  
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: packages, isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: () => listPackages({}).then((r) => r.data),
  });

  const paymentMutation = useMutation({
    mutationFn: ({ packageId, ...data }) => recordPayment(packageId, { ...data, payment_date: data.payment_date.format('YYYY-MM-DD') }),
    onSuccess: () => {
      messageApi.success('Payment recorded');
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setPaymentModal(null);
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  const columns = [
    { title: t('students.studentName'), dataIndex: 'student_name', key: 'student_name' },
    { title: t('package.class'), dataIndex: 'class_display_id', key: 'class_display_id' },
    { title: t('package.numberOfLessons'), dataIndex: 'number_of_lessons', key: 'number_of_lessons' },
    {
      title: t('tuition.remainingSessions'), dataIndex: 'remaining_sessions', key: 'remaining_sessions',
      render: (val) => <Tag color={val <= 2 ? 'red' : val <= 5 ? 'orange' : 'green'}>{val}</Tag>,
    },
    {
      title: t('tuition.paymentStatus'), dataIndex: 'payment_status', key: 'payment_status',
      render: (status) => <Tag color={status === 'paid' ? 'green' : 'red'}>{t(`tuition.${status}`)}</Tag>,
    },
    {
      title: t('common.actions'), key: 'actions',
      render: (_, record) => (
        <Space>
          {isAdmin && record.payment_status !== 'paid' && (
            <Button icon={<DollarOutlined />} size="small" onClick={(e) => { e.stopPropagation(); setPaymentModal(record.id); }}>
              {t('tuition.recordPayment')}
            </Button>
          )}
        </Space>
      ),
    },
  ];

  if (isAdmin) {
    // Insert price before payment status
    columns.splice(5, 0, {
      title: t('tuition.price'), dataIndex: 'price', key: 'price',
      render: (val) => val ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val) : '-',
    });
  }

  return (
    <div className="fade-in">
      {contextHolder}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>{t('tuition.title')}</Title>
        {isAdmin && (
          <Button id="create-package-btn" type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
            {t('package.assignPackage')}
          </Button>
        )}
      </div>

      <Card>
        <Table id="tuition-table" columns={columns} dataSource={packages || []} rowKey="id" loading={isLoading} />
      </Card>

      <PackageForm open={createModal} onCancel={() => setCreateModal(false)} />

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
