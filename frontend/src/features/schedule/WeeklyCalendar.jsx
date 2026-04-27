import { useState } from 'react';
import { Card, Typography, Select, Space } from 'antd';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getWeeklySchedule } from '../../api/classes';
import { listTeachers } from '../../api/teachers';

const { Title } = Typography;

const TYPE_COLORS = {
  individual: '#4096ff',
  pair: '#52c41a',
  group: '#722ed1',
};

export default function WeeklyCalendar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [teacherFilter, setTeacherFilter] = useState(undefined);

  const { data: scheduleData } = useQuery({
    queryKey: ['schedule', teacherFilter],
    queryFn: () => getWeeklySchedule({ teacher_id: teacherFilter }).then((r) => r.data),
  });

  const { data: teachers } = useQuery({
    queryKey: ['teachers'],
    queryFn: () => listTeachers().then((r) => r.data),
  });

  const events = (scheduleData?.sessions || []).map((s) => ({
    id: s.id,
    title: `${s.title || s.class_type}\n${s.teacher.full_name}`,
    start: `${s.date}T${s.start_time}`,
    end: `${s.date}T${s.end_time}`,
    backgroundColor: TYPE_COLORS[s.class_type] || '#1677ff',
    borderColor: TYPE_COLORS[s.class_type] || '#1677ff',
    extendedProps: s,
  }));

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>{t('schedule.title')}</Title>
        <Space>
          <Select
            id="teacher-filter"
            placeholder={t('schedule.teacher')}
            value={teacherFilter}
            onChange={setTeacherFilter}
            style={{ width: 200 }}
            allowClear
            options={(teachers || []).map((t) => ({ label: t.full_name, value: t.id }))}
          />
        </Space>
      </div>
      <Card bodyStyle={{ padding: 12 }}>
        <FullCalendar
          plugins={[timeGridPlugin]}
          initialView="timeGridWeek"
          events={events}
          slotMinTime="07:00:00"
          slotMaxTime="21:00:00"
          allDaySlot={false}
          height="auto"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: '',
          }}
          eventClick={(info) => navigate(`/classes/${info.event.id}`)}
          locale={localStorage.getItem('language') || 'vi'}
          firstDay={1}
        />
      </Card>
    </div>
  );
}
