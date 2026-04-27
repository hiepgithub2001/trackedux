import { Descriptions, Card, Typography, Button, Space, Table, Tag, Modal, message } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getClass, deleteClass } from '../../api/classes';
import { useAuth } from '../../auth/AuthContext';

const { Title, Text } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ClassDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: classData, isLoading } = useQuery({
    queryKey: ['class', id],
    queryFn: () => getClass(id).then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteClass(id),
    onSuccess: () => {
      messageApi.success(t('common.deleted'));
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      navigate('/classes');
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || t('common.deleteError');
      if (err.response?.status === 409) {
        messageApi.error(t('classes.deleteBlocked'));
      } else {
        messageApi.error(msg);
      }
    },
  });

  const handleDelete = () => {
    Modal.confirm({
      title: t('classes.deleteConfirm'),
      okText: t('common.yes'),
      cancelText: t('common.no'),
      okType: 'danger',
      onOk: () => deleteMutation.mutate(),
    });
  };

  if (isLoading || !classData) return <div>{t('common.loading')}</div>;

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/classes')}>{t('common.back')}</Button>
          <Title level={3} style={{ margin: 0 }}>{classData.display_id || classData.name}</Title>
        </Space>
        {isAdmin && (
          <Space>
            <Button icon={<EditOutlined />} onClick={() => navigate(`/classes/${id}/edit`)}>{t('common.edit')}</Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleDelete} loading={deleteMutation.isPending}>{t('common.delete')}</Button>
          </Space>
        )}
      </Space>
      <Card>
        <Space style={{ marginBottom: 12 }}>
          <Title level={4} style={{ margin: 0 }}>{classData.name}</Title>
          {classData.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
        </Space>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('schedule.teacher')}>{classData.teacher_name}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.dayOfWeek')}>{DAYS[classData.day_of_week]}</Descriptions.Item>
          <Descriptions.Item label={t('common.time')}>{classData.start_time} - {classData.end_time}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.duration')}>{classData.duration_minutes} {t('schedule.minutes')}</Descriptions.Item>
          <Descriptions.Item label={t('package.lessonKind')}>{classData.lesson_kind_name || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('schedule.recurring')}>{classData.is_recurring ? '✓' : '✗'}</Descriptions.Item>
          {isAdmin && classData.tuition_fee_per_lesson !== null && (
            <Descriptions.Item label={t('classes.feePerLesson')}>
              <Text strong>{classData.tuition_fee_per_lesson?.toLocaleString('vi-VN')} VND</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
        <Title level={5} style={{ marginTop: 24 }}>{t('schedule.students')} ({classData.enrolled_count})</Title>
        <Table size="small" dataSource={classData.enrolled_students || []} rowKey="id" pagination={false}
          columns={[{ title: t('students.studentName'), dataIndex: 'name', key: 'name' }]} />
      </Card>
    </div>
  );
}
