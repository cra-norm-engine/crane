import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import LoginView from '@/views/LoginView.vue';
import { useAuthStore } from '@/stores/auth';

const mocks = vi.hoisted(() => ({
  login: vi.fn(), fetchUser: vi.fn(), push: vi.fn(),
  query: {} as Record<string, string>,
}));
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
  useRoute: () => ({ query: mocks.query }),
}));
vi.mock('@/router', () => ({ resolveLandingRouteName: () => 'my-tasks' }));
vi.mock('@/services/auth-service', () => ({ loginRequest: mocks.login, fetchCurrentUser: mocks.fetchUser }));

const demo = { email: 'crane@cra-norm-engine.com', password: '8hARz]9$]>r3Tn' };
const user = {
  id: 'demo', email: demo.email, full_name: 'Demo user', avatar_data: null,
  is_active: true, roles: [], permissions: [], auth_provider: 'local', must_change_password: false,
  preferences: { theme: 'light', timezone: 'UTC', date_format: 'YYYY-MM-DD', default_landing_page: 'my-tasks' },
};
const render = () => mount(LoginView, { global: { stubs: { AppLogo: true } } });

describe('Login page', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.stubEnv('VITE_PUBLIC_DEMO', 'true');
    vi.stubEnv('DEV', false);
    mocks.query = {};
    const values = new Map<string, string>();
    Object.defineProperty(window, 'localStorage', { configurable: true, value: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    } });
    mocks.login.mockResolvedValue({ access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' });
    mocks.fetchUser.mockResolvedValue(user);
  });
  afterEach(() => vi.unstubAllEnvs());

  it('shows the published public credentials and fills the demo form', async () => {
    const wrapper = render();
    expect(wrapper.get('.demo-credentials').text()).toContain(demo.email);
    expect(wrapper.get('.demo-credentials').text()).toContain(demo.password);
    expect(wrapper.get('.demo-notice').text()).toContain('Shared public workspace');
    expect((wrapper.get('#email').element as HTMLInputElement).value).toBe(demo.email);
    expect((wrapper.get('#password').element as HTMLInputElement).value).toBe(demo.password);
    await wrapper.get('#email').setValue('other@example.com');
    await wrapper.get('#password').setValue('Other password');
    await wrapper.get('.demo-fill').trigger('click');
    expect((wrapper.get('#email').element as HTMLInputElement).value).toBe(demo.email);
    expect((wrapper.get('#password').element as HTMLInputElement).value).toBe(demo.password);
    expect(mocks.login).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it('signs in with the demo account, applies the theme, and honors a deep link', async () => {
    mocks.query = { redirect: '/products' };
    const wrapper = render();
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(mocks.login).toHaveBeenCalledWith(demo);
    expect(mocks.fetchUser).toHaveBeenCalledWith('access');
    expect(useAuthStore().accessToken).toBe('access');
    expect(document.documentElement.dataset.theme).toBe('light');
    expect(mocks.push).toHaveBeenCalledWith('/products');
    wrapper.unmount();
  });

  it('prevents duplicate requests and restores controls after a failed login', async () => {
    let rejectLogin!: (reason: Error) => void;
    mocks.login.mockImplementationOnce(() => new Promise((_resolve, reject) => { rejectLogin = reject; }));
    const wrapper = render();
    await wrapper.get('form').trigger('submit');
    await wrapper.get('form').trigger('submit');
    expect(mocks.login).toHaveBeenCalledTimes(1);
    expect(wrapper.get('#email').attributes('disabled')).toBeDefined();
    expect(wrapper.get('.btn-primary').attributes('aria-busy')).toBe('true');
    expect(wrapper.get('.demo-fill').attributes('disabled')).toBeDefined();
    rejectLogin(new Error('Demo is temporarily unavailable. Please try again.'));
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('temporarily unavailable');
    expect(wrapper.get('#email').attributes('disabled')).toBeUndefined();
    expect(wrapper.get('.btn-primary').attributes('aria-busy')).toBe('false');
    await wrapper.get('#email').setValue('visitor@example.com');
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    await wrapper.get('.demo-fill').trigger('click');
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(mocks.push).toHaveBeenCalledWith({ name: 'my-tasks' });
    wrapper.unmount();
  });

  it('shows and hides the password with an accessible toggle', async () => {
    const wrapper = render();
    expect(wrapper.get('#password').attributes('type')).toBe('password');
    await wrapper.get('button[aria-label="Show password"]').trigger('click');
    expect(wrapper.get('#password').attributes('type')).toBe('text');
    expect(wrapper.get('button[aria-label="Hide password"]').attributes('aria-pressed')).toBe('true');
    await wrapper.get('button[aria-label="Hide password"]').trigger('click');
    expect(wrapper.get('#password').attributes('type')).toBe('password');
    wrapper.unmount();
  });

  it.each(['false', 'auto', undefined])('keeps private installations free of demo credentials (%s)', (setting) => {
    vi.stubEnv('VITE_PUBLIC_DEMO', setting);
    vi.stubEnv('DEV', true);
    const wrapper = render();
    expect(wrapper.find('.demo-account').exists()).toBe(false);
    expect((wrapper.get('#email').element as HTMLInputElement).value).toBe('');
    expect((wrapper.get('#password').element as HTMLInputElement).value).toBe('');
    expect(wrapper.get('#login-heading').text()).toBe('Welcome to CRANE.');
    wrapper.unmount();
  });
});
