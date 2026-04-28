import { Drawer, Table, Tag, Typography, Space, Spin, DatePicker, Empty } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { getStudentLedger } from '../../api/tuition';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

export default function StudentLedger({ open, studentId, onClose }) {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState(null);

  const params = {};
  if (dateRange && dateRange[0]) params.from_date = dateRange[0].format('YYYY-MM-DD');
  if (dateRange && dateRange[1]) params.to_date = dateRange[1].format('YYYY-MM-DD');

  const { data: ledger, isLoading } = useQuery({
    queryKey: ['student-ledger', studentId, params.from_date, params.to_date],
    queryFn: () => getStudentLedger(studentId, params).then((r) => r.data),
    enabled: open && !!studentId,
  });

  const columns = [
    {
      title: t('common.date', 'Date'),
      dataIndex: 'entry_date',
      key: 'entry_date',
      width: 120,
    },
    {
      title: t('tuition.type', 'Type'),
      dataIndex: 'entry_type',
      key: 'type',
      width: 130,
      render: (type) => (
        <Space size="small">
          {type === 'payment' ? (
            <ArrowUpOutlined style={{ color: '#52c41a' }} />
          ) : (
            <ArrowDownOutlined style={{ color: '#fa541c' }} />
          )}
          {type === 'payment' ? (
            <Tag color="green" style={{ margin: 0 }}>{t('tuition.payment', 'Payment')}</Tag>
          ) : (
            <Tag color="orange" style={{ margin: 0 }}>{t('tuition.classFee', 'Class Fee')}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: t('tuition.class', 'Class'),
      key: 'class',
      render: (_, record) => record.entry_type === 'class_fee' ? (record.class_display_id || '-') : '-',
    },
    {
      title: t('common.notes', 'Notes'),
      key: 'notes',
      render: (_, record) => {
        if (record.entry_type === 'payment') {
          return record.description && record.description !== 'Payment' ? record.description : '-';
        }
        return '-';
      },
    },
    {
      title: t('tuition.amount', 'Amount'),
      dataIndex: 'amount',
      key: 'amount',
      width: 160,
      align: 'right',
      render: (val, record) => (
        <Text
          strong
          style={{ color: record.entry_type === 'payment' ? '#52c41a' : '#fa541c' }}
        >
          {record.entry_type === 'payment' ? '+' : '-'}
          {vndFormatter.format(val || 0)}
        </Text>
      ),
    },
    {
      title: t('tuition.balanceAfter', 'Balance After'),
      dataIndex: 'balance_after',
      key: 'balance_after',
      width: 160,
      align: 'right',
      render: (val) => (
        <Text strong style={{ color: val >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {vndFormatter.format(val || 0)}
        </Text>
      ),
    },
  ];

  const balanceColor = ledger?.current_balance >= 0 ? '#52c41a' : '#ff4d4f';

  return (
    <Drawer
      title={t('tuition.studentLedger', 'Student Ledger')}
      open={open}
      onClose={onClose}
      width={720}
      destroyOnClose
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      ) : ledger ? (
        <>
          <div
            style={{
              marginBottom: 20,
              padding: '16px 20px',
              borderRadius: 10,
              background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <Title level={4} style={{ margin: 0 }}>
                {ledger.student_name}
              </Title>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
              <div>
                <Text type="secondary">{t('tuition.totalPaid', 'Total Paid')}</Text>
                <div style={{ fontSize: 18, color: '#52c41a', fontWeight: 600 }}>
                  {vndFormatter.format(ledger.total_paid || 0)}
                </div>
              </div>
              <div>
                <Text type="secondary">{t('tuition.totalFees', 'Total Fees')}</Text>
                <div style={{ fontSize: 18, color: '#fa8c16', fontWeight: 600 }}>
                  {vndFormatter.format(ledger.total_fees || 0)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <Text type="secondary">{t('tuition.balance', 'Balance')}</Text>
                <div style={{ fontSize: 24, color: balanceColor, fontWeight: 700, lineHeight: 1 }}>
                  {vndFormatter.format(ledger.current_balance || 0)}
                </div>
              </div>
            </div>
          </div>

          <Space style={{ marginBottom: 16 }}>
            <RangePicker onChange={setDateRange} />
          </Space>

          {ledger.entries?.length > 0 ? (
            <Table
              columns={columns}
              dataSource={ledger.entries}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              size="small"
            />
          ) : (
            <Empty description={t('common.noData', 'No data')} />
          )}
        </>
      ) : (
        <Empty description={t('common.noData', 'No data')} />
      )}
    </Drawer>
  );
}
