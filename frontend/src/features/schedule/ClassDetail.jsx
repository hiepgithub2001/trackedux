import { Descriptions, Tag, Card, Typography, Button, Space, Table } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getClass } from '../../api/classes';

const { Title } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TYPE_COLORS = { individual: 'blue', pair: 'green', group: 'purple' };

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
        <Title level={3}>{classData.title || `${classData.class_type.charAt(0).toUpperCase() + classData.class_type.slice(1)} Class`}</Title>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('schedule.classType')}>
            <Tag color={TYPE_COLORS[classData.class_type]}>{t(`schedule.${classData.class_type}`)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('schedule.teacher')}>{classData.teacher_name}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.dayOfWeek')}>{DAYS[classData.day_of_week]}</Descriptions.Item>
          <Descriptions.Item label={t('common.time')}>{classData.start_time} - {classData.end_time}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.maxStudents')}>{classData.max_students}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.recurring')}>{classData.is_recurring ? '✓' : '✗'}</Descriptions.Item>
        </Descriptions>
        <Title level={5} style={{ marginTop: 24 }}>{t('schedule.students')} ({classData.enrolled_students?.length || 0})</Title>
        <Table size="small" dataSource={classData.enrolled_students || []} rowKey="id" pagination={false}
          columns={[{ title: t('students.studentName'), dataIndex: 'name', key: 'name' }]} />
      </Card>
    </div>
  );
}
