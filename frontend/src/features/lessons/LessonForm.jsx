import { Modal, Form, Select, InputNumber, DatePicker, Radio, Input, Button, Alert, message, Spin } from 'antd';
import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import { listClasses } from '../../api/classes';
import { listTeachers } from '../../api/teachers';
import { createLesson, getLesson, updateLessonSeries } from '../../api/lessons';

const TIME_OPTIONS = [];
for (let h = 7; h <= 21; h++) {
  for (let m = 0; m < 60; m += 15) {
    if (h === 21 && m > 0) continue;
    const hour = h.toString().padStart(2, '0');
    const min = m.toString().padStart(2, '0');
    TIME_OPTIONS.push({ label: `${hour}:${min}`, value: `${hour}:${min}` });
  }
}

const DAYS = [
  { label: 'Monday', value: 0 },
  { label: 'Tuesday', value: 1 },
  { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 },
  { label: 'Friday', value: 4 },
  { label: 'Saturday', value: 5 },
  { label: 'Sunday', value: 6 },
];
const BYDAY_MAP = { 0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU' };

function buildRrule({ day_of_week, count, until }) {
  const byday = BYDAY_MAP[day_of_week] ?? 'MO';
  let rule = `FREQ=WEEKLY;BYDAY=${byday}`;
  if (count) rule += `;COUNT=${count}`;
  else if (until) rule += `;UNTIL=${until.format('YYYYMMDD')}`;
  return rule;
}

function parseRrule(rruleStr) {
  if (!rruleStr) return {};
  const rules = Object.fromEntries(rruleStr.split(';').map(p => p.split('=')));
  const byday = rules['BYDAY'] || 'MO';
  const day_of_week = Object.keys(BYDAY_MAP).find(k => BYDAY_MAP[k] === byday) ?? 0;
  return {
    day_of_week: Number(day_of_week),
    count: rules['COUNT'] ? Number(rules['COUNT']) : undefined,
    until: rules['UNTIL'] ? dayjs(rules['UNTIL'], 'YYYYMMDD') : undefined,
  };
}

export default function LessonForm({ open, onClose, onSuccess, defaultClassId, lessonId }) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const [lessonType, setLessonType] = useState('recurring');
  const [conflictError, setConflictError] = useState(null);
  
  const isEdit = !!lessonId;

  const { data: classes = [] } = useQuery({
    queryKey: ['classes'],
    queryFn: () => listClasses().then((r) => r.data),
  });

  const { data: teachers = [] } = useQuery({
    queryKey: ['teachers'],
    queryFn: () => listTeachers().then((r) => r.data),
  });

  const { data: lessonData, isLoading: isLessonLoading } = useQuery({
    queryKey: ['lesson', lessonId],
    queryFn: () => getLesson(lessonId).then(r => r.data),
    enabled: isEdit && open,
  });

  useEffect(() => {
    if (isEdit && lessonData && open) {
      const type = lessonData.rrule ? 'recurring' : 'oneoff';
      setLessonType(type);
      const parsedRrule = type === 'recurring' ? parseRrule(lessonData.rrule) : {};
      form.setFieldsValue({
        class_id: lessonData.class_id,
        teacher_id: lessonData.teacher_id,
        title: lessonData.title,
        start_time: lessonData.start_time,
        duration_minutes: lessonData.duration_minutes,
        specific_date: lessonData.specific_date ? dayjs(lessonData.specific_date) : undefined,
        ...parsedRrule,
      });
    } else if (!isEdit && open) {
      form.resetFields();
      setLessonType('recurring');
      form.setFieldsValue({ class_id: defaultClassId, duration_minutes: 60 });
    }
  }, [isEdit, lessonData, open, form, defaultClassId]);

  const saveMutation = useMutation({
    mutationFn: (payload) => {
      if (isEdit) {
        return updateLessonSeries(lessonId, payload);
      }
      return createLesson(payload);
    },
    onSuccess: () => {
      messageApi.success(isEdit ? t('lessons.updated', 'Lesson updated') : t('lessons.created', 'Lesson created'));
      form.resetFields();
      setConflictError(null);
      onSuccess?.();
    },
    onError: (err) => {
      if (err.response?.status === 409) {
        const detail = err.response.data?.detail;
        if (detail?.conflicts) {
          setConflictError(detail.conflicts.map((c) => c.message).join('; '));
        } else {
          setConflictError(t('lessons.conflictGeneric', 'Scheduling conflict detected'));
        }
      } else {
        messageApi.error(err.response?.data?.detail || t('common.error'));
      }
    },
  });

  const handleFinish = (values) => {
    setConflictError(null);
    const payload = {
      class_id: values.class_id || defaultClassId || null,
      teacher_id: values.teacher_id,
      title: values.title || null,
      start_time: values.start_time,
      duration_minutes: values.duration_minutes,
    };

    if (lessonType === 'recurring') {
      payload.rrule = buildRrule({
        day_of_week: values.day_of_week,
        count: values.count || null,
        until: values.until || null,
      });
      payload.specific_date = null;
    } else {
      payload.specific_date = values.specific_date?.format('YYYY-MM-DD');
      payload.rrule = null;
    }

    saveMutation.mutate(payload);
  };

  return (
    <Modal
      title={isEdit ? t('lessons.editLesson', 'Edit Lesson') : t('lessons.addLesson', 'Add Lesson')}
      open={open}
      onCancel={() => { setConflictError(null); form.resetFields(); onClose(); }}
      footer={null}
      width={520}
    >
      {contextHolder}
      {isEdit && isLessonLoading ? (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Spin />
        </div>
      ) : (
        <>
          {conflictError && (
            <Alert
              type="error"
              message={t('lessons.conflictError', 'Scheduling Conflict')}
              description={conflictError}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          <Form form={form} layout="vertical" onFinish={handleFinish} initialValues={{ class_id: defaultClassId, duration_minutes: 60 }}>
            <Form.Item name="class_id" label={t('classes.class', 'Class')}>
              <Select
                placeholder={t('lessons.selectClass', 'Select a class (optional)')}
                allowClear
                options={classes.map((c) => ({ label: c.name, value: c.id }))}
                disabled={isEdit || !!defaultClassId}
              />
            </Form.Item>

            <Form.Item name="teacher_id" label={t('schedule.teacher')} rules={[{ required: true }]}>
              <Select
                placeholder={t('lessons.selectTeacher', 'Select teacher')}
                options={teachers.map((t) => ({ label: t.full_name, value: t.id }))}
              />
            </Form.Item>

            <Form.Item name="title" label={t('lessons.title', 'Title (optional)')}>
              <Input placeholder={t('lessons.titlePlaceholder', 'e.g. Theory lesson, Group makeup')} />
            </Form.Item>

            <Form.Item label={t('lessons.lessonType', 'Lesson Type')}>
              <Radio.Group value={lessonType} onChange={(e) => setLessonType(e.target.value)}>
                <Radio.Button value="recurring">{t('lessons.recurring', 'Recurring')}</Radio.Button>
                <Radio.Button value="oneoff">{t('lessons.oneOff', 'One-off')}</Radio.Button>
              </Radio.Group>
            </Form.Item>

            {lessonType === 'recurring' ? (
              <>
                <Form.Item name="day_of_week" label={t('lessons.dayOfWeek', 'Day of Week')} rules={[{ required: true }]}>
                  <Select options={DAYS} />
                </Form.Item>
                <Form.Item name="count" label={t('lessons.count', 'Number of occurrences (leave blank for open-ended)')}>
                  <InputNumber min={1} max={520} style={{ width: '100%' }} placeholder="e.g. 10" />
                </Form.Item>
                <Form.Item name="until" label={t('lessons.until', 'End date (alternative to count)')}>
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </>
            ) : (
              <Form.Item name="specific_date" label={t('lessons.specificDate', 'Date')} rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            )}

            <Form.Item name="start_time" label={t('common.time', 'Start Time')} rules={[{ required: true }]}>
              <Select
                showSearch
                options={TIME_OPTIONS}
                placeholder={t('lessons.selectTime', 'Select time')}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item name="duration_minutes" label={t('lessons.duration', 'Duration (minutes)')} rules={[{ required: true }]}>
              <InputNumber min={15} max={480} step={15} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={saveMutation.isPending}>
                {isEdit ? t('common.save', 'Save') : t('lessons.createLesson', 'Create Lesson')}
              </Button>
            </Form.Item>
          </Form>
        </>
      )}
    </Modal>
  );
}
