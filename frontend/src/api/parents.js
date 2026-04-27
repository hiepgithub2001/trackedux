import client from './client';

export const listParents = () => client.get('/parents');
export const getParent = (id) => client.get(`/parents/${id}`);
export const createParent = (data) => client.post('/parents', data);
export const updateParent = (id, data) => client.patch(`/parents/${id}`, data);
