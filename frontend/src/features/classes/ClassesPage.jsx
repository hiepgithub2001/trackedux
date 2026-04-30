import { Table, Button, Space, Typography, Card, Input } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listClasses } from '../../api/classes';
import { useAuth } from '../../auth/AuthContext';

const { Text } = Typography;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ClassesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState('');
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data: classes, isLoading } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
  });

  const columns = [
    {
      title: t('common.name', 'Class Name'),
      dataIndex: 'name',
      key: 'name',
      render: (text) => <Text strong style={{ color: '#1890ff' }}>{text}</Text>,
      sorter: (a, b) => (a.name || '').localeCompare(b.name || ''),
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
      title: t('classes.lessonKind', 'Lesson Kind'),
      dataIndex: 'lesson_kind_name',
      key: 'lesson_kind_name',
      sorter: (a, b) => (a.lesson_kind_name || '').localeCompare(b.lesson_kind_name || ''),
    },
    {
      title: t('classes.enrolled', 'Students'),
      dataIndex: 'enrolled_count',
      key: 'enrolled_count',
      sorter: (a, b) => a.enrolled_count - b.enrolled_count,
      render: (val) => `${val ?? 0} students`,
    },
    {
      title: t('classes.status', 'Status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (val) => val ? <Text type="success">Active</Text> : <Text type="secondary">Inactive</Text>,
      filters: [{ text: 'Active', value: true }, { text: 'Inactive', value: false }],
      onFilter: (value, record) => record.is_active === value,
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

  const filteredClasses = classes?.filter(c => 
    (c.name || '').toLowerCase().includes(searchText.toLowerCase()) || 
    (c.display_id || '').toLowerCase().includes(searchText.toLowerCase()) ||
    (c.teacher_name || '').toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div className="fade-in">
      <Card bodyStyle={{ padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
          <Space size="middle" wrap>
            <Input
              id="class-search"
              prefix={<SearchOutlined />}
              placeholder={t('common.search')}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 240 }}
              allowClear
            />
          </Space>
          {isAdmin && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/classes/new')}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
              {t('classes.createClass')}
            </Button>
          )}
        </div>
        <Table
          dataSource={filteredClasses}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          locale={{ emptyText: t('classes.noClasses') }}
          pagination={{ pageSize: 15 }}
          onRow={(record) => ({
            onClick: () => navigate(`/classes/${record.id}`),
            style: { cursor: 'pointer' },
          })}
        />
      </Card>
    </div>
  );
}
