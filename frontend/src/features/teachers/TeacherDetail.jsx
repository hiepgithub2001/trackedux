import { Descriptions, Tag, Card, Typography, Button, Space } from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getTeacher } from '../../api/teachers';

const { Title } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function TeacherDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: teacher, isLoading } = useQuery({
    queryKey: ['teacher', id],
    queryFn: () => getTeacher(id).then((r) => r.data),
  });

  if (isLoading || !teacher) return <div>{t('common.loading')}</div>;

  return (
    <div className="fade-in">
      <Space style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/teachers')}>{t('common.back')}</Button>
        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/teachers/${id}/edit`)}>
          {t('common.edit')}
        </Button>
      </Space>
      <Card>
        <Title level={3}>{teacher.full_name}</Title>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('common.phone')}>{teacher.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.email')}>{teacher.email || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.status')}>
            <Tag color={teacher.is_active ? 'green' : 'red'}>{teacher.is_active ? t('teachers.active') : t('teachers.inactive')}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('common.notes')}>{teacher.notes || '-'}</Descriptions.Item>
        </Descriptions>
        {teacher.availability?.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <Title level={5}>{t('teachers.availability')}</Title>
            {teacher.availability.map((slot, i) => (
              <Tag key={i} color="blue" style={{ marginBottom: 4 }}>
                {DAYS[slot.day_of_week]} {slot.start_time} - {slot.end_time}
              </Tag>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
