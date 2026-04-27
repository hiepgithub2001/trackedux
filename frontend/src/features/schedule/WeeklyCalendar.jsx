import { useState } from 'react';
import { Card, Typography, Select, Space, Tag } from 'antd';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getWeeklySchedule } from '../../api/classes';
import { listTeachers } from '../../api/teachers';

const { Title } = Typography;

const REGULAR_COLOR = '#1677ff';
const MAKEUP_COLOR = '#fa8c16';

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

  const events = (scheduleData?.sessions || []).map((s) => {
    const color = s.is_makeup ? MAKEUP_COLOR : REGULAR_COLOR;
    return {
      id: s.id,
      title: `${s.name}\n${s.teacher.full_name}`,
      start: `${s.date}T${s.start_time}`,
      end: `${s.date}T${s.end_time}`,
      backgroundColor: color,
      borderColor: color,
      extendedProps: s,
    };
  });

  const renderEventContent = (eventInfo) => {
    const { is_makeup, name, teacher } = eventInfo.event.extendedProps;
    return (
      <div style={{ padding: '2px 4px', overflow: 'hidden', lineHeight: 1.25 }}>
        {is_makeup && (
          <Tag
            color="orange"
            style={{ marginRight: 0, marginBottom: 2, padding: '0 6px', fontSize: 10, lineHeight: '16px' }}
          >
            {t('schedule.makeupBadge')}
          </Tag>
        )}
        <div style={{ fontSize: 12, fontWeight: 600 }}>{eventInfo.timeText}</div>
        <div style={{ fontSize: 12, fontWeight: 600 }}>{name}</div>
        <div style={{ fontSize: 11, opacity: 0.85 }}>{teacher?.full_name}</div>
      </div>
    );
  };

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
            options={(teachers || []).map((teacher) => ({ label: teacher.full_name, value: teacher.id }))}
          />
        </Space>
      </div>
      <Card bodyStyle={{ padding: 12 }}>
        <FullCalendar
          plugins={[timeGridPlugin]}
          initialView="timeGridWeek"
          events={events}
          eventContent={renderEventContent}
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
