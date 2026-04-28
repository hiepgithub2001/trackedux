import { Card, Row, Col, Statistic } from 'antd';
import { UserOutlined, CalendarOutlined, ExclamationCircleOutlined, DollarOutlined, WarningOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getDashboard } from '../../api/packages';
import { useAuth } from '../../auth/AuthContext';

const STAT_CARDS = [
  { key: 'active_students', icon: <UserOutlined />, color: '#667eea', tKey: 'dashboard.activeStudents' },
  { key: 'today_sessions', icon: <CalendarOutlined />, color: '#52c41a', tKey: 'dashboard.todaySessions' },
  { key: 'today_absences', icon: <ExclamationCircleOutlined />, color: '#faad14', tKey: 'dashboard.todayAbsences' },
  { key: 'expiring_packages', icon: <WarningOutlined />, color: '#ff4d4f', tKey: 'dashboard.expiringPackages' },
];

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const { data: metrics } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboard().then((r) => r.data),
    refetchInterval: 60000,
  });

  return (
    <div className="fade-in">
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {STAT_CARDS.map((card) => (
          <Col xs={12} sm={6} key={card.key}>
            <Card hoverable bodyStyle={{ padding: 20 }}>
              <Statistic
                title={t(card.tKey)}
                value={metrics?.[card.key] ?? '-'}
                prefix={card.icon}
                valueStyle={{ color: card.color, fontSize: 28, fontWeight: 700 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {user?.role === 'admin' && metrics?.monthly_revenue !== null && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12}>
            <Card hoverable bodyStyle={{ padding: 20 }}>
              <Statistic
                title={t('dashboard.monthlyRevenue')}
                value={metrics?.monthly_revenue ?? 0}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#667eea', fontSize: 28, fontWeight: 700 }}
                formatter={(val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val)}
              />
            </Card>
          </Col>
        </Row>
      )}

    </div>
  );
}
