import client from './client';

export const listClasses = (params) => client.get('/classes', { params });
export const getClass = (id) => client.get(`/classes/${id}`);
export const createClass = (data) => client.post('/classes', data);
export const updateClass = (id, data) => client.put(`/classes/${id}`, data);
export const deleteClass = (id) => client.delete(`/classes/${id}`);
export const enrollStudent = (classId, studentId, enrolled_since) =>
  client.post(`/classes/${classId}/enroll`, { student_id: studentId, enrolled_since });
export const unenrollStudent = (classId, studentId, unenrolled_at) =>
  client.delete(`/classes/${classId}/enroll/${studentId}`, { params: { unenrolled_at } });
export const getWeeklySchedule = (params) => client.get('/schedule/weekly', { params });
export const getPastSessions = (params) => client.get('/schedule/past', { params });

