import { Table, Button, Space, Typography, Card, Tag } from 'antd';
import { PlusOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listClasses } from '../../api/classes';
import { useAuth } from '../../auth/AuthContext';

const { Title, Text } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ClassesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: classes, isLoading } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
  });

  const columns = [
    {
      title: t('classes.displayId'),
      dataIndex: 'display_id',
      key: 'display_id',
      render: (text, record) => <Text strong style={{ cursor: 'pointer', color: '#1890ff' }} onClick={() => navigate(`/classes/${record.id}`)}>{text || record.name}</Text>,
    },
    {
      title: t('classes.teacher'),
      dataIndex: 'teacher_name',
      key: 'teacher_name',
      sorter: (a, b) => (a.teacher_name || '').localeCompare(b.teacher_name || ''),
      filters: Array.from(new Set(classes?.map(c => c.teacher_name).filter(Boolean))).map(name => ({ text: name, value: name })),
      onFilter: (value, record) => record.teacher_name === value,
    },
    {
      title: t('package.lessonKind'),
      dataIndex: 'lesson_kind_name',
      key: 'lesson_kind_name',
      sorter: (a, b) => (a.lesson_kind_name || '').localeCompare(b.lesson_kind_name || ''),
    },
    {
      title: t('classes.weekday'),
      dataIndex: 'day_of_week',
      key: 'day_of_week',
      render: (val) => DAYS[val],
      sorter: (a, b) => a.day_of_week - b.day_of_week,
      filters: DAYS.map((day, idx) => ({ text: day, value: idx })),
      onFilter: (value, record) => record.day_of_week === value,
    },
    {
      title: t('classes.time'),
      dataIndex: 'start_time',
      key: 'start_time',
      sorter: (a, b) => a.start_time.localeCompare(b.start_time),
      render: (text, record) => `${text} - ${record.end_time}`,
    },
    {
      title: t('classes.duration'),
      dataIndex: 'duration_minutes',
      key: 'duration_minutes',
      render: (val) => `${val} ${t('schedule.minutes')}`,
    },
    {
      title: t('classes.enrolled'),
      dataIndex: 'enrolled_count',
      key: 'enrolled_count',
      sorter: (a, b) => a.enrolled_count - b.enrolled_count,
    },
  ];

  if (isAdmin) {
    columns.push({
      title: t('classes.feePerLesson'),
      dataIndex: 'tuition_fee_per_lesson',
      key: 'tuition_fee_per_lesson',
      sorter: (a, b) => (a.tuition_fee_per_lesson || 0) - (b.tuition_fee_per_lesson || 0),
      render: (val) => val ? `${val.toLocaleString('vi-VN')} VND` : '-',
    });
  }

  return (
    <div className="fade-in">
      <Space style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <Space>
          <AppstoreOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0 }}>{t('classes.title')}</Title>
        </Space>
        {isAdmin && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/classes/new')}>
            {t('classes.createClass')}
          </Button>
        )}
      </Space>

      <Card>
        <Table
          dataSource={classes}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          locale={{ emptyText: t('classes.noClasses') }}
          pagination={{ pageSize: 15 }}
          onRow={(record) => ({
            onDoubleClick: () => navigate(`/classes/${record.id}`),
          })}
        />
      </Card>
    </div>
  );
}
