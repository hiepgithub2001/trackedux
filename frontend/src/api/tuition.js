import client from './client';

export const listBalances = (params) => client.get('/tuition/balances', { params });
export const recordPayment = (data) => client.post('/tuition/payments', data);
export const listPayments = (params) => client.get('/tuition/payments', { params });
export const getStudentLedger = (studentId, params) => client.get(`/tuition/ledger/${studentId}`, { params });
export const getChildBalance = (studentId) => client.get(`/tuition/my-child/${studentId}/balance`);
export const getDashboard = () => client.get('/dashboard');
