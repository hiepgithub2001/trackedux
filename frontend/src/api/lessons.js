import client from './client';

/** List lessons, optionally filtered by class_id or teacher_id */
export const listLessons = (params) => client.get('/lessons', { params });

/** Get a single lesson by ID */
export const getLesson = (id) => client.get(`/lessons/${id}`);

/** Create a new lesson (one-off: { specific_date } or recurring: { rrule }) */
export const createLesson = (data) => client.post('/lessons', data);

/** Update the series-level fields of a recurring lesson.
 *  data must include scope: "series"
 */
export const updateLessonSeries = (id, data) =>
  client.patch(`/lessons/${id}`, { scope: 'series', ...data });

/** Deactivate (soft-delete) a lesson */
export const deleteLesson = (id) => client.delete(`/lessons/${id}`);

/** Get occurrence override record for a single date */
export const getOccurrence = (lessonId, date) =>
  client.get(`/lessons/${lessonId}/occurrences/${date}`);

/**
 * Override a single occurrence.
 * action: "cancel" | "reschedule" | "revert"
 * For reschedule: include override_date (and optionally override_start_time "HH:MM")
 */
export const overrideOccurrence = (lessonId, date, data) =>
  client.patch(`/lessons/${lessonId}/occurrences/${date}`, data);
