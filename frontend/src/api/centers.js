import api from './client';

export const centersApi = {
  listCenters: async (params) => {
    const response = await api.get('/system/centers', { params });
    return response.data;
  },
  
  createCenter: async (data) => {
    const response = await api.post('/system/centers', data);
    return response.data;
  },

  updateCenterStatus: async (id, isActive) => {
    const response = await api.patch(`/system/centers/${id}`, { is_active: isActive });
    return response.data;
  }
};
