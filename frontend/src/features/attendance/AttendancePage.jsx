import { useState, useCallback } from 'react';
import { Card, Table, Tag, Button, message, Space, Radio, Row, Col, Pagination, Modal } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined, DollarOutlined, StopOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getPastSessions } from '../../api/classes';
import { markBatchAttendance, getSessionAttendance, getAttendanceWeekly } from '../../api/attendance';
import dayjs from 'dayjs';

const PAST_PAGE_SIZE = 5;

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
  const [chargeFeeData, setChargeFeeData] = useState({});

  const openSession = useCallback((session) => {
    setAttendanceData({});
    setChargeFeeData({});
    setSelectedSession(session);
  }, []);

  const closeSession = useCallback(() => {
    setSelectedSession(null);
    setAttendanceData({});
    setChargeFeeData({});
  }, []);

  const { data: scheduleData } = useQuery({
    queryKey: ['attendance-weekly'],
    queryFn: () => getAttendanceWeekly({}).then((r) => r.data),
  });

  const [pastPage, setPastPage] = useState(1);
  const { data: pastData } = useQuery({
    queryKey: ['past-sessions', pastPage],
    queryFn: () =>
      getPastSessions({
        limit: PAST_PAGE_SIZE,
        offset: (pastPage - 1) * PAST_PAGE_SIZE,
      }).then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  const { data: savedRecords } = useQuery({
    queryKey: ['attendance', selectedSession?.lesson_id, selectedSession?.original_date || selectedSession?.date],
    queryFn: () => getSessionAttendance(selectedSession.lesson_id, selectedSession.original_date || selectedSession.date).then((r) => {
      const records = Array.isArray(r.data) ? r.data : (r.data?.records ?? r.data ?? []);
      return records;
    }),
    enabled: !!selectedSession,
    staleTime: 0, // always re-fetch when session opens — never show stale charge_fee values
  });

  const getDerivedStatus = (studentId) => {
    if (attendanceData[studentId] !== undefined) return attendanceData[studentId];
    if (savedRecords && savedRecords.length > 0) {
      const rec = savedRecords.find(r => r.student_id === studentId);
      if (rec) return rec.status;
    }
    return 'present'; // default
  };

  const getDerivedChargeFee = (studentId) => {
    // Returns boolean for use in handleMark
    if (chargeFeeData[studentId] !== undefined) return chargeFeeData[studentId];
    if (savedRecords && savedRecords.length > 0) {
      const rec = savedRecords.find(r => r.student_id === studentId);
      if (rec && rec.charge_fee !== undefined) return rec.charge_fee;
    }
    return true; // default
  };

  // Returns string value for Radio.Group (avoids Ant Design boolean coercion bug)
  const getChargeRadioValue = (studentId) => getDerivedChargeFee(studentId) ? 'charge' : 'nocharge';

  const mutation = useMutation({
    mutationFn: (data) => markBatchAttendance(data),
    onSuccess: () => {
      messageApi.success('Attendance marked');
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['attendance-weekly'] });
      queryClient.invalidateQueries({ queryKey: ['past-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['tuition-balances'] });
      queryClient.invalidateQueries({ queryKey: ['student-ledger'] });
      closeSession();
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? JSON.stringify(detail) : 'Error saving attendance');
      messageApi.error(msg);
    },
  });

  const handleMark = () => {
    if (!selectedSession) return;
    const records = selectedSession.students.map((student) => ({
      student_id: student.id,
      status: getDerivedStatus(student.id),
      charge_fee: getDerivedChargeFee(student.id),
    }));
    mutation.mutate({ lesson_id: selectedSession.lesson_id, session_date: selectedSession.original_date || selectedSession.date, records });
  };

  const now = dayjs();
  const todayDateStr = now.format('YYYY-MM-DD');

  const allSessions = scheduleData?.sessions || [];

  const runningSessions = allSessions.filter((s) => {
    const start = dayjs(`${s.date}T${s.start_time}`);
    const end = dayjs(`${s.date}T${s.end_time}`);
    return (now.isAfter(start) || now.isSame(start)) && now.isBefore(end);
  });

  const pendingSessions = allSessions.filter((s) => !s.attendance_marked)
    .sort((a, b) => dayjs(`${a.date}T${a.start_time}`).valueOf() - dayjs(`${b.date}T${b.start_time}`).valueOf());

  const todaySessions = allSessions.filter((s) => {
    if (s.date !== todayDateStr) return false;
    const start = dayjs(`${s.date}T${s.start_time}`);
    const end = dayjs(`${s.date}T${s.end_time}`);
    const isRunning = (now.isAfter(start) || now.isSame(start)) && now.isBefore(end);
    return !isRunning;
  });

  const paginatedPast = pastData?.sessions ?? [];
  const pastTotal = pastData?.total ?? 0;

  const [pendingPage, setPendingPage] = useState(1);
  const pageSize = 5;
  const paginatedPending = pendingSessions.slice((pendingPage - 1) * pageSize, pendingPage * pageSize);

  const sortedAllSessions = [...allSessions].sort((a, b) => {
    const dateA = a.date || '';
    const dateB = b.date || '';
    if (dateA !== dateB) return dateA.localeCompare(dateB);
    return (a.start_time || '').localeCompare(b.start_time || '');
  });

  const [allWeekPage, setAllWeekPage] = useState(1);
  const paginatedAllWeek = sortedAllSessions.slice((allWeekPage - 1) * pageSize, allWeekPage * pageSize);

  const SessionCard = ({ session, isHighlighted }) => (
    <Card
      size="small"
      hoverable
      onClick={() => openSession(session)}
      style={{
        border: selectedSession?.id === session.id ? '2px solid #667eea' : undefined,
        background: isHighlighted ? '#e6f4ff' : undefined,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space wrap>
          <Tag color={isHighlighted ? 'processing' : 'blue'}>{session.start_time} - {session.end_time}</Tag>
          {session.date !== todayDateStr && <Tag color="default">{session.date}</Tag>}
          {session.is_makeup && <Tag color="orange">{t('schedule.makeupBadge')}</Tag>}
          <span style={{ fontWeight: 600 }}>{session.name}</span>
          <span>({session.teacher.full_name})</span>
          <Tag>{session.students.length} students</Tag>
        </Space>
        <div>
          {session.attendance_marked ? (
            <Tag icon={<CheckCircleOutlined />} color="success" style={{ margin: 0 }}>{t('attendance.marked', 'Marked')}</Tag>
          ) : (
            <Tag color="warning" style={{ margin: 0 }}>{t('attendance.unmarked', 'Not Marked')}</Tag>
          )}
        </div>
      </div>
    </Card>
  );

  return (
    <div className="fade-in">
      {contextHolder}

      {/* Pending Attendance Panel */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24}>
          <Card title={t('attendance.pendingSessions', 'Pending Attendance')} headStyle={{ background: '#fffbe6' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {paginatedPending.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {paginatedPending.map(s => <SessionCard key={s.id + s.date} session={s} />)}
              {pendingSessions.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                  <Pagination current={pendingPage} pageSize={pageSize} total={pendingSessions.length} onChange={setPendingPage} />
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={12}>
          <Card title={t('dashboard.runningSessions', 'Running Sessions')} style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {runningSessions.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {runningSessions.map(s => <SessionCard key={s.id + s.date} session={s} isHighlighted />)}
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title={t('attendance.todaySessions', 'Today\'s Sessions')} style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {todaySessions.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {todaySessions.map(s => <SessionCard key={s.id + s.date} session={s} />)}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24}>
          <Card title={t('schedule.allSessionsThisWeek', 'All Sessions This Week')}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {paginatedAllWeek.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {paginatedAllWeek.map(s => <SessionCard key={s.id + s.date} session={s} />)}
              {sortedAllSessions.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                  <Pagination current={allWeekPage} pageSize={pageSize} total={sortedAllSessions.length} onChange={setAllWeekPage} />
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24}>
          <Card title={t('attendance.pastSessions', 'Past Sessions')}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {paginatedPast.length === 0 && <p style={{ color: '#888' }}>{t('common.noData')}</p>}
              {paginatedPast.map(s => <SessionCard key={s.id + s.date} session={s} />)}
              {pastTotal > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                  <Pagination current={pastPage} pageSize={PAST_PAGE_SIZE} total={pastTotal} onChange={setPastPage} />
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Modal
        title={selectedSession ? `${t('attendance.markAttendance')}: ${selectedSession.name}` : ''}
        centered
        width={850}
        onCancel={closeSession}
        open={!!selectedSession}
        footer={
          <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={closeSession}>{t('common.cancel')}</Button>
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
            scroll={{ x: 'max-content' }}
            columns={[
              { title: t('students.studentName'), dataIndex: 'name', key: 'name', width: 150 },
              {
                title: t('common.status'), key: 'status',
                render: (_, record) => (
                  <Radio.Group value={getDerivedStatus(record.id)} onChange={(e) => setAttendanceData((prev) => ({ ...prev, [record.id]: e.target.value }))}>
                    <Radio.Button value="present">{STATUS_ICONS.present} {t('attendance.present')}</Radio.Button>
                    <Radio.Button value="absent">{STATUS_ICONS.absent} {t('attendance.absent')}</Radio.Button>
                    <Radio.Button value="absent_with_notice">{STATUS_ICONS.absent_with_notice} {t('attendance.absentWithNotice')}</Radio.Button>
                  </Radio.Group>
                ),
              },
              {
                title: t('attendance.chargeFee'), key: 'charge_fee', width: 220,
                render: (_, record) => {
                  const chargeVal = getChargeRadioValue(record.id);
                  const isCharged = chargeVal === 'charge';
                  return (
                    <Radio.Group
                      value={chargeVal}
                      onChange={(e) => setChargeFeeData((prev) => ({ ...prev, [record.id]: e.target.value === 'charge' }))}
                      buttonStyle={isCharged ? "solid" : "outline"}
                    >
                      <Radio.Button value="charge">
                        <DollarOutlined /> {t('attendance.charge')}
                      </Radio.Button>
                      <Radio.Button value="nocharge" style={!isCharged ? { backgroundColor: '#8c8c8c', color: 'white', borderColor: '#8c8c8c' } : {}}>
                        <StopOutlined /> {t('attendance.noCharge')}
                      </Radio.Button>
                    </Radio.Group>
                  );
                },
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
}
