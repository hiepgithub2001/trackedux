import { useState } from 'react';
import { Card, Table, Tag, Button, message, Space, Radio, Row, Col, Pagination, Modal } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getWeeklySchedule } from '../../api/classes';
import { markBatchAttendance, getSessionAttendance } from '../../api/attendance';
import dayjs from 'dayjs';

const STATUS_ICONS = {
  present: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  absent: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
  absent_with_notice: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
};

export default function AttendancePage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [selectedSession, setSelectedSession] = useState(null);
  const [attendanceData, setAttendanceData] = useState({});

  const { data: scheduleData } = useQuery({
    queryKey: ['schedule'],
    queryFn: () => getWeeklySchedule({}).then((r) => r.data),
  });

  useQuery({
    queryKey: ['attendance', selectedSession?.id, selectedSession?.date],
    queryFn: () => getSessionAttendance(selectedSession.id, selectedSession.date).then((r) => r.data),
    enabled: !!selectedSession,
  });

  const mutation = useMutation({
    mutationFn: (data) => markBatchAttendance(data),
    onSuccess: (res) => {
      messageApi.success('Attendance marked');
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      queryClient.invalidateQueries({ queryKey: ['student'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
      const renewals = res.data.records?.filter((r) => r.renewal_reminder_triggered);
      if (renewals?.length > 0) {
        messageApi.warning(`${renewals.length} student(s) have ≤2 sessions remaining`);
      }
      setSelectedSession(null);
    },
    onError: (err) => messageApi.error(err.response?.data?.detail || 'Error'),
  });

  const handleMark = () => {
    if (!selectedSession) return;
    const records = Object.entries(attendanceData).map(([studentId, status]) => ({ student_id: studentId, status }));
    mutation.mutate({ class_session_id: selectedSession.id, session_date: selectedSession.date, records });
  };

  const now = dayjs();
  const todayDateStr = now.format('YYYY-MM-DD');
  const todaySessions = (scheduleData?.sessions || []).filter((s) => s.date === todayDateStr);
  
  const runningSessions = todaySessions.filter((s) => {
    const start = dayjs(`${s.date}T${s.start_time}`);
    const end = dayjs(`${s.date}T${s.end_time}`);
    return (now.isAfter(start) || now.isSame(start)) && now.isBefore(end);
  });

  const pastSessions = (scheduleData?.sessions || [])
    .filter((s) => {
      const end = dayjs(`${s.date}T${s.end_time}`);
      return now.isAfter(end);
    })
    .sort((a, b) => dayjs(`${b.date}T${b.start_time}`).valueOf() - dayjs(`${a.date}T${a.start_time}`).valueOf());

  const [pastPage, setPastPage] = useState(1);
  const pastPageSize = 5;
  const paginatedPast = pastSessions.slice((pastPage - 1) * pastPageSize, pastPage * pastPageSize);

  return (
    <div className="fade-in">
      {contextHolder}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={12}>
          <Card title={t('dashboard.runningSessions', 'Running Sessions')} style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {runningSessions.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {runningSessions.map((session) => (
                <Card key={session.id} size="small" hoverable onClick={() => setSelectedSession(session)}
                  style={{ border: selectedSession?.id === session.id ? '2px solid #667eea' : undefined, background: '#e6f4ff' }}>
                  <Space wrap>
                    <Tag color="processing">{session.start_time} - {session.end_time}</Tag>
                    {session.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
                    <span style={{ fontWeight: 600 }}>{session.name}</span>
                    <span>({session.teacher.full_name})</span>
                    <Tag>{session.students.length} students</Tag>
                  </Space>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title={t('attendance.todaySessions')} style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {todaySessions.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {todaySessions.map((session) => (
                <Card key={session.id} size="small" hoverable onClick={() => setSelectedSession(session)}
                  style={{ border: selectedSession?.id === session.id ? '2px solid #667eea' : undefined }}>
                  <Space wrap>
                    <Tag color="blue">{session.start_time} - {session.end_time}</Tag>
                    {session.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
                    <span style={{ fontWeight: 500 }}>{session.name}</span>
                    <span>({session.teacher.full_name})</span>
                    <Tag>{session.students.length} students</Tag>
                  </Space>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24}>
          <Card title={t('attendance.pastSessions', 'Past Sessions')}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {paginatedPast.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {paginatedPast.map((session) => (
                <Card key={session.id} size="small" hoverable onClick={() => setSelectedSession(session)}
                  style={{ border: selectedSession?.id === session.id ? '2px solid #667eea' : undefined }}>
                  <Space wrap>
                    <Tag color="default">{session.date}</Tag>
                    <Tag color="default">{session.start_time} - {session.end_time}</Tag>
                    {session.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
                    <span style={{ fontWeight: 500 }}>{session.name}</span>
                    <span>({session.teacher.full_name})</span>
                    <Tag>{session.students.length} students</Tag>
                  </Space>
                </Card>
              ))}
              {pastSessions.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                  <Pagination 
                    current={pastPage} 
                    pageSize={pastPageSize} 
                    total={pastSessions.length} 
                    onChange={setPastPage} 
                  />
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Modal
        title={selectedSession ? `${t('attendance.markAttendance')}: ${selectedSession.name}` : ''}
        centered
        width={600}
        onCancel={() => setSelectedSession(null)}
        open={!!selectedSession}
        footer={
          <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={() => setSelectedSession(null)}>{t('common.cancel')}</Button>
            <Button type="primary" onClick={handleMark} loading={mutation.isPending} style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
              {t('common.save')}
            </Button>
          </Space>
        }
      >
        {selectedSession && (
          <Table
            dataSource={selectedSession.students}
            rowKey="id"
            pagination={false}
            columns={[
              { title: t('students.studentName'), dataIndex: 'name', key: 'name' },
              {
                title: t('common.status'), key: 'status',
                render: (_, record) => (
                  <Radio.Group value={attendanceData[record.id]} onChange={(e) => setAttendanceData((prev) => ({ ...prev, [record.id]: e.target.value }))}>
                    <Radio.Button value="present">{STATUS_ICONS.present} {t('attendance.present')}</Radio.Button>
                    <Radio.Button value="absent">{STATUS_ICONS.absent} {t('attendance.absent')}</Radio.Button>
                    <Radio.Button value="absent_with_notice">{STATUS_ICONS.absent_with_notice} {t('attendance.absentWithNotice')}</Radio.Button>
                  </Radio.Group>
                ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
}
