import { useState } from 'react';
import { Card, Select, Tag } from 'antd';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getWeeklySchedule } from '../../api/classes';
import { listTeachers } from '../../api/teachers';
import { UserOutlined } from '@ant-design/icons';
import './WeeklyCalendar.css';

// Premium gradient colors for events
const REGULAR_COLOR = '#1677ff'; // We'll rely on CSS for gradient or use it as fallback
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
    const isMakeup = s.is_makeup;
    const color = s.teacher?.color || (isMakeup ? MAKEUP_COLOR : REGULAR_COLOR);
    return {
      id: s.id,
      title: `${s.name}\n${s.teacher.full_name}`,
      start: `${s.date}T${s.start_time}`,
      end: `${s.date}T${s.end_time}`,
      backgroundColor: color,
      borderColor: color,
      extendedProps: s,
      className: isMakeup ? 'makeup-event' : 'regular-event',
    };
  });

  const renderEventContent = (eventInfo) => {
    const { is_makeup, name, teacher } = eventInfo.event.extendedProps;
    return (
      <div style={{ padding: '2px', overflow: 'hidden', lineHeight: 1.3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        {is_makeup && (
          <div style={{ marginBottom: 4 }}>
            <Tag
              color="volcano"
              style={{ margin: 0, padding: '0 6px', fontSize: 10, lineHeight: '18px', border: 'none', borderRadius: 4, fontWeight: 700 }}
            >
              {t('schedule.makeupBadge')}
            </Tag>
          </div>
        )}
        <div style={{ fontSize: 12, fontWeight: 700, color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,0.15)' }}>
          {eventInfo.timeText}
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginTop: 2, textShadow: '0 1px 2px rgba(0,0,0,0.15)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {name}
        </div>
        {teacher?.full_name && (
          <div style={{ fontSize: 11, opacity: 0.95, color: '#fff', marginTop: 'auto', display: 'flex', alignItems: 'center' }}>
            <span style={{ backgroundColor: 'rgba(255,255,255,0.25)', padding: '2px 6px', borderRadius: 4, display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
              <UserOutlined style={{ fontSize: 10 }} />
              <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>
                {teacher.full_name}
              </span>
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fade-in">
      <Card className="calendar-card" bordered={false}>
        <div style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 10 }}>
            <Select
              id="teacher-filter"
              placeholder={t('schedule.teacher')}
              value={teacherFilter}
              onChange={setTeacherFilter}
              style={{ width: 220 }}
              allowClear
              size="large"
              options={(teachers || []).map((teacher) => ({ 
                label: (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: teacher.color || '#1677ff' }} />
                    <span>{teacher.full_name}</span>
                  </div>
                ), 
                value: teacher.id 
              }))}
            />
          </div>
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
            center: '',
            right: '',
          }}
          eventClick={(info) => navigate(`/classes/${info.event.id}`)}
          locale={localStorage.getItem('language') || 'vi'}
          firstDay={1}
          nowIndicator={true}
          slotLabelFormat={{
            hour: '2-digit',
            minute: '2-digit',
            omitZeroMinute: false,
            meridiem: 'short'
          }}
          dayHeaderFormat={{ weekday: 'short' }}
        />
        </div>
      </Card>
    </div>
  );
}
