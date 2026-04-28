import { Card, Statistic, Alert, Spin, Row, Col } from 'antd';
import { DollarOutlined, BookOutlined, WalletOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getChildBalance } from '../../api/tuition';

const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

/**
 * Parent-facing tuition summary card for a single child.
 * Shows total paid, classes attended, and current balance.
 * No per-lesson fee amounts are exposed.
 */
export default function ChildTuitionCard({ studentId }) {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ['child-balance', studentId],
    queryFn: () => getChildBalance(studentId).then((r) => r.data),
    enabled: !!studentId,
  });

  if (isLoading) {
    return (
      <Card style={{ textAlign: 'center', padding: 40 }}>
        <Spin />
      </Card>
    );
  }

  if (!data) return null;

  const balanceColor = data.current_balance >= 0 ? '#52c41a' : '#ff4d4f';

  return (
    <Card title={t('portal.childTuition', 'Tuition Info')} style={{ marginBottom: 16 }}>
      {data.current_balance < 0 && (
        <Alert
          type="warning"
          showIcon
          message={t('tuition.paymentNeeded', 'Additional payment needed')}
          style={{ marginBottom: 16 }}
        />
      )}
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title={t('tuition.totalPaid', 'Total Paid')}
            value={data.total_paid || 0}
            formatter={(val) => vndFormatter.format(val)}
            prefix={<DollarOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title={t('attendance.title', 'Classes Attended')}
            value={data.classes_attended || 0}
            prefix={<BookOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title={t('tuition.balance', 'Balance')}
            value={data.current_balance || 0}
            formatter={(val) => vndFormatter.format(val)}
            prefix={<WalletOutlined />}
            valueStyle={{ color: balanceColor }}
          />
        </Col>
      </Row>
    </Card>
  );
}
