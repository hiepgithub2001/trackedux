import client from './client';

export const listClasses = (params) => client.get('/classes', { params });
export const getClass = (id) => client.get(`/classes/${id}`);
export const createClass = (data) => client.post('/classes', data);
export const updateClass = (id, data) => client.put(`/classes/${id}`, data);
export const deleteClass = (id) => client.delete(`/classes/${id}`);
export const enrollStudent = (classId, studentId) => client.post(`/classes/${classId}/enroll`, { student_id: studentId });
export const unenrollStudent = (classId, studentId) => client.delete(`/classes/${classId}/enroll/${studentId}`);
export const getWeeklySchedule = (params) => client.get('/schedule/weekly', { params });
