import { Descriptions, Tag, Card, Typography, Button, Space, Modal, message } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getTeacher, deleteTeacher } from '../../api/teachers';
import { useAuth } from '../../auth/useAuth';

const { Title } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function TeacherDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [messageApi, contextHolder] = message.useMessage();

  const { data: teacher, isLoading } = useQuery({
    queryKey: ['teacher', id],
    queryFn: () => getTeacher(id).then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTeacher(id),
    onSuccess: () => {
      messageApi.success(t('common.deletedSuccess', 'Deleted successfully'));
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['attendance-weekly'] });
      queryClient.invalidateQueries({ queryKey: ['past-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate('/teachers');
    },
    onError: (err) => {
      messageApi.error(err.response?.data?.detail || t('common.errorDeleting', 'Error deleting'));
    },
  });

  const handleDelete = () => {
    Modal.confirm({
      title: t('common.confirmDelete', 'Are you sure you want to delete this?'),
      content: t('common.cannotUndo', 'This action cannot be undone.'),
      okText: t('common.yes', 'Yes'),
      okType: 'danger',
      cancelText: t('common.no', 'No'),
      onOk: () => deleteMutation.mutate(),
    });
  };

  if (isLoading || !teacher) return <div>{t('common.loading')}</div>;

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/teachers')}>{t('common.back')}</Button>
        <Space>
          {user?.role === 'admin' && (
            <Button
              id="delete-teacher-btn"
              danger
              icon={<DeleteOutlined />}
              onClick={handleDelete}
            >
              {t('common.delete', 'Delete')}
            </Button>
          )}
          <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/teachers/${id}/edit`)}>
            {t('common.edit')}
          </Button>
        </Space>
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
