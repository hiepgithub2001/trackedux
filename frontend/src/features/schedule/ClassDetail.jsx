import { Descriptions, Card, Typography, Button, Space, Table, Tag } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getClass } from '../../api/classes';

const { Title } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ClassDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: classData, isLoading } = useQuery({
    queryKey: ['class', id],
    queryFn: () => getClass(id).then((r) => r.data),
  });

  if (isLoading || !classData) return <div>{t('common.loading')}</div>;

  return (
    <div className="fade-in">
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/schedule')}>{t('common.back')}</Button>
      </Space>
      <Card>
        <Space style={{ marginBottom: 12 }}>
          <Title level={3} style={{ margin: 0 }}>{classData.name}</Title>
          {classData.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
        </Space>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('schedule.teacher')}>{classData.teacher_name}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.dayOfWeek')}>{DAYS[classData.day_of_week]}</Descriptions.Item>
          <Descriptions.Item label={t('common.time')}>{classData.start_time} - {classData.end_time}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.duration')}>{classData.duration_minutes} {t('schedule.minutes')}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.recurring')}>{classData.is_recurring ? '✓' : '✗'}</Descriptions.Item>
        </Descriptions>
        <Title level={5} style={{ marginTop: 24 }}>{t('schedule.students')} ({classData.enrolled_students?.length || 0})</Title>
        <Table size="small" dataSource={classData.enrolled_students || []} rowKey="id" pagination={false}
          columns={[{ title: t('students.studentName'), dataIndex: 'name', key: 'name' }]} />
      </Card>
    </div>
  );
}
