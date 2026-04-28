import { Table, Tag, Card, Button, Space, Select, message } from 'antd';
import { PlusOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { listBalances } from '../../api/tuition';
import PaymentForm from './PaymentForm';
import StudentLedger from './StudentLedger';
import { useAuth } from '../../auth/AuthContext';

const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

export default function TuitionPage() {
  const { t } = useTranslation();
  const [messageApi, contextHolder] = message.useMessage();
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [balanceFilter, setBalanceFilter] = useState('all');
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [ledgerOpen, setLedgerOpen] = useState(false);

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: balances, isLoading, refetch } = useQuery({
    queryKey: ['tuition-balances', balanceFilter],
    queryFn: () => listBalances({ balance_filter: balanceFilter }).then((r) => r.data),
  });

  const columns = [
    { title: t('students.studentName'), dataIndex: 'student_name', key: 'student_name', sorter: (a, b) => a.student_name.localeCompare(b.student_name) },
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
              setSelectedStudentId(record.student_id);
              setLedgerOpen(true);
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          {isAdmin && (
            <Select
              id="balance-filter"
              value={balanceFilter}
              onChange={setBalanceFilter}
              style={{ width: 180 }}
              options={[
                { value: 'all', label: t('tuition.filterAll', 'All Students') },
                { value: 'positive', label: t('tuition.filterPositive', 'Positive Balance') },
                { value: 'zero', label: t('tuition.filterZero', 'Zero Balance') },
                { value: 'negative', label: t('tuition.filterNegative', 'Owing Money') },
              ]}
            />
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
          dataSource={balances || []}
          rowKey="student_id"
          loading={isLoading}
          onRow={(record) => ({
            onClick: () => {
              if (isAdmin) {
                setSelectedStudentId(record.student_id);
                setLedgerOpen(true);
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

      <StudentLedger
        open={ledgerOpen}
        studentId={selectedStudentId}
        onClose={() => {
          setLedgerOpen(false);
          setSelectedStudentId(null);
        }}
      />
    </div>
  );
}
