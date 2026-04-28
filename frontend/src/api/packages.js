import client from './client';

export const listPackages = (params) => client.get('/packages', { params });
export const createPackage = (data) => client.post('/packages', data);
export const updatePackage = (id, data) => client.patch(`/packages/${id}`, data);
export const recordPayment = (packageId, data) => client.post(`/packages/${packageId}/payments`, data);
export const deletePackage = (id) => client.delete(`/packages/${id}`);
export const getDashboard = () => client.get('/dashboard');
