import { Descriptions, Tag, Card, Typography, Button, Space, Tabs, Modal, Input, Select, message, Table } from 'antd';
import { EditOutlined, ArrowLeftOutlined, SwapOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { getStudent, changeStudentStatus } from '../../api/students';
import { listClasses } from '../../api/classes';
import { getStudentLedger } from '../../api/tuition';
import { useAuth } from '../../auth/useAuth';

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

  const { data: ledgerData } = useQuery({
    queryKey: ['ledger', id],
    queryFn: () => getStudentLedger(id).then((r) => r.data),
    enabled: !!id && (user?.role === 'admin' || user?.role === 'superadmin'),
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
      key: 'overview',
      label: t('common.overview', 'Overview'),
      children: (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Descriptions title={t('students.studentInfo', 'Student Info')} column={{ xs: 1, sm: 2 }} bordered>
            <Descriptions.Item label={t('students.studentName')}>{student.name}</Descriptions.Item>
            <Descriptions.Item label={t('students.nickname')}>{student.nickname || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('students.dateOfBirth')}>{student.date_of_birth || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('students.age')}>{student.age || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('students.enrolledAt')}>{student.enrolled_at}</Descriptions.Item>
            <Descriptions.Item label={t('students.enrollmentStatus')}>
              <Tag color={STATUS_COLORS[student.enrollment_status]}>
                {t(`students.status${student.enrollment_status.charAt(0).toUpperCase() + student.enrollment_status.slice(1)}`)}
              </Tag>
            </Descriptions.Item>
            {user?.role === 'admin' && (
              <Descriptions.Item label={t('tuition.balance', 'Balance')} span={2}>
                <Text strong type={(ledgerData?.current_balance || 0) >= 0 ? 'success' : 'danger'}>
                  {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(ledgerData?.current_balance || 0)}
                </Text>
              </Descriptions.Item>
            )}
            <Descriptions.Item label={t('common.notes')} span={2}>
              {student.notes || '-'}
            </Descriptions.Item>
          </Descriptions>

          <Descriptions title={t('students.contactInfo', 'Contact Info')} column={{ xs: 1, sm: 2 }} bordered>
            <Descriptions.Item label={t('students.contactName')}>{student.contact?.name || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('students.relationship')}>
              {student.contact?.relationship ? t(`students.relationship${student.contact.relationship.charAt(0).toUpperCase() + student.contact.relationship.slice(1)}`) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label={t('common.phone')}>{student.contact?.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('common.phone') + ' 2'}>{student.contact?.phone_secondary || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('common.email')}>{student.contact?.email || '-'}</Descriptions.Item>
            <Descriptions.Item label="Zalo ID">{student.contact?.zalo_id || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('common.address')} span={2}>{student.contact?.address || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('common.notes')} span={2}>{student.contact?.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Space>
      ),
    },
    {
      key: 'classes',
      label: t('classes.title', 'Enrolled Classes'),
      children: (
        <Table
          size="small"
          dataSource={(classes || []).filter(c => student.class_ids?.includes(c.id))}
          rowKey="id"
          loading={isLoadingClasses}
          scroll={{ x: 'max-content' }}
          columns={[
            { title: t('schedule.name'), dataIndex: 'name', key: 'name' },
            { title: t('schedule.teacher'), dataIndex: 'teacher_name', key: 'teacher_name' },
            { title: t('classes.lessonKind', 'Lesson Kind'), dataIndex: 'lesson_kind_name', key: 'lesson_kind_name', render: val => val || '—' },
            { title: t('common.status', 'Status'), dataIndex: 'is_active', key: 'is_active', render: val => val ? <Text type="success">Active</Text> : <Text type="secondary">Inactive</Text> },
          ]}
        />
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
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
          <Title level={3} style={{ margin: 0, wordBreak: 'break-word' }}>
            {student.name}
            {student.nickname ? ` (${student.nickname})` : ''}
          </Title>
          <Space wrap>
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
