import { Descriptions, Card, Typography, Button, Space, Table, Tag, Modal, message, Divider, Badge } from 'antd';
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { getClass, deleteClass } from '../../api/classes';
import { listLessons, deleteLesson } from '../../api/lessons';
import { useAuth } from '../../auth/AuthContext';
import LessonForm from '../lessons/LessonForm';

const { Title, Text } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ClassDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [editingLessonId, setEditingLessonId] = useState(null);

  const { data: classData, isLoading } = useQuery({
    queryKey: ['class', id],
    queryFn: () => getClass(id).then((r) => r.data),
  });

  const { data: lessons = [] } = useQuery({
    queryKey: ['lessons', { class_id: id }],
    queryFn: () => listLessons({ class_id: id }).then((r) => r.data),
    enabled: !!id,
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
      messageApi.error(msg);
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

  const deleteLessonMutation = useMutation({
    mutationFn: (lessonId) => deleteLesson(lessonId),
    onSuccess: () => {
      messageApi.success(t('common.deleted'));
      queryClient.invalidateQueries({ queryKey: ['lessons', { class_id: id }] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || t('common.deleteError');
      messageApi.error(msg);
    },
  });

  const handleDeleteLesson = (lessonId) => {
    Modal.confirm({
      title: t('lessons.deleteConfirm', 'Are you sure you want to delete this lesson?'),
      okText: t('common.yes'),
      cancelText: t('common.no'),
      okType: 'danger',
      onOk: () => deleteLessonMutation.mutate(lessonId),
    });
  };

  if (isLoading || !classData) return <div>{t('common.loading')}</div>;

  const lessonColumns = [
    {
      title: t('lessons.type', 'Type'),
      key: 'type',
      width: 110,
      render: (_, l) => l.rrule
        ? <Tag color="blue">{t('lessons.recurring', 'Recurring')}</Tag>
        : <Tag color="orange">{t('lessons.oneOff', 'One-off')}</Tag>,
    },
    {
      title: t('common.time', 'Time'),
      key: 'time',
      render: (_, l) => {
        if (l.specific_date) return `${l.specific_date} ${l.start_time}`;
        if (l.day_of_week !== null && l.day_of_week !== undefined) {
          return `${DAYS[l.day_of_week]}, ${l.start_time}`;
        }
        return l.start_time;
      },
    },
    {
      title: t('lessons.duration', 'Duration'),
      key: 'duration',
      render: (_, l) => `${l.duration_minutes} min`,
    },
    {
      title: t('lessons.title', 'Title'),
      dataIndex: 'title',
      key: 'title',
      render: (v) => v || <Text type="secondary">—</Text>,
    },
    {
      title: t('common.status', 'Status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => <Badge status={v ? 'success' : 'default'} text={v ? 'Active' : 'Inactive'} />,
    },
    ...(isAdmin ? [{
      title: t('common.actions', 'Actions'),
      key: 'actions',
      render: (_, l) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => setEditingLessonId(l.id)}>
            {t('common.edit', 'Edit')}
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteLesson(l.id)}>
            {t('common.delete', 'Delete')}
          </Button>
        </Space>
      ),
    }] : []),
  ];

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/classes')}>{t('common.back')}</Button>
          <Title level={3} style={{ margin: 0 }}>{classData.name}</Title>
        </Space>
        {isAdmin && (
          <Space>
            <Button icon={<EditOutlined />} onClick={() => navigate(`/classes/${id}/edit`)}>{t('common.edit')}</Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleDelete} loading={deleteMutation.isPending}>{t('common.delete')}</Button>
          </Space>
        )}
      </Space>

      <Card>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('schedule.teacher')}>{classData.teacher_name}</Descriptions.Item>
          <Descriptions.Item label={t('classes.lessonKind', 'Lesson Kind')}>{classData.lesson_kind_name || '—'}</Descriptions.Item>
          <Descriptions.Item label={t('common.status', 'Status')}>
            {classData.is_active ? <Text type="success">Active</Text> : <Text type="secondary">Inactive</Text>}
          </Descriptions.Item>
          {isAdmin && classData.tuition_fee_per_lesson !== null && (
            <Descriptions.Item label={t('classes.feePerLesson')}>
              <Text strong>{classData.tuition_fee_per_lesson?.toLocaleString('vi-VN')} VND</Text>
            </Descriptions.Item>
          )}
        </Descriptions>

        <Divider />

        {/* Lessons section */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <Title level={5} style={{ margin: 0 }}>{t('lessons.lessons', 'Lessons')} ({lessons.length})</Title>
          {isAdmin && (
            <Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => setShowLessonForm(true)}>
              {t('lessons.addLesson', 'Add Lesson')}
            </Button>
          )}
        </div>
        <Table
          size="small"
          dataSource={lessons}
          rowKey="id"
          columns={lessonColumns}
          pagination={false}
          locale={{ emptyText: t('lessons.noLessons', 'No lessons yet. Add one to start scheduling.') }}
        />

        <Divider />

        {/* Enrolled students */}
        <Title level={5} style={{ marginTop: 0 }}>{t('schedule.students')} ({classData.enrolled_count})</Title>
        <Table
          size="small"
          dataSource={classData.enrolled_students || []}
          rowKey="id"
          pagination={false}
          columns={[{ title: t('students.studentName'), dataIndex: 'name', key: 'name' }]}
        />
      </Card>

      {/* Inline LessonForm modal */}
      {(showLessonForm || editingLessonId) && (
        <LessonForm
          open={!!(showLessonForm || editingLessonId)}
          lessonId={editingLessonId}
          defaultClassId={id}
          onClose={() => { setShowLessonForm(false); setEditingLessonId(null); }}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['lessons', { class_id: id }] });
            queryClient.invalidateQueries({ queryKey: ['schedule'] });
            setShowLessonForm(false);
            setEditingLessonId(null);
          }}
        />
      )}
    </div>
  );
}
