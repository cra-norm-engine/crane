import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import DependencyTrackSettings from '@/components/DependencyTrackSettings.vue';
import { dependencyTrackService as service } from '@/services/dependency-track-service';

vi.mock('@/services/dependency-track-service', () => ({ dependencyTrackService: {
  list: vi.fn(), sboms: vi.fn(), test: vi.fn(), connect: vi.fn(), sync: vi.fn(), schedule: vi.fn(), disconnect: vi.fn(),
} }));
const connection = { id: 'connection', server_url: 'https://dtrack.example', project_id: 'project', project_name: 'Product · 1.0', sbom_record_id: 'sbom', automatic_sync: true, last_attempt_at: null, last_synced_at: null, last_error: null, last_result: null };

describe('Dependency-Track Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(service.list).mockResolvedValue([]);
    vi.mocked(service.sboms).mockResolvedValue([{ id: 'sbom', label: 'Product · 1.0 · sbom.json' }]);
    vi.mocked(service.test).mockResolvedValue([{ uuid: 'project', name: 'Product', version: '1.0' }]);
    vi.mocked(service.connect).mockResolvedValue(connection);
    vi.mocked(service.sync).mockResolvedValue({ ...connection, last_synced_at: '2026-09-11T00:00:00Z', last_result: { created: 2, updated: 0, unchanged: 0, stale: 0, assessment_conflicts: [] } });
  });

  it('tests credentials, selects named scopes, connects and syncs without a CRANE key', async () => {
    const wrapper = mount(DependencyTrackSettings, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    await wrapper.get('#dt-url').setValue('https://dtrack.example');
    await wrapper.get('#dt-api-key').setValue('secret');
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.text()).toContain('Connection verified');
    await wrapper.get('#dt-project').setValue('project');
    await wrapper.get('#dt-sbom').setValue('sbom');
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(service.connect).toHaveBeenCalledWith({ server_url: 'https://dtrack.example', api_key: 'secret', project_id: 'project', sbom_record_id: 'sbom', automatic_sync: true });
    expect(service.sync).toHaveBeenCalledWith('connection');
    expect(wrapper.text()).toContain('2 added');
    expect((wrapper.get('#dt-api-key').element as HTMLInputElement).value).toBe('');
    wrapper.unmount();
  });

  it('invalidates project selection when credentials change and offers retry on load failure', async () => {
    vi.mocked(service.list).mockRejectedValueOnce(new Error('offline'));
    const wrapper = mount(DependencyTrackSettings, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('Retry');
    await wrapper.get('[role="alert"] button').trigger('click');
    await flushPromises();
    await wrapper.get('#dt-url').setValue('https://dtrack.example');
    await wrapper.get('#dt-api-key').setValue('secret');
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.find('#dt-project').exists()).toBe(true);
    await wrapper.get('#dt-api-key').setValue('changed');
    expect(wrapper.find('#dt-project').exists()).toBe(false);
    wrapper.unmount();
  });
});
