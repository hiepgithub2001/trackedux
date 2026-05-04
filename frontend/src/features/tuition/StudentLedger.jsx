import { Table, Tag, Typography, Space, Spin, DatePicker, Empty, Card, Button, Row, Col } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, ArrowLeftOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined,
  DollarOutlined, StopOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStudentLedger } from '../../api/tuition';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

const STATUS_CONFIG = {
  present: { icon: <CheckCircleOutlined />, color: '#52c41a', tagColor: 'green' },
  absent: { icon: <CloseCircleOutlined />, color: '#ff4d4f', tagColor: 'red' },
  absent_with_notice: { icon: <ExclamationCircleOutlined />, color: '#faad14', tagColor: 'gold' },
};

export default function StudentLedgerPage() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState(null);

  const params = {};
  if (dateRange && dateRange[0]) params.from_date = dateRange[0].format('YYYY-MM-DD');
  if (dateRange && dateRange[1]) params.to_date = dateRange[1].format('YYYY-MM-DD');

  const { data: ledger, isLoading } = useQuery({
    queryKey: ['student-ledger', studentId, params.from_date, params.to_date],
    queryFn: () => getStudentLedger(studentId, params).then((r) => r.data),
    enabled: !!studentId,
  });

  const columns = [
    {
      title: t('common.date', 'Date'),
      dataIndex: 'entry_date',
      key: 'entry_date',
      width: 120,
      sorter: (a, b) => a.entry_date.localeCompare(b.entry_date),
      defaultSortOrder: 'descend',
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
      filters: [
        { text: t('tuition.payment', 'Payment'), value: 'payment' },
        { text: t('tuition.classFee', 'Class Fee'), value: 'class_fee' },
      ],
      onFilter: (value, record) => record.entry_type === value,
    },
    {
      title: t('tuition.class', 'Class'),
      key: 'class',
      width: 160,
      render: (_, record) => record.entry_type === 'class_fee' ? (record.class_display_id || '-') : '-',
    },
    {
      title: t('common.status', 'Status'),
      key: 'attendance_status',
      width: 150,
      render: (_, record) => {
        if (record.entry_type !== 'class_fee' || !record.attendance_status) return '-';
        const cfg = STATUS_CONFIG[record.attendance_status] || {};
        const label =
          record.attendance_status === 'present' ? t('attendance.present', 'Present') :
          record.attendance_status === 'absent' ? t('attendance.absent', 'Absent') :
          t('attendance.absentWithNotice', 'Absent (Notified)');
        return (
          <Tag icon={cfg.icon} color={cfg.tagColor} style={{ margin: 0 }}>
            {label}
          </Tag>
        );
      },
      filters: [
        { text: t('attendance.present', 'Present'), value: 'present' },
        { text: t('attendance.absent', 'Absent'), value: 'absent' },
        { text: t('attendance.absentWithNotice', 'Absent (Notified)'), value: 'absent_with_notice' },
      ],
      onFilter: (value, record) => record.attendance_status === value,
    },
    {
      title: t('attendance.chargeFee', 'Fee'),
      key: 'charge_fee',
      width: 110,
      align: 'center',
      render: (_, record) => {
        if (record.entry_type !== 'class_fee') return '-';
        if (record.charge_fee === true) {
          return <Tag icon={<DollarOutlined />} color="green" style={{ margin: 0 }}>{t('attendance.charge', 'Charge')}</Tag>;
        }
        if (record.charge_fee === false) {
          return <Tag icon={<StopOutlined />} color="red" style={{ margin: 0 }}>{t('attendance.noCharge', 'No Charge')}</Tag>;
        }
        return '-';
      },
    },
    {
      title: t('common.notes', 'Notes'),
      key: 'notes',
      ellipsis: true,
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
      sorter: (a, b) => (a.amount || 0) - (b.amount || 0),
      render: (val, record) => (
        <Text
          strong
          style={{ color: record.entry_type === 'payment' ? '#52c41a' : '#fa541c', fontSize: 14 }}
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
        <Text strong style={{ color: val >= 0 ? '#52c41a' : '#ff4d4f', fontSize: 14 }}>
          {vndFormatter.format(val || 0)}
        </Text>
      ),
    },
  ];

  const balanceColor = ledger?.current_balance >= 0 ? '#52c41a' : '#ff4d4f';

  return (
    <div className="fade-in">
      <Space style={{ marginBottom: 20 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tuition')}>
          {t('common.back')}
        </Button>
      </Space>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : ledger ? (
        <>
          {/* Summary header */}
          <Card
            style={{
              marginBottom: 20,
              background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              border: 'none',
            }}
          >
            <Row gutter={24} align="middle">
              <Col flex="auto">
                <Title level={3} style={{ margin: 0 }}>
                  {ledger.student_name}
                </Title>
                <Text type="secondary">{t('tuition.studentLedger', 'Student Ledger')}</Text>
              </Col>
              <Col>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>{t('tuition.totalPaid', 'Total Paid')}</Text>
                  <div style={{ fontSize: 20, color: '#52c41a', fontWeight: 600 }}>
                    {vndFormatter.format(ledger.total_paid || 0)}
                  </div>
                </div>
              </Col>
              <Col>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>{t('tuition.totalFees', 'Total Fees')}</Text>
                  <div style={{ fontSize: 20, color: '#fa8c16', fontWeight: 600 }}>
                    {vndFormatter.format(ledger.total_fees || 0)}
                  </div>
                </div>
              </Col>
              <Col>
                <div style={{ textAlign: 'right' }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>{t('tuition.balance', 'Balance')}</Text>
                  <div style={{ fontSize: 28, color: balanceColor, fontWeight: 700, lineHeight: 1.2 }}>
                    {vndFormatter.format(ledger.current_balance || 0)}
                  </div>
                </div>
              </Col>
            </Row>
          </Card>

          {/* Date filter */}
          <Card bodyStyle={{ padding: '12px 16px' }} style={{ marginBottom: 16 }}>
            <Space>
              <Text strong>{t('common.filter', 'Filter')}:</Text>
              <RangePicker onChange={setDateRange} />
            </Space>
          </Card>

          {/* Ledger table */}
          <Card bodyStyle={{ padding: 0 }}>
            {ledger.entries?.length > 0 ? (
              <Table
                columns={columns}
                dataSource={ledger.entries}
                rowKey="id"
                pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }}
                size="middle"
                scroll={{ x: 'max-content' }}
              />
            ) : (
              <div style={{ padding: 40 }}>
                <Empty description={t('common.noData', 'No data')} />
              </div>
            )}
          </Card>
        </>
      ) : (
        <Card>
          <Empty description={t('common.noData', 'No data')} />
        </Card>
      )}
    </div>
  );
}
