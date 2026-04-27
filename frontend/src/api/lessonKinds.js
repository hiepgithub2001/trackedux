import client from './client';

export const fetchLessonKinds = (search) => client.get('/lesson-kinds', { params: { search } });
