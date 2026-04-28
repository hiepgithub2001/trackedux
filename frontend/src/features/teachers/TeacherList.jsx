import { Table, Button, Tag, Card } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listTeachers } from '../../api/teachers';

export default function TeacherList() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: teachers, isLoading } = useQuery({
    queryKey: ['teachers'],
    queryFn: () => listTeachers().then((r) => r.data),
  });

  const columns = [
    { title: t('teachers.teacherName'), dataIndex: 'full_name', key: 'full_name' },
    { title: t('common.phone'), dataIndex: 'phone', key: 'phone' },
    { title: t('common.email'), dataIndex: 'email', key: 'email' },
    {
      title: t('common.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => <Tag color={active ? 'green' : 'red'}>{active ? t('teachers.active') : t('teachers.inactive')}</Tag>,
    },
  ];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 24 }}>
        <Button id="add-teacher-btn" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/teachers/new')}
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
          {t('teachers.addTeacher')}
        </Button>
      </div>
      <Card>
        <Table id="teacher-table" columns={columns} dataSource={teachers || []} rowKey="id" loading={isLoading}
          onRow={(record) => ({ onClick: () => navigate(`/teachers/${record.id}`), style: { cursor: 'pointer' } })} />
      </Card>
    </div>
  );
}
