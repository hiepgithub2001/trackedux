import { Table, Tag, Card, Button, Space, Select, message } from 'antd';
import { PlusOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listBalances } from '../../api/tuition';
import PaymentForm from './PaymentForm';
import { useAuth } from '../../auth/AuthContext';

const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

const STATUS_COLORS = {
  trial: 'blue',
  active: 'green',
  paused: 'orange',
  withdrawn: 'red',
};

export default function TuitionPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [messageApi, contextHolder] = message.useMessage();
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [balanceFilter, setBalanceFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState(undefined);

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: balances, isLoading, refetch } = useQuery({
    queryKey: ['tuition-balances', balanceFilter],
    queryFn: () => listBalances({ balance_filter: balanceFilter }).then((r) => r.data),
  });

  const columns = [
    { title: t('students.studentName'), dataIndex: 'student_name', key: 'student_name', sorter: (a, b) => a.student_name.localeCompare(b.student_name) },
    {
      title: t('students.enrollmentStatus', 'Status'),
      dataIndex: 'enrollment_status',
      key: 'enrollment_status',
      width: 130,
      render: (status) => {
        if (!status) return null;
        return <Tag color={STATUS_COLORS[status]}>{t(`students.status${status.charAt(0).toUpperCase() + status.slice(1)}`)}</Tag>;
      },
      filters: [
        { text: t('students.statusTrial'), value: 'trial' },
        { text: t('students.statusActive'), value: 'active' },
        { text: t('students.statusPaused'), value: 'paused' },
        { text: t('students.statusWithdrawn'), value: 'withdrawn' },
      ],
      onFilter: (value, record) => record.enrollment_status === value,
    },
  ];

  if (isAdmin) {
    columns.push(
      {
        title: t('tuition.balance', 'Balance'),
        dataIndex: 'balance',
        key: 'balance',
        render: (val) => {
          const color = val > 0 ? 'green' : val < 0 ? 'red' : 'default';
          return <Tag color={color}>{vndFormatter.format(val || 0)}</Tag>;
        },
        sorter: (a, b) => (a.balance || 0) - (b.balance || 0),
        defaultSortOrder: 'ascend',
      },
    );
  }

  columns.push({
    title: t('common.actions'),
    key: 'actions',
    render: (_, record) => (
      <Space>
        {isAdmin && (
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/tuition/${record.student_id}`);
            }}
          >
            {t('tuition.viewLedger', 'View Ledger')}
          </Button>
        )}
      </Space>
    ),
  });

  return (
    <div className="fade-in">
      {contextHolder}
      <Card bodyStyle={{ padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
          {isAdmin && (
            <Space wrap style={{ flex: 1 }}>
              <Select
                id="balance-filter"
                value={balanceFilter}
                onChange={setBalanceFilter}
                style={{ width: '100%', minWidth: 150, maxWidth: 180 }}
                options={[
                  { value: 'all', label: t('tuition.filterAll', 'All Students') },
                  { value: 'positive', label: t('tuition.filterPositive', 'Positive Balance') },
                  { value: 'zero', label: t('tuition.filterZero', 'Zero Balance') },
                  { value: 'negative', label: t('tuition.filterNegative', 'Owing Money') },
                ]}
              />
              <Select
                id="status-filter"
                placeholder={t('students.enrollmentStatus')}
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: '100%', minWidth: 120, maxWidth: 160 }}
                allowClear
                options={[
                  { label: t('students.statusTrial'), value: 'trial' },
                  { label: t('students.statusActive'), value: 'active' },
                  { label: t('students.statusPaused'), value: 'paused' },
                  { label: t('students.statusWithdrawn'), value: 'withdrawn' },
                ]}
              />
            </Space>
          )}
          {isAdmin && (
            <Button
              id="add-payment-btn"
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setPaymentModalOpen(true)}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
            >
              {t('tuition.addPayment', 'Add Payment')}
            </Button>
          )}
        </div>
        <Table
          id="tuition-table"
          columns={columns}
          dataSource={balances ? balances.filter(b => !statusFilter || b.enrollment_status === statusFilter) : []}
          rowKey="student_id"
          loading={isLoading}
          scroll={{ x: 'max-content' }}
          onRow={(record) => ({
            onClick: () => {
              if (isAdmin) {
                navigate(`/tuition/${record.student_id}`);
              }
            },
            style: { cursor: isAdmin ? 'pointer' : 'default' },
          })}
        />
      </Card>

      <PaymentForm
        open={paymentModalOpen}
        onCancel={() => setPaymentModalOpen(false)}
        onSuccess={() => {
          setPaymentModalOpen(false);
          refetch();
          messageApi.success(t('tuition.paymentRecorded', 'Payment recorded successfully'));
        }}
      />
    </div>
  );
}
