import { useState } from 'react';
import { Table, Input, Select, Button, Tag, Space, Card } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listStudents } from '../../api/students';

const STATUS_COLORS = {
  trial: 'blue',
  active: 'green',
  paused: 'orange',
  withdrawn: 'red',
};

export default function StudentList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    status: undefined,
    search: '',
    page: 1,
    page_size: 20,
    sort_by: 'name',
    sort_order: 'asc',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['students', filters],
    queryFn: () => listStudents(filters).then((r) => r.data),
  });

  const columns = [
    {
      title: t('students.studentName'),
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (text, record) => (
        <a onClick={() => navigate(`/students/${record.id}`)}>
          {text}
          {record.nickname ? ` (${record.nickname})` : ''}
        </a>
      ),
    },
    {
      title: t('students.age'),
      dataIndex: 'age',
      key: 'age',
      width: 80,
    },

    {
      title: t('students.enrollmentStatus'),
      dataIndex: 'enrollment_status',
      key: 'enrollment_status',
      width: 130,
      render: (status) => (
        <Tag color={STATUS_COLORS[status]}>{t(`students.status${status.charAt(0).toUpperCase() + status.slice(1)}`)}</Tag>
      ),
    },
    {
      title: t('students.contactName'),
      dataIndex: 'contact_name',
      key: 'contact_name',
      width: 160,
    },
    {
      title: t('students.enrolledAt'),
      dataIndex: 'enrolled_at',
      key: 'enrolled_at',
      width: 130,
      sorter: true,
    },
  ];

  const handleTableChange = (pagination, _filters, sorter) => {
    setFilters((prev) => ({
      ...prev,
      page: pagination.current,
      page_size: pagination.pageSize,
      sort_by: sorter.field || 'name',
      sort_order: sorter.order === 'descend' ? 'desc' : 'asc',
    }));
  };

  return (
    <div className="fade-in">
      <Card bodyStyle={{ padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
          <Space size="middle" wrap>
          <Input
            id="student-search"
            prefix={<SearchOutlined />}
            placeholder={t('common.search')}
            value={filters.search}
            onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }))}
            style={{ width: 240 }}
            allowClear
          />
          <Select
            id="status-filter"
            placeholder={t('students.enrollmentStatus')}
            value={filters.status}
            onChange={(val) => setFilters((prev) => ({ ...prev, status: val, page: 1 }))}
            style={{ width: 160 }}
            allowClear
            options={[
              { label: t('students.statusTrial'), value: 'trial' },
              { label: t('students.statusActive'), value: 'active' },
              { label: t('students.statusPaused'), value: 'paused' },
              { label: t('students.statusWithdrawn'), value: 'withdrawn' },
            ]}
          />
          </Space>
          <Button
            id="add-student-btn"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/students/new')}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
            }}
          >
            {t('students.addStudent')}
          </Button>
        </div>

        <Table
          id="student-table"
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          onChange={handleTableChange}
          pagination={{
            current: data?.page || 1,
            pageSize: data?.page_size || 20,
            total: data?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `${t('common.total')}: ${total}`,
          }}
          onRow={(record) => ({
            onClick: () => navigate(`/students/${record.id}`),
            style: { cursor: 'pointer' },
          })}
        />
      </Card>
    </div>
  );
}
