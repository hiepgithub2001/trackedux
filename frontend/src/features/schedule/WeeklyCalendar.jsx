import { useState } from 'react';
import { Card, Select, Tag, Modal, Button, DatePicker, TimePicker, Space, message } from 'antd';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getWeeklySchedule } from '../../api/classes';
import { listTeachers } from '../../api/teachers';
import { overrideOccurrence } from '../../api/lessons';
import { UserOutlined } from '@ant-design/icons';
import './WeeklyCalendar.css';

const CANCELED_COLOR = '#d9d9d9';
const RESCHEDULED_COLOR = '#faad14';
const REGULAR_COLOR = '#1677ff';
const MAKEUP_COLOR = '#fa8c16';

export default function WeeklyCalendar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [teacherFilter, setTeacherFilter] = useState(undefined);
  const [weekStart, setWeekStart] = useState(null);
  const [overrideModal, setOverrideModal] = useState(null); // { lessonId, originalDate, currentStatus }
  const [rescheduleDate, setRescheduleDate] = useState(null);
  const [rescheduleTime, setRescheduleTime] = useState(null);

  const { data: scheduleData } = useQuery({
    queryKey: ['schedule', weekStart, teacherFilter],
    queryFn: () =>
      getWeeklySchedule({
        teacher_id: teacherFilter,
        week_start: weekStart,
      }).then((r) => r.data),
  });

  const { data: teachers } = useQuery({
    queryKey: ['teachers'],
    queryFn: () => listTeachers().then((r) => r.data),
  });

  const overrideMutation = useMutation({
    mutationFn: ({ lessonId, originalDate, data }) =>
      overrideOccurrence(lessonId, originalDate, data),
    onSuccess: () => {
      messageApi.success(t('lessons.occurrenceUpdated', 'Occurrence updated'));
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      setOverrideModal(null);
      setRescheduleDate(null);
      setRescheduleTime(null);
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail?.conflicts) {
        messageApi.error(t('lessons.conflictError', 'Scheduling conflict: ') + detail.conflicts[0]?.message);
      } else {
        messageApi.error(detail || t('common.error'));
      }
    },
  });

  const events = (scheduleData?.sessions || []).map((s) => {
    const isMakeup = s.is_makeup;
    const isCanceled = s.is_canceled;
    const isRescheduled = s.is_rescheduled;
    let color = s.teacher?.color || (isMakeup ? MAKEUP_COLOR : REGULAR_COLOR);
    if (isCanceled) color = CANCELED_COLOR;
    else if (isRescheduled) color = RESCHEDULED_COLOR;

    return {
      id: `${s.lesson_id}_${s.original_date || s.date}`,
      title: `${s.name}\n${s.teacher?.full_name}`,
      start: `${s.date}T${s.start_time}`,
      end: `${s.date}T${s.end_time}`,
      backgroundColor: isCanceled ? CANCELED_COLOR : color,
      borderColor: color,
      textColor: isCanceled ? '#595959' : '#fff',
      extendedProps: s,
      className: [
        isMakeup ? 'makeup-event' : 'regular-event',
        isCanceled ? 'canceled-event' : '',
        isRescheduled ? 'rescheduled-event' : '',
      ].filter(Boolean).join(' '),
    };
  });

  const renderEventContent = (eventInfo) => {
    const { is_makeup, is_canceled, is_rescheduled, name, teacher } = eventInfo.event.extendedProps;
    return (
      <div style={{
        padding: '2px', overflow: 'hidden', lineHeight: 1.3, height: '100%',
        display: 'flex', flexDirection: 'column',
        opacity: is_canceled ? 0.55 : 1,
        textDecoration: is_canceled ? 'line-through' : 'none',
      }}>
        <div style={{ marginBottom: 2, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {is_makeup && (
            <Tag color="volcano" style={{ margin: 0, padding: '0 4px', fontSize: 10, lineHeight: '16px', border: 'none', borderRadius: 3, fontWeight: 700 }}>
              {t('schedule.makeupBadge', 'MAKEUP')}
            </Tag>
          )}
          {is_canceled && (
            <Tag color="default" style={{ margin: 0, padding: '0 4px', fontSize: 10, lineHeight: '16px', border: 'none', borderRadius: 3, fontWeight: 700 }}>
              {t('lessons.canceled', 'CANCELED')}
            </Tag>
          )}
          {is_rescheduled && (
            <Tag color="gold" style={{ margin: 0, padding: '0 4px', fontSize: 10, lineHeight: '16px', border: 'none', borderRadius: 3, fontWeight: 700 }}>
              {t('lessons.rescheduled', 'MOVED')}
            </Tag>
          )}
        </div>
        <div style={{ fontSize: 12, fontWeight: 700, color: is_canceled ? '#595959' : '#fff', textShadow: is_canceled ? 'none' : '0 1px 2px rgba(0,0,0,0.15)' }}>
          {eventInfo.timeText}
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, color: is_canceled ? '#595959' : '#fff', marginTop: 2 }}>
          {name}
        </div>
        {teacher?.full_name && (
          <div style={{ fontSize: 11, opacity: 0.9, color: is_canceled ? '#595959' : '#fff', marginTop: 'auto', display: 'flex', alignItems: 'center' }}>
            <span style={{ backgroundColor: is_canceled ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.25)', padding: '2px 6px', borderRadius: 4, display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 500 }}>
              <UserOutlined style={{ fontSize: 10 }} />
              <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{teacher.full_name}</span>
            </span>
          </div>
        )}
      </div>
    );
  };

  const handleEventClick = (info) => {
    const s = info.event.extendedProps;
    // Open override modal if admin, else navigate to class
    setOverrideModal({
      lessonId: s.lesson_id,
      originalDate: s.original_date || s.date,
      currentStatus: s.is_canceled ? 'canceled' : s.is_rescheduled ? 'rescheduled' : 'active',
      className: s.name,
      classId: s.class_id,
    });
  };

  const handleDatesSet = (info) => {
    const d = info.start;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    setWeekStart(`${year}-${month}-${day}`);
  };

  return (
    <div className="fade-in">
      {contextHolder}
      <Card className="calendar-card" bordered={false}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
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
              value: teacher.id,
            }))}
          />
        </div>
        <FullCalendar
          plugins={[timeGridPlugin]}
          initialView="timeGridWeek"
          events={events}
          eventContent={renderEventContent}
          datesSet={handleDatesSet}
          slotMinTime="07:00:00"
          slotMaxTime="21:00:00"
          allDaySlot={false}
          height="auto"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: '',
          }}
          eventClick={handleEventClick}
          locale={localStorage.getItem('language') || 'vi'}
          firstDay={1}
          nowIndicator={true}
          slotLabelFormat={{ hour: '2-digit', minute: '2-digit', omitZeroMinute: false, meridiem: 'short' }}
          dayHeaderFormat={{ weekday: 'short', day: 'numeric', month: 'numeric' }}
        />
      </Card>

      {/* Occurrence Override Modal */}
      <Modal
        title={overrideModal?.className || t('lessons.occurrenceActions', 'Occurrence Actions')}
        open={!!overrideModal}
        onCancel={() => { setOverrideModal(null); setRescheduleDate(null); setRescheduleTime(null); }}
        footer={null}
        width={420}
      >
        {overrideModal && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div style={{ color: '#888', fontSize: 13 }}>
              {t('lessons.originalDate', 'Original date')}: <strong>{overrideModal.originalDate}</strong>
            </div>

            {overrideModal.currentStatus === 'canceled' ? (
              <Button
                block
                onClick={() => overrideMutation.mutate({ lessonId: overrideModal.lessonId, originalDate: overrideModal.originalDate, data: { action: 'revert' } })}
                loading={overrideMutation.isPending}
              >
                {t('lessons.revertToSeries', 'Revert to Series (Undo Cancel)')}
              </Button>
            ) : (
              <>
                <Button
                  block danger
                  onClick={() => overrideMutation.mutate({ lessonId: overrideModal.lessonId, originalDate: overrideModal.originalDate, data: { action: 'cancel' } })}
                  loading={overrideMutation.isPending}
                >
                  {t('lessons.cancelOccurrence', 'Cancel This Occurrence')}
                </Button>

                <div>
                  <div style={{ marginBottom: 8, fontWeight: 500 }}>{t('lessons.rescheduleOccurrence', 'Reschedule to:')}</div>
                  <Space>
                    <DatePicker
                      value={rescheduleDate}
                      onChange={setRescheduleDate}
                      format="YYYY-MM-DD"
                    />
                    <TimePicker
                      value={rescheduleTime}
                      onChange={setRescheduleTime}
                      format="HH:mm"
                      placeholder="Override time (optional)"
                    />
                  </Space>
                  <Button
                    type="primary"
                    block
                    style={{ marginTop: 8 }}
                    disabled={!rescheduleDate}
                    onClick={() =>
                      overrideMutation.mutate({
                        lessonId: overrideModal.lessonId,
                        originalDate: overrideModal.originalDate,
                        data: {
                          action: 'reschedule',
                          override_date: rescheduleDate?.format('YYYY-MM-DD'),
                          override_start_time: rescheduleTime?.format('HH:mm') || undefined,
                        },
                      })
                    }
                    loading={overrideMutation.isPending}
                  >
                    {t('lessons.confirmReschedule', 'Confirm Reschedule')}
                  </Button>
                </div>

                {overrideModal.currentStatus === 'rescheduled' && (
                  <Button
                    block
                    onClick={() => overrideMutation.mutate({ lessonId: overrideModal.lessonId, originalDate: overrideModal.originalDate, data: { action: 'revert' } })}
                    loading={overrideMutation.isPending}
                  >
                    {t('lessons.revertToSeries', 'Revert Reschedule')}
                  </Button>
                )}
              </>
            )}

            <Button block onClick={() => navigate(`/classes/${overrideModal.classId}`)}>
              {t('common.viewClass', 'View Class')}
            </Button>
          </Space>
        )}
      </Modal>
    </div>
  );
}
