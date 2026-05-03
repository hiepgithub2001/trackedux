import client from './client';

export const markBatchAttendance = (data) => client.post('/attendance/batch', data);
export const getSessionAttendance = (classSessionId, sessionDate) => client.get(`/attendance/session/${classSessionId}/${sessionDate}`);
export const getStudentAttendance = (studentId) => client.get(`/attendance/student/${studentId}`);
export const getAttendanceWeekly = (params) => client.get('/attendance/weekly', { params });
