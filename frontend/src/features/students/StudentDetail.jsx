import { Descriptions, Tag, Card, Typography, Button, Space, Tabs, Modal, Input, Select, message, Table, Statistic } from 'antd';
import { EditOutlined, ArrowLeftOutlined, SwapOutlined, WalletOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { getStudent, changeStudentStatus } from '../../api/students';
import { listClasses } from '../../api/classes';
import { useAuth } from '../../auth/AuthContext';

const { Title, Text } = Typography;

const STATUS_COLORS = {
  trial: 'blue',
  active: 'green',
  paused: 'orange',
  withdrawn: 'red',
};

export default function StudentDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [statusModal, setStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');
  const [messageApi, contextHolder] = message.useMessage();

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', id],
    queryFn: () => getStudent(id).then((r) => r.data),
  });


  const { data: classes, isLoading: isLoadingClasses } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
  });

  const statusMutation = useMutation({
    mutationFn: () => changeStudentStatus(id, { status: newStatus, reason: statusReason }),
    onSuccess: () => {
      messageApi.success('Status updated');
      queryClient.invalidateQueries({ queryKey: ['student', id] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setStatusModal(false);
    },
    onError: (err) => {
      messageApi.error(err.response?.data?.detail || 'Error updating status');
    },
  });

  if (isLoading || !student) {
    return <div>{t('common.loading')}</div>;
  }

  const tabItems = [
    {
      key: 'info',
      label: t('students.studentName'),
      children: (
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('students.studentName')}>{student.name}</Descriptions.Item>
          <Descriptions.Item label={t('students.nickname')}>{student.nickname || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('students.dateOfBirth')}>{student.date_of_birth || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('students.age')}>{student.age || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.notes')} span={2}>
            {student.notes || '-'}
          </Descriptions.Item>
          <Descriptions.Item label={t('students.enrolledAt')}>{student.enrolled_at}</Descriptions.Item>
          <Descriptions.Item label={t('students.enrollmentStatus')}>
            <Tag color={STATUS_COLORS[student.enrollment_status]}>
              {t(`students.status${student.enrollment_status.charAt(0).toUpperCase() + student.enrollment_status.slice(1)}`)}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'contact',
      label: t('students.contactInfo'),
      children: (
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label={t('students.contactName')}>{student.contact?.name || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('students.relationship')}>
            {student.contact?.relationship ? t(`students.relationship${student.contact.relationship.charAt(0).toUpperCase() + student.contact.relationship.slice(1)}`) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label={t('common.phone')}>{student.contact?.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.phone') + ' 2'}>{student.contact?.phone_secondary || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.email')}>{student.contact?.email || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.address')} span={2}>{student.contact?.address || '-'}</Descriptions.Item>
          <Descriptions.Item label="Zalo ID">{student.contact?.zalo_id || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('common.notes')} span={2}>{student.contact?.notes || '-'}</Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'classes',
      label: t('schedule.title'),
      children: (
        <Table
          size="small"
          dataSource={(classes || []).filter(c => student.class_ids?.includes(c.id))}
          rowKey="id"
          loading={isLoadingClasses}
          columns={[
            { title: t('schedule.name'), dataIndex: 'name', key: 'name' },
            { title: t('schedule.teacher'), dataIndex: 'teacher_name', key: 'teacher_name' },
            { title: t('schedule.dayOfWeek'), dataIndex: 'day_of_week', key: 'day_of_week', render: val => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][val] },
            { title: t('schedule.startTime'), dataIndex: 'start_time', key: 'start_time' },
            { title: t('schedule.duration'), dataIndex: 'duration_minutes', key: 'duration_minutes', render: val => `${val} min` },
          ]}
        />
      ),
    },
    {
      key: 'attendance',
      label: t('attendance.title'),
      children: <Text type="secondary">Coming soon...</Text>,
    },
    {
      key: 'tuition',
      label: t('tuition.title'),
      children: (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Statistic
            title={t('tuition.balance', 'Balance')}
            value={student.balance || 0}
            prefix={<WalletOutlined />}
            valueStyle={{ color: (student.balance || 0) >= 0 ? '#52c41a' : '#ff4d4f', fontSize: 28 }}
            formatter={(val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val)}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="fade-in">
      {contextHolder}
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')}>
          {t('common.back')}
        </Button>
      </Space>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={3} style={{ margin: 0 }}>
            {student.name}
            {student.nickname ? ` (${student.nickname})` : ''}
          </Title>
          <Space>
            {user?.role === 'admin' && (
              <Button
                id="change-status-btn"
                icon={<SwapOutlined />}
                onClick={() => setStatusModal(true)}
              >
                {t('students.changeStatus')}
              </Button>
            )}
            <Button
              id="edit-student-btn"
              type="primary"
              icon={<EditOutlined />}
              onClick={() => navigate(`/students/${id}/edit`)}
            >
              {t('common.edit')}
            </Button>
          </Space>
        </div>

        <Tabs items={tabItems} defaultActiveKey="info" />
      </Card>

      <Modal
        title={t('students.changeStatus')}
        open={statusModal}
        onOk={() => statusMutation.mutate()}
        onCancel={() => setStatusModal(false)}
        confirmLoading={statusMutation.isPending}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Select
            id="new-status-select"
            placeholder={t('students.enrollmentStatus')}
            value={newStatus || undefined}
            onChange={setNewStatus}
            style={{ width: '100%' }}
            options={[
              { label: t('students.statusTrial'), value: 'trial' },
              { label: t('students.statusActive'), value: 'active' },
              { label: t('students.statusPaused'), value: 'paused' },
              { label: t('students.statusWithdrawn'), value: 'withdrawn' },
            ]}
          />
          <Input.TextArea
            id="status-reason"
            placeholder={t('students.statusReason')}
            value={statusReason}
            onChange={(e) => setStatusReason(e.target.value)}
            rows={3}
          />
        </Space>
      </Modal>
    </div>
  );
}
