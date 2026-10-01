import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import LifecycleNotificationsView from '@/views/LifecycleNotificationsView.vue';
import { lifecycleNotificationService as notifications } from '@/services/lifecycle-notification-service';
import { supportPeriodService } from '@/services/support-period-service';
import { supplierAssessmentService } from '@/services/supplier-assessment-service';
import { productReleaseService } from '@/services/product-release-service';
import { useAuthStore } from '@/stores/auth';
import type { LifecycleNotificationRead } from '@/types/product';

vi.mock('@/services/lifecycle-notification-service', () => ({ lifecycleNotificationService: {
  list: vi.fn(), markSent: vi.fn(), dismiss: vi.fn(), scheduleEosCheck: vi.fn(),
} }));
vi.mock('@/services/product-service', () => ({ productService: { list: vi.fn().mockResolvedValue([
  { id: 'p1', name: 'Smart Lock', product_code: 'SL1', manufacturer_name: 'Maker', current_classification: 'normal', updated_at: '2026-09-01' },
  { id: 'p2', name: 'No support product', product_code: 'NS1', current_classification: 'normal', updated_at: '2026-09-01' },
]) } }));
vi.mock('@/services/product-release-service', () => ({ productReleaseService: { list: vi.fn().mockResolvedValue([{ id: 'r1', display_version: '1.0' }, { id: 'r2', display_version: '2.0' }]) } }));
vi.mock('@/services/support-period-service', () => ({ supportPeriodService: { list: vi.fn() } }));
vi.mock('@/services/supplier-assessment-service', () => ({ supplierAssessmentService: { componentSupport: vi.fn() } }));
const makeAlert = (id: string, status = 'pending') => ({
  id, status, title: `Support alert ${id}`, message: 'Review support communication.', notification_type: 'end_of_support_upcoming',
  recipient_user: { full_name: 'Reviewer' }, created_at: '2026-09-01T12:00:00Z',
} as LifecycleNotificationRead);
let wrapper: VueWrapper;
const button = (text: string) => wrapper.findAll('button').find(item => item.text() === text)!;
const select = (label: string) => wrapper.findAll('label').find(item => item.text().startsWith(label))!.get('select');
async function render() {
  wrapper = mount(LifecycleNotificationsView, { attachTo: document.body, global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } });
  await flushPromises();
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-09-30T12:00:00Z'));
  vi.spyOn(useAuthStore(), 'hasPermission').mockReturnValue(true);
  vi.mocked(notifications.list).mockResolvedValue([makeAlert('pending'), makeAlert('sent', 'sent')]);
  vi.mocked(supportPeriodService.list).mockResolvedValue([
    { id: 'ended', product_id: 'p1', is_active: true, support_end_date: '2026-09-29' },
    { id: 'today', product_id: 'p1', product_release_id: 'r1', is_active: true, support_end_date: '2026-09-30' },
    { id: 'ninety', product_id: 'p1', product_release_id: 'r2', is_active: true, support_end_date: '2026-12-29' },
    { id: 'later', product_id: 'p1', product_release_id: 'r3', is_active: true, support_end_date: '2026-12-30' },
  ] as Awaited<ReturnType<typeof supportPeriodService.list>>);
  vi.mocked(supplierAssessmentService.componentSupport).mockResolvedValue([]);
  vi.spyOn(HTMLDialogElement.prototype, 'showModal').mockImplementation(function (this: HTMLDialogElement) { this.open = true; });
  vi.spyOn(HTMLDialogElement.prototype, 'close').mockImplementation(function (this: HTMLDialogElement) { this.open = false; this.dispatchEvent(new Event('close')); });
});
afterEach(() => { wrapper?.unmount(); vi.restoreAllMocks(); vi.useRealTimers(); });

describe('Lifecycle alert workflow', () => {
  it('starts with pending notifications, pages large queues, and resets the page when filtering', async () => {
    vi.mocked(notifications.list).mockResolvedValue([...Array.from({ length: 21 }, (_, i) => makeAlert(String(i))), makeAlert('history', 'sent')]);
    await render();
    expect(wrapper.findAll('.alert-card')).toHaveLength(20);
    expect(wrapper.text()).not.toContain('Support alert history');
    await button('Next').trigger('click');
    expect(wrapper.findAll('.alert-card')).toHaveLength(1);
    await wrapper.get('input[type="search"]').setValue('alert 0');
    expect(wrapper.findAll('.alert-card')).toHaveLength(1);
    expect(wrapper.get('.alert-card').text()).toContain('Support alert 0');
    await button('Reset filters').trigger('click');
    expect(wrapper.get('.result-count').text()).toBe('22 notifications');
  });
  it('loads support in bulk and includes today, day 90, release records, and missing records accurately', async () => {
    await render();
    expect(supportPeriodService.list).toHaveBeenCalledExactlyOnceWith({ active_only: true });
    const summary = wrapper.findAll('.summary-card');
    expect(summary[1].get('strong').text()).toBe('1');
    expect(summary[2].get('strong').text()).toBe('2');
    await summary[2].trigger('click');
    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
    expect(wrapper.text()).toContain('Ends today');
    expect(wrapper.text()).toContain('90 days remaining');
    expect(wrapper.get('tbody').text()).toContain('Release 1.0');
    expect(wrapper.get('tbody').text()).toContain('Release 2.0');
    expect(wrapper.text()).not.toContain('91 days remaining');
    await select('Support window').setValue('missing');
    expect(wrapper.findAll('tbody tr')).toHaveLength(1);
    expect(wrapper.get('tbody').text()).toContain('No support product');
    await select('Support window').setValue('custom');
    await wrapper.get('input[type="number"]').setValue(0);
    expect(wrapper.get('#custom-days-error').text()).toContain('whole number');
    expect(wrapper.findAll('tbody tr')).toHaveLength(0);
  });
  it('requires confirmation, reports mutation failures, and updates a single notification without refetching', async () => {
    await render();
    await button('Record as sent').trigger('click');
    await flushPromises();
    expect(notifications.markSent).not.toHaveBeenCalled();
    expect(wrapper.get('dialog').text()).toContain('does not deliver an email');
    vi.mocked(notifications.markSent).mockRejectedValueOnce(new Error('network'));
    await button('Confirm sent').trigger('click');
    await flushPromises();
    expect(wrapper.get('dialog [role="alert"]').text()).toContain('Could not confirm');
    expect(wrapper.findAll('.alert-card')).toHaveLength(1);
    vi.mocked(notifications.markSent).mockResolvedValueOnce(makeAlert('pending', 'sent'));
    await button('Confirm sent').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('.alert-card')).toHaveLength(0);
    expect(wrapper.text()).toContain('recorded as sent');
    expect(notifications.list).toHaveBeenCalledTimes(1);
    expect(document.activeElement).toBe(wrapper.get('h2').element);
  });
  it('dismisses only after confirmation and retains the notification in history', async () => {
    await render();
    await button('Dismiss').trigger('click');
    await flushPromises();
    expect(notifications.dismiss).not.toHaveBeenCalled();
    expect(wrapper.get('dialog').text()).toContain('does not resolve the underlying support risk');
    vi.mocked(notifications.dismiss).mockResolvedValueOnce(makeAlert('pending', 'dismissed'));
    await button('Confirm dismissal').trigger('click');
    await flushPromises();
    expect(notifications.dismiss).toHaveBeenCalledExactlyOnceWith('pending');
    expect(wrapper.findAll('.alert-card')).toHaveLength(0);
    await select('Status').setValue('dismissed');
    expect(wrapper.findAll('.alert-card')).toHaveLength(1);
  });
  it('uses configured scheduler settings independently of display filters', async () => {
    vi.mocked(notifications.scheduleEosCheck).mockResolvedValue([]);
    await render();
    await button('Product support').trigger('click');
    await select('Support window').setValue('30');
    await button('Check support deadlines').trigger('click');
    await flushPromises();
    expect(notifications.scheduleEosCheck).toHaveBeenCalledExactlyOnceWith();
    expect(wrapper.text()).toContain('0 new notifications');
    expect(wrapper.text()).not.toContain('threshold 30');
  });
  it('keeps failed loads visible and allows retry without hiding other sections', async () => {
    vi.mocked(notifications.list).mockRejectedValueOnce(new Error('offline'));
    await render();
    expect(wrapper.get('[role="alert"]').text()).toContain('Could not load notification queue');
    expect(wrapper.text()).not.toContain('No notifications awaiting review');
    await button('Try again').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('.alert-card')).toHaveLength(1);
  });
  it('hides write controls and restricted datasets for a notification-only reader', async () => {
    vi.mocked(useAuthStore().hasPermission).mockImplementation(permission => permission === 'lifecycle_notification_read');
    await render();
    expect(wrapper.text()).toContain('read-only access');
    expect(button('Record as sent')).toBeUndefined();
    expect(button('Check support deadlines')).toBeUndefined();
    expect(button('Product support')).toBeUndefined();
    expect(supportPeriodService.list).not.toHaveBeenCalled();
    expect(supplierAssessmentService.componentSupport).not.toHaveBeenCalled();
    expect(productReleaseService.list).not.toHaveBeenCalled();
  });
  it('distinguishes coverage risks from covered relationships and supports finding covered records', async () => {
    vi.mocked(supplierAssessmentService.componentSupport).mockResolvedValue([
      { link_id: 'risk', component_name: 'Library A', status: 'gap', severity: 'high', product_name: 'Lock', support_gap_days: 45 },
      { link_id: 'safe', component_name: 'Library B', status: 'covered', severity: 'info', product_name: 'Lock' },
    ] as Awaited<ReturnType<typeof supplierAssessmentService.componentSupport>>);
    await render();
    await wrapper.findAll('.summary-card')[3].trigger('click');
    expect(wrapper.findAll('tbody tr')).toHaveLength(1);
    expect(wrapper.get('tbody').text()).toContain('45 days of coverage gap');
    await select('Coverage').setValue('all');
    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
  });
});
