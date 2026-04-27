import { Form, Input, Modal, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { createParent } from '../../api/parents';

export default function ParentFormModal({ open, onCancel, onSuccess }) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (values) => createParent(values),
    onSuccess: (response) => {
      messageApi.success(t('common.success', 'Thêm phụ huynh thành công'));
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      form.resetFields();
      if (onSuccess) {
        onSuccess(response.data.id);
      }
    },
    onError: (err) => {
      messageApi.error(err.response?.data?.detail || t('common.error', 'Đã xảy ra lỗi'));
    },
  });

  const handleOk = () => {
    form.validateFields().then((values) => {
      mutation.mutate(values);
    });
  };

  return (
    <>
      {contextHolder}
      <Modal
        title={t('students.addParent', 'Thêm phụ huynh')}
        open={open}
        onOk={handleOk}
        onCancel={() => {
          form.resetFields();
          onCancel();
        }}
        confirmLoading={mutation.isPending}
        okText={t('common.save', 'Lưu')}
        cancelText={t('common.cancel', 'Hủy')}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="full_name"
            label={t('students.parentName', 'Tên phụ huynh')}
            rules={[{ required: true, message: t('validation.required', 'Trường này bắt buộc') }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="phone"
            label={t('students.phone', 'Số điện thoại')}
            rules={[{ required: true, message: t('validation.required', 'Trường này bắt buộc') }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="phone_secondary" label={t('students.phoneSecondary', 'SĐT phụ')}>
            <Input />
          </Form.Item>

          <Form.Item name="address" label={t('students.address', 'Địa chỉ')}>
            <Input.TextArea rows={2} />
          </Form.Item>

          <Form.Item name="zalo_id" label={t('students.zaloId', 'Zalo ID / SĐT Zalo')}>
            <Input />
          </Form.Item>

          <Form.Item name="notes" label={t('students.notes', 'Ghi chú')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
