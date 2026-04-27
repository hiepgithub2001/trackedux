import client from './client';

export const listTeachers = () => client.get('/teachers');
export const getTeacher = (id) => client.get(`/teachers/${id}`);
export const createTeacher = (data) => client.post('/teachers', data);
export const updateTeacher = (id, data) => client.patch(`/teachers/${id}`, data);
export const setTeacherAvailability = (id, data) => client.put(`/teachers/${id}/availability`, data);
