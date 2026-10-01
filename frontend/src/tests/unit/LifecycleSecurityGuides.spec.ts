import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import ChangesView from '@/views/ChangesView.vue';
import PageGuide from '@/components/PageGuide.vue';
import LifecycleNotificationsView from '@/views/LifecycleNotificationsView.vue';
import SecurityUpdateHistoryView from '@/views/SecurityUpdateHistoryView.vue';
import { apiClient } from '@/services/api';
import { useAuthStore } from '@/stores/auth';

const route = vi.hoisted(() => ({ name: 'lifecycle-notifications' }));
vi.mock('vue-router', async (original) => ({
  ...await original<typeof import('vue-router')>(), useRoute: () => route, useRouter: () => ({ push: vi.fn() }),
}));
vi.mock('@/services/api', () => ({ apiClient: {
  get: vi.fn().mockResolvedValue({ data: [] }), post: vi.fn(),
} }));
let main: HTMLElement;
let view: VueWrapper | undefined;
let guide: VueWrapper;
async function render(name: string) {
  route.name = name;
  main = document.createElement('main');
  document.body.appendChild(main);
  if (name === 'changes') view = mount(ChangesView, { attachTo: main });
  else if (name === 'lifecycle-notifications') view = mount(LifecycleNotificationsView, { attachTo: main });
  else if (name === 'security-updates') view = mount(SecurityUpdateHistoryView, { attachTo: main });
  guide = mount(PageGuide, { attachTo: document.body });
  await flushPromises();
}
async function tourButton(label: string) {
  const button = Array.from(document.querySelectorAll<HTMLButtonElement>('.page-guide-actions button')).find(button => button.textContent === label);
  expect(button).toBeDefined();
  button!.click();
  await flushPromises();
}
function highlighted() { return main.querySelector('.page-guide-target')?.getAttribute('data-guide'); }
beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(useAuthStore(), 'hasPermission').mockReturnValue(true);
  HTMLElement.prototype.scrollIntoView = vi.fn();
});
afterEach(() => {
  guide?.unmount(); view?.unmount(); view = undefined; main?.remove();
  vi.restoreAllMocks();
});

describe('Lifecycle and security page guides', () => {
  it.each(['changes', 'lifecycle-notifications', 'security-updates'])('places one Guide button inside the page header on %s', async name => {
    await render(name);
    expect(view!.get('.page-header > .embedded-guide-trigger').text()).toBe('? Guide');
    expect(document.querySelectorAll('.embedded-guide-trigger')).toHaveLength(1);
    expect(guide.find('.page-guide-trigger').exists()).toBe(false);
    await view!.get('.embedded-guide-trigger').trigger('click');
    await flushPromises();
    expect(document.querySelector('.page-guide-card')).not.toBeNull();
    await tourButton('Skip tour');
  });
  it.each([true, false])('walks lifecycle sections forward and back, respecting read access (%s)', async fullAccess => {
    vi.mocked(useAuthStore().hasPermission).mockImplementation(permission => fullAccess || permission === 'lifecycle_notification_read');
    await render('lifecycle-notifications');
    const reads = vi.mocked(apiClient.get).mock.calls.length;
    await view!.get('.embedded-guide-trigger').trigger('click');
    await flushPromises();
    const targets = ['lifecycle-header', 'lifecycle-summary', 'lifecycle-queue', 'lifecycle-filters', ...(fullAccess ? ['lifecycle-products', 'lifecycle-components'] : [])];
    for (let i = 0; i < targets.length; i++) {
      expect(highlighted()).toBe(targets[i]);
      expect(document.querySelector('.page-guide-kicker')?.textContent).toContain(`${i + 1} / ${targets.length}`);
      if (targets[i] === 'lifecycle-products') expect(view!.find('#lifecycle-products').exists()).toBe(true);
      if (targets[i] === 'lifecycle-components') expect(view!.find('#lifecycle-components').exists()).toBe(true);
      if (i < targets.length - 1) await tourButton('Continue');
    }
    if (fullAccess) {
      await tourButton('Back');
      expect(view!.find('#lifecycle-products').exists()).toBe(true);
      await tourButton('Back');
      expect(highlighted()).toBe('lifecycle-filters');
      expect(view!.find('#lifecycle-queue').exists()).toBe(true);
      await tourButton('Continue'); await tourButton('Continue');
    }
    await tourButton('Finish');
    expect(document.querySelector('.page-guide-card')).toBeNull();
    expect(main.querySelector('.page-guide-target')).toBeNull();
    expect(apiClient.get).toHaveBeenCalledTimes(reads);
    expect(apiClient.post).not.toHaveBeenCalled();
  });
  it('guides security search, scope, creation prerequisites, and history without creating data', async () => {
    await render('security-updates');
    await view!.get('.embedded-guide-trigger').trigger('click');
    await flushPromises();
    const targets = ['security-header', 'security-search', 'security-product', 'security-release', 'security-create', 'security-history'];
    for (let i = 0; i < targets.length; i++) {
      expect(highlighted()).toBe(targets[i]);
      if (i < targets.length - 1) await tourButton('Continue');
    }
    await tourButton('Back');
    expect(highlighted()).toBe('security-create');
    expect(view!.get('[data-guide="security-create"]').attributes('disabled')).toBeDefined();
    expect(document.querySelector('#create-security-update-form')).toBeNull();
    await tourButton('Skip tour');
    expect(document.querySelector('.page-guide-card')).toBeNull();
    expect(apiClient.post).not.toHaveBeenCalled();
  });
});
