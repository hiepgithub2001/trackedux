import { Modal, Form, InputNumber, DatePicker, Select, Input, Button } from 'antd';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { recordPayment } from '../../api/tuition';
import { listStudents } from '../../api/students';
import dayjs from 'dayjs';

export default function PaymentForm({ open, onCancel, onSuccess }) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: students } = useQuery({
    queryKey: ['students'],
    queryFn: () => listStudents({}).then((r) => r.data),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: (values) =>
      recordPayment({
        ...values,
        payment_date: values.payment_date ? values.payment_date.format('YYYY-MM-DD') : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tuition-balances'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      form.resetFields();
      onSuccess?.();
    },
  });

  return (
    <Modal
      title={t('tuition.addPayment', 'Add Payment')}
      open={open}
      onCancel={() => {
        form.resetFields();
        onCancel?.();
      }}
      footer={null}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        initialValues={{
          payment_date: dayjs(),
        }}
      >
        <Form.Item
          name="student_id"
          label={t('tuition.selectStudent', 'Select Student')}
          rules={[{ required: true, message: t('validation.required') }]}
        >
          <Select
            showSearch
            placeholder={t('tuition.selectStudent', 'Select Student')}
            optionFilterProp="label"
            options={(students?.items || []).map((s) => ({
              value: s.id,
              label: s.name || s.student_name,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="amount"
          label={t('tuition.amount', 'Amount') + ' (VND)'}
          rules={[
            { required: true, message: t('validation.required') },
            { type: 'number', min: 1, message: t('validation.required') },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={1}
            max={1000000000}
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value.replace(/,/g, '')}
            placeholder="0"
          />
        </Form.Item>

        <Form.Item
          name="payment_date"
          label={t('tuition.paymentDate', 'Payment Date')}
          rules={[{ required: true, message: t('validation.required') }]}
        >
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="payment_method" label={t('tuition.paymentMethod', 'Payment Method')}>
          <Select
            allowClear
            placeholder={t('tuition.paymentMethod', 'Payment Method')}
            options={[
              { value: 'cash', label: t('tuition.methodCash', 'Cash') },
              { value: 'bank_transfer', label: t('tuition.methodBankTransfer', 'Bank Transfer') },
              { value: 'other', label: t('tuition.methodOther', 'Other') },
            ]}
          />
        </Form.Item>

        <Form.Item name="notes" label={t('common.notes', 'Notes')}>
          <Input.TextArea rows={2} />
        </Form.Item>

        <Button
          type="primary"
          htmlType="submit"
          loading={mutation.isPending}
          block
          style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}
        >
          {t('tuition.addPayment', 'Add Payment')}
        </Button>

        {mutation.isError && (
          <div style={{ color: '#ff4d4f', marginTop: 8 }}>
            {mutation.error?.response?.data?.detail || 'Error recording payment'}
          </div>
        )}
      </Form>
    </Modal>
  );
}
