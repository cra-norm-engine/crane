import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import SettingsView from '@/views/SettingsView.vue';
import PageGuide from '@/components/PageGuide.vue';
import { useAuthStore } from '@/stores/auth';
import { apiClient } from '@/services/api';

vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }), useRoute: () => ({ name: 'settings' }) }));
vi.mock('@/services/jira-service', () => ({ jiraService: { connections: vi.fn().mockResolvedValue([]) } }));
vi.mock('@/services/user-service', () => ({ userService: { listSummary: vi.fn().mockResolvedValue([]) } }));
vi.mock('@/services/admin-service', () => ({ adminService: {
  getVulnerabilityScanning: vi.fn().mockResolvedValue({ enabled: true }),
  getSystemUpdates: vi.fn().mockResolvedValue({
    installed_version: '1.2.0', configured: true, update_checks_enabled: true,
    policy: { policy: 'manual', channel: 'stable', maintenance_day: 6, maintenance_hour_utc: 2, postponed_until: null },
    update_available: false, automatic_update_eligible: false, manifest: null,
    last_checked_at: null, last_error: null, last_operation: null, manual_command: './crane-update apply',
  }),
} }));
vi.mock('@/services/api', () => ({ apiClient: {
  get: vi.fn().mockResolvedValue({ data: [] }),
  post: vi.fn().mockResolvedValue({ data: {} }),
  patch: vi.fn(),
  put: vi.fn(),
} }));

describe('Settings category navigation', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
    const values = new Map<string, string>();
    Object.defineProperty(window, 'localStorage', { configurable: true, value: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
      clear: () => values.clear(),
    } });
    HTMLElement.prototype.scrollIntoView = vi.fn();
    useAuthStore().login('test', 'refresh', { id: 'user', email: 'user@example.com', full_name: 'Test user', avatar_data: null, is_active: true, roles: [], permissions: [], auth_provider: 'local', must_change_password: false });
  });

  it('marks invalid profile drafts and lets the user discard them', async () => {
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    const name = wrapper.get('#settings-full-name');
    await name.setValue('');
    expect(name.attributes('aria-invalid')).toBe('true');
    expect(wrapper.get('#full-name-error').text()).toContain('Enter your full name');
    expect(wrapper.find('button[aria-controls="account"] [aria-label="Unsaved changes"]').exists()).toBe(true);
    expect(wrapper.get('#account .app-btn--primary').attributes('disabled')).toBeDefined();
    await wrapper.get('#account .s-card-foot .app-btn--secondary').trigger('click');
    expect((name.element as HTMLInputElement).value).toBe('Test user');
    expect(wrapper.find('#account .save-note').exists()).toBe(false);
    expect(name.attributes('aria-invalid')).toBe('false');
    wrapper.unmount();
  });

  it('keeps a failed save editable, then clears pending state after retry succeeds', async () => {
    vi.mocked(apiClient.patch).mockRejectedValueOnce(new Error('Could not save profile'));
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    await wrapper.get('#settings-full-name').setValue('Updated name');
    await wrapper.get('#account .app-btn--primary').trigger('click');
    await flushPromises();
    expect(wrapper.get('#account [role="alert"]').text()).toBe('Could not save profile');
    expect(wrapper.get('#account .save-note').text()).toBe('Unsaved changes');
    expect(wrapper.get('#settings-full-name').attributes('disabled')).toBeUndefined();
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: { full_name: 'Updated name' } });
    await wrapper.get('#account .app-btn--primary').trigger('click');
    await flushPromises();
    expect(apiClient.patch).toHaveBeenLastCalledWith('/auth/me/profile', { full_name: 'Updated name' });
    expect(useAuthStore().userFullName).toBe('Updated name');
    expect(wrapper.find('#account .save-note').exists()).toBe(false);
    expect(wrapper.get('#account .saved-tag').text()).toBe('Saved');
    wrapper.unmount();
  });

  it('navigates with the mobile picker, retains drafts, and restores saved preferences', async () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({ ...window.matchMedia(''), matches: true });
    useAuthStore().updateUser({ preferences: { theme: 'dark', timezone: 'Europe/Vienna', date_format: 'DD/MM/YYYY', default_landing_page: 'my-tasks' } });
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    await wrapper.get('#settings-section').setValue('preferences');
    await flushPromises();
    expect(wrapper.get('#preferences').isVisible()).toBe(true);
    expect(document.activeElement).toBe(wrapper.get('#preferences h2').element);
    expect(HTMLElement.prototype.scrollIntoView).toHaveBeenLastCalledWith({ behavior: 'instant', block: 'start' });
    expect(wrapper.findAll('#settings-timezone option').map(option => option.attributes('value'))).toContain('UTC');
    await wrapper.get('#settings-timezone').setValue('UTC');
    await wrapper.get('#settings-date-format').setValue('YYYY-MM-DD');
    await wrapper.get('#settings-landing-page').setValue('products');
    expect(wrapper.find('button[aria-controls="preferences"] [aria-label="Unsaved changes"]').exists()).toBe(true);
    await wrapper.get('#settings-section').setValue('security');
    await wrapper.get('#settings-section').setValue('preferences');
    expect((wrapper.get('#settings-timezone').element as HTMLSelectElement).value).toBe('UTC');
    await wrapper.get('#preferences .s-card-foot .app-btn--secondary').trigger('click');
    expect((wrapper.get('#settings-timezone').element as HTMLSelectElement).value).toBe('Europe/Vienna');
    expect((wrapper.get('#settings-date-format').element as HTMLSelectElement).value).toBe('DD/MM/YYYY');
    expect((wrapper.get('#settings-landing-page').element as HTMLSelectElement).value).toBe('my-tasks');
    expect(wrapper.find('#preferences .save-note').exists()).toBe(false);
    wrapper.unmount();
  });

  it('saves preferences and applies the previewed theme immediately', async () => {
    const preferences = { theme: 'dark', timezone: 'UTC', date_format: 'YYYY-MM-DD', default_landing_page: 'products' };
    vi.mocked(apiClient.put).mockResolvedValueOnce({ data: preferences });
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    await wrapper.get('#settings-section').setValue('preferences');
    await wrapper.get('#settings-landing-page').setValue('products');
    await wrapper.get('#preferences .app-btn--primary').trigger('click');
    await flushPromises();
    expect(useAuthStore().preferences).toEqual(preferences);
    expect(wrapper.get('#preferences .saved-tag').text()).toBe('Saved');
    expect(wrapper.find('#preferences .save-note').exists()).toBe(false);
    vi.mocked(apiClient.put).mockResolvedValueOnce({ data: { ...preferences, theme: 'light' } });
    await wrapper.get('#settings-section').setValue('appearance');
    await wrapper.get('.theme-opt').trigger('click');
    await flushPromises();
    expect(document.documentElement.dataset.theme).toBe('light');
    expect(wrapper.get('.theme-opt').attributes('aria-pressed')).toBe('true');
    expect(apiClient.put).toHaveBeenLastCalledWith('/auth/me/preferences', { theme: 'light' });
    wrapper.unmount();
  });

  it('shows one category and preserves unsaved values when switching', async () => {
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    expect(wrapper.get('#account').isVisible()).toBe(true);
    expect(wrapper.get('#appearance').isVisible()).toBe(false);
    const name = wrapper.get('#account input[autocomplete="name"]');
    await name.setValue('Draft name');
    await wrapper.get('button[aria-controls="appearance"]').trigger('click');
    await flushPromises();
    expect(wrapper.get('#appearance').isVisible()).toBe(true);
    expect(wrapper.get('#account').isVisible()).toBe(false);
    expect(wrapper.get('button[aria-controls="appearance"]').attributes('aria-current')).toBe('page');
    await wrapper.get('button[aria-controls="account"]').trigger('click');
    expect((name.element as HTMLInputElement).value).toBe('Draft name');
    expect(wrapper.find('button[aria-controls="external-findings"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it('reveals an admin integration when the guide targets its hidden panel', async () => {
    const auth = useAuthStore();
    vi.spyOn(auth, 'hasPermission').mockReturnValue(true);
    const wrapper = mount(SettingsView, { attachTo: document.body, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    await flushPromises();
    expect(wrapper.get('#external-findings').isVisible()).toBe(false);
    window.dispatchEvent(new CustomEvent('crane-guide-reveal', { detail: '[data-guide="settings-external-tools"]' }));
    await flushPromises();
    expect(wrapper.get('#external-findings').isVisible()).toBe(true);
    expect(wrapper.get('#account').isVisible()).toBe(false);
    wrapper.unmount();
  });

  it.each([true, false])('keeps the guide in navigation order and Back works (admin: %s)', async (admin) => {
    vi.spyOn(useAuthStore(), 'hasPermission').mockReturnValue(admin);
    const main = document.createElement('main');
    document.body.appendChild(main);
    const wrapper = mount(SettingsView, { attachTo: main, global: { stubs: { DependencyTrackSettings: true, AppLogo: true } } });
    const guide = mount(PageGuide, { attachTo: document.body });
    await flushPromises();
    const navigation = wrapper.findAll('.snav-link').map(button => button.attributes('aria-controls'));
    expect(navigation.at(-1)).toBe('about');
    expect(wrapper.get('.snav-about button').attributes('aria-controls')).toBe('about');
    window.dispatchEvent(new Event('crane-guide-start'));
    await flushPromises();
    const visited: string[] = [];
    for (let i = 0; i < 20; i++) {
      const current = wrapper.get('.snav-link[aria-current="page"]').attributes('aria-controls');
      if (current && visited.at(-1) !== current) visited.push(current);
      if (document.querySelector('#page-guide-title')?.textContent === 'Review system information') break;
      (document.querySelector('.page-guide-actions .page-guide-primary') as HTMLButtonElement).click();
      await flushPromises();
    }
    expect(visited).toEqual(navigation);
    const back = Array.from(document.querySelectorAll<HTMLButtonElement>('.page-guide-actions button')).find(button => button.textContent === 'Back')!;
    back.click();
    await flushPromises();
    expect(wrapper.get('#jira').isVisible()).toBe(true);
    back.click();
    await flushPromises();
    expect(wrapper.get(admin ? '#external-findings' : '#security').isVisible()).toBe(true);
    guide.unmount(); wrapper.unmount(); main.remove();
  });
});
