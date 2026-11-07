import { beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import View from '@/views/SupportAdvisorView.vue';
import AppSpinner from '@/components/AppSpinner.vue';
import { productService } from '@/services/product-service';
import { supportAdvisorService as service, type Context, type Assessment, type Component } from '@/services/support-advisor-service';

const { permission, routeGuard } = vi.hoisted(() => ({ permission: vi.fn(() => true), routeGuard: vi.fn() }));
vi.mock('vue-router', () => ({ onBeforeRouteLeave: routeGuard, useRoute: () => ({ params: { productId: 'product' } }) }));
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: { id: 'author' }, hasPermission: permission }) }));
vi.mock('@/services/product-service', () => ({ productService: { get: vi.fn() } }));
vi.mock('@/services/task-service', () => ({ taskService: { create: vi.fn() } }));
vi.mock('@/services/support-advisor-service', () => ({ supportAdvisorService: { context: vi.fn(), preview: vi.fn(), history: vi.fn(), create: vi.fn(), review: vi.fn(), report: vi.fn() } }));
const baseContext: Context = {
  context_version: 'a'.repeat(64), product: { name: 'Industrial system' }, release: { id: 'release', user_version: '1.0' },
  support: { support_start_date: '2026-01-01', support_end_date: '2038-01-01', justification_text: 'Existing manufacturer reasoning', expected_use_time_text: 'Fifteen years', comparable_products_text: null, third_party_support_constraints_text: null },
  components: [], evidence: [{ id: 'evidence', title: 'Expected-use study', external_url: null }], sboms: [], risk_assessments: [], vulnerabilities: [],
};
const makeAssessment = (changes: Partial<Assessment> = {}): Assessment => ({
  id: 'assessment', product_release_id: 'release', author_id: 'reviewee', created_at: '2026-11-07', status: 'pending_review', needs_refresh: false,
  inputs: { context_version: baseContext.context_version, product_release_id: 'release', support_start: '2026-01-01', support_end: '2038-01-01', expected_use_end: '2041-01-01', expected_use_basis: 'documented', rationale: 'Stored proportionality reasoning', evidence_ids: ['evidence'], remediations: [] },
  context_snapshot: baseContext, reviewer_id: null, reviewed_at: null, review_reason: null,
  result: { rules_version: 'support-advisor-1.0', findings: [], components: [], approval_blockers: [], legal_admissibility: 'review_required', technical_readiness: 'review_required', economic_attractiveness: 'not_assessed', general_minimum_met: true },
  ...changes,
});
const component = (changes: Partial<Component> = {}): Component => ({ id: 'component', link_id: 'link', name: 'Controller', version: '1.0', supplier_name: 'Acme', criticality: 'high', is_core_function: true, support_start_date: '2026-01-01', support_end_date: '2034-01-01', support_verified_at: '2026-01-01', support_reference_url: 'https://example.com/contract', support_scope: 'Patches for version 1.0', ...changes });
const mountView = () => mount(View, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } });
const button = (w: ReturnType<typeof mountView>, text: string) => w.findAll('button').find(b => b.text().includes(text))!;
beforeEach(() => {
  vi.resetAllMocks(); permission.mockReturnValue(true);
  vi.mocked(productService.get).mockResolvedValue({ name: 'Industrial system', releases: [{ id: 'release', system_version: 1, user_version: '1.0' }, { id: 'release-2', system_version: 2, user_version: '2.0' }] } as Awaited<ReturnType<typeof productService.get>>);
  vi.mocked(service.context).mockResolvedValue(structuredClone(baseContext));
  vi.mocked(service.history).mockResolvedValue([]);
  vi.mocked(service.preview).mockResolvedValue(makeAssessment().result);
  vi.mocked(service.create).mockResolvedValue(makeAssessment({ author_id: 'author' }));
  Element.prototype.scrollIntoView = vi.fn();
});
it('prefills manufacturer records without inventing expected dates and saves the source version', async () => {
  const w = mountView(); await flushPromises();
  expect(w.text()).toContain('Industrial system'); expect(w.text()).toContain('Fifteen years');
  expect((w.get('#support-start').element as HTMLInputElement).value).toBe('2026-01-01');
  expect((w.get('#expected-end').element as HTMLInputElement).value).toBe('');
  await w.get('#expected-end').setValue('2041-01-01');
  await w.get('#support-assessment-form').trigger('submit'); await flushPromises();
  expect(service.create).toHaveBeenCalledWith('product', expect.objectContaining({ context_version: 'a'.repeat(64), expected_use_end: '2041-01-01' }));
  expect(w.text()).toContain('Assessment saved for independent review.');
  expect(w.text()).toContain('Authors cannot approve their own decisions.');
  expect(service.history).toHaveBeenCalledTimes(1);
});
it('blocks stale approvals with an explanation and exports stored reports', async () => {
  vi.mocked(service.history).mockResolvedValue([makeAssessment({ needs_refresh: true })]);
  const w = mountView(); await flushPromises(); expect(w.text()).toContain('SP-007');
  expect((button(w, 'Approve decision record').element as HTMLButtonElement).disabled).toBe(true);
  expect(w.text()).toContain('save a new assessment');
  await button(w, 'Export report').trigger('click'); await flushPromises();
  expect(service.report).toHaveBeenCalledWith('product', 'assessment');
});
it('preserves input on server errors and rejects incomplete remediation before submitting', async () => {
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, components: [component()] });
  vi.mocked(service.create).mockRejectedValue({ response: { data: { error: { message: 'Source data changed while editing' } } } });
  const w = mountView(); await flushPromises();
  await w.get('#expected-end').setValue('2041-01-01');
  await w.get('#approach-link').setValue('independent_patching');
  await w.get('#support-assessment-form').trigger('submit'); await flushPromises();
  expect(service.create).not.toHaveBeenCalled();
  expect(w.get('[role="alert"]').text()).toContain('at least one evidence');
  await w.get('#approach-link').setValue('');
  await w.get('#support-assessment-form').trigger('submit'); await flushPromises();
  expect(w.get('[role="alert"]').text()).toContain('Source data changed');
  expect((w.get('#expected-end').element as HTMLInputElement).value).toBe('2041-01-01');
});
it('asks before discarding edits and retains them when canceled', async () => {
  const w = mountView(); await flushPromises();
  await w.get('#expected-end').setValue('2041-01-01');
  await button(w, 'Refresh source records').trigger('click'); await flushPromises();
  expect(document.body.textContent).toContain('Discard unsaved assessment changes?');
  expect(service.context).toHaveBeenCalledTimes(1);
  const keep = Array.from(document.body.querySelectorAll('button')).find(b => b.textContent?.includes('Keep editing'))!;
  keep.click(); await flushPromises();
  expect((w.get('#expected-end').element as HTMLInputElement).value).toBe('2041-01-01');
  await button(w, 'Refresh source records').trigger('click'); await flushPromises();
  const discard = Array.from(document.body.querySelectorAll('button')).find(b => b.textContent?.includes('Discard and continue'))!;
  discard.click(); await flushPromises();
  expect(service.context).toHaveBeenCalledTimes(2);
  expect((w.get('#expected-end').element as HTMLInputElement).value).toBe('');
  w.unmount();
});
it('filters component coverage without treating unknown commitments as covered', async () => {
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, components: [component(), component({ id: 'other', link_id: 'other', name: 'Sensor', supplier_name: 'Beta', criticality: 'low', is_core_function: false, support_verified_at: null })] });
  const w = mountView(); await flushPromises();
  expect(w.findAll('.component-row')).toHaveLength(2);
  expect(w.text()).toContain('Unknown / unverified');
  await w.get('input[type="search"]').setValue('beta');
  expect(w.findAll('.component-row')).toHaveLength(1);
  await w.get('input[type="search"]').setValue('absent');
  expect(w.text()).toContain('No components match');
  await button(w, 'Clear filters').trigger('click');
  await w.get('.check input').setValue(true);
  expect(w.findAll('.component-row')).toHaveLength(1);
  expect(w.get('.component-row').text()).toContain('Controller');
});
it('shows only the selected release history and resolves document titles from its snapshot', async () => {
  vi.mocked(service.history).mockResolvedValue([makeAssessment(), makeAssessment({ id: 'old', created_at: '2026-10-01', status: 'returned' }), makeAssessment({ id: 'different-release', product_release_id: 'release-2' })]);
  const w = mountView(); await flushPromises();
  expect(w.findAll('.version-item')).toHaveLength(2);
  expect(w.text()).toContain('Expected-use study');
  await w.findAll('.version-item')[1].trigger('click');
  expect(w.get('.decision-heading h3').text()).toBe('Returned');
});
it('requires review reasoning and records the returned result without another history fetch', async () => {
  vi.mocked(service.history).mockResolvedValue([makeAssessment()]);
  vi.mocked(service.review).mockResolvedValue(makeAssessment({ status: 'approved', reviewer_id: 'author', review_reason: 'Evidence reviewed independently' }));
  const w = mountView(); await flushPromises();
  expect((button(w, 'Approve decision record').element as HTMLButtonElement).disabled).toBe(true);
  await w.get('#review-assessment').setValue('Evidence reviewed independently');
  await w.get('.review-form').trigger('submit'); await flushPromises();
  expect(service.review).toHaveBeenCalledWith('product', 'assessment', 'approved', 'Evidence reviewed independently');
  expect(w.text()).toContain('Reviewer decision recorded.');
  expect(w.find('.review-form').exists()).toBe(false);
});
it('allows read-only users to search coverage while disabling assessment edits', async () => {
  permission.mockImplementation((key?: string) => key !== 'support_period_write');
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, components: [component()] });
  const w = mountView(); await flushPromises();
  expect((w.get('#support-rationale').element as HTMLTextAreaElement).readOnly).toBe(true);
  expect((w.get('input[type="search"]').element as HTMLInputElement).disabled).toBe(false);
  expect(w.text()).toContain('You have read-only access');
  expect(w.find('button[type="submit"]').exists()).toBe(false);
});
it('renders a single accessible shared spinner', () => {
  const w = mount(AppSpinner, { props: { label: 'Loading support context' } });
  expect(w.findAll('[role="status"]')).toHaveLength(1);
  expect(w.get('[role="status"]').attributes('aria-label')).toBe('Loading support context');
});

it('keeps release scope unchanged when a release switch is canceled', async () => {
  const w = mountView(); await flushPromises();
  await w.get('#expected-end').setValue('2041-01-01');
  await w.get('#advisor-release').setValue('release-2'); await flushPromises();
  expect((w.get('#advisor-release').element as HTMLSelectElement).value).toBe('release');
  const keep = Array.from(document.body.querySelectorAll('button')).find(b => b.textContent?.includes('Keep editing'))!;
  keep.click(); await flushPromises();
  expect(service.context).toHaveBeenCalledTimes(1);
  expect((w.get('#expected-end').element as HTMLInputElement).value).toBe('2041-01-01');
  w.unmount();
});
it('shows the no-release recovery path and retries an initial loading error', async () => {
  vi.mocked(productService.get).mockRejectedValueOnce(new Error('Connection interrupted'));
  const w = mountView(); await flushPromises();
  expect(w.get('[role="alert"]').text()).toContain('Connection interrupted');
  await button(w, 'Try again').trigger('click'); await flushPromises();
  expect(w.find('#support-rationale').exists()).toBe(true);
  w.unmount();
  vi.mocked(productService.get).mockResolvedValue({ name: 'Industrial system', releases: [] } as unknown as Awaited<ReturnType<typeof productService.get>>);
  const empty = mountView(); await flushPromises();
  expect(empty.text()).toContain('Create a product release first');
  expect(empty.find('#support-assessment-form').exists()).toBe(false);
});

it('protects unsaved changes when leaving the product advisor', async () => {
  const w = mountView(); await flushPromises();
  const guard = routeGuard.mock.calls[0][0] as () => boolean | Promise<boolean>;
  expect(guard()).toBe(true);
  await w.get('#expected-end').setValue('2041-01-01');
  const pending = guard(); await flushPromises();
  const discard = Array.from(document.body.querySelectorAll('button')).find(b => b.textContent?.includes('Discard and continue'))!;
  discard.click(); await flushPromises();
  await expect(pending).resolves.toBe(true);
  w.unmount();
});

it('checks a draft without saving a version and invalidates results after edits', async () => {
  vi.mocked(service.preview).mockResolvedValue({ ...makeAssessment().result,
    findings: [{ rule: 'SP-006', message: 'Documented expected use is missing' }], approval_blockers: ['SP-006'],
  });
  const w = mountView(); await flushPromises();
  await w.get('#expected-end').setValue('2041-01-01');
  await button(w, 'Check draft').trigger('click'); await flushPromises();
  expect(service.preview).toHaveBeenCalledWith('product', expect.objectContaining({ expected_use_end: '2041-01-01' }));
  expect(service.create).not.toHaveBeenCalled();
  expect(w.get('#draft-check').text()).toContain('Actions needed before approval');
  expect(w.get('#draft-check').text()).toContain('Complete supporting evidence');
  await w.get('#support-rationale').setValue('Updated proportionality reasoning');
  expect(w.get('#draft-check').text()).toContain('Changes need rechecking');
  expect(w.get('#draft-check').text()).not.toContain('Documented expected use is missing');
});
it('revises a saved assessment with fresh sources and excludes unavailable evidence and changed components', async () => {
  const snapshot = structuredClone(baseContext);
  snapshot.components = [component()];
  const original = makeAssessment({ status: 'returned', context_snapshot: snapshot,
    inputs: { ...makeAssessment().inputs, evidence_ids: ['evidence', 'removed-evidence'], remediations: [
      { component_link_id: 'link', approach: 'replacement', rationale: 'Replace with maintained controller', evidence_ids: ['evidence'] },
    ] },
  });
  vi.mocked(service.history).mockResolvedValue([original]);
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, context_version: 'b'.repeat(64), components: [component({ version: '2.0' })] });
  const w = mountView(); await flushPromises();
  await button(w, 'Start a revision').trigger('click'); await flushPromises();
  expect(service.context).toHaveBeenCalledTimes(2);
  expect((w.get('#support-rationale').element as HTMLTextAreaElement).value).toBe('Stored proportionality reasoning');
  expect(w.text()).toContain('New draft from a saved assessment');
  expect((w.get('#approach-link').element as HTMLSelectElement).value).toBe('');
  await w.get('#support-assessment-form').trigger('submit'); await flushPromises();
  expect(service.create).toHaveBeenCalledWith('product', expect.objectContaining({ context_version: 'b'.repeat(64), evidence_ids: ['evidence'], remediations: [] }));
  expect(original.inputs.evidence_ids).toEqual(['evidence', 'removed-evidence']);
  expect(original.inputs.remediations).toHaveLength(1);
});
it('filters gaps separately from unverified commitments and covered windows', async () => {
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, components: [component(), component({ id: 'unknown', link_id: 'unknown', name: 'Unknown library', support_verified_at: null }), component({ id: 'covered', link_id: 'covered', name: 'Covered library', support_end_date: '2045-01-01' })] });
  const w = mountView(); await flushPromises();
  await w.get('.coverage-filter select').setValue('gaps');
  expect(w.findAll('.component-row')).toHaveLength(1);
  expect(w.get('.component-row').text()).toContain('Controller');
  await w.get('.coverage-filter select').setValue('unknown');
  expect(w.get('.component-row').text()).toContain('Unknown library');
  await w.get('.coverage-filter select').setValue('covered');
  expect(w.get('.component-row').text()).toContain('Covered library');
});
it('requires confirmation before replacing unsaved work with a revision', async () => {
  vi.mocked(service.history).mockResolvedValue([makeAssessment({ status: 'returned' })]);
  const w = mountView(); await flushPromises();
  await w.get('#support-rationale').setValue('Keep my current draft reasoning');
  await button(w, 'Start a revision').trigger('click'); await flushPromises();
  expect(document.body.textContent).toContain('Discard unsaved assessment changes?');
  expect(service.context).toHaveBeenCalledTimes(1);
  const discard = Array.from(document.body.querySelectorAll('button')).find(b => b.textContent?.includes('Discard and continue'))!;
  discard.click(); await flushPromises();
  expect((w.get('#support-rationale').element as HTMLTextAreaElement).value).toBe('Stored proportionality reasoning');
  w.unmount();
});

it('pages large inventories while preserving remediation edits and reveals invalid off-page work', async () => {
  vi.mocked(service.context).mockResolvedValue({ ...baseContext, components: Array.from({ length: 24 }, (_, i) => component({ id: `component-${i}`, link_id: `link-${i}`, name: `Controller ${i}` })) });
  const w = mountView(); await flushPromises();
  expect(w.findAll('.component-row')).toHaveLength(20);
  expect(w.get('.component-pagination').text()).toContain('1–20 of 24');
  await w.get('[aria-label="Next component page"]').trigger('click');
  expect(w.findAll('.component-row')).toHaveLength(4);
  await w.get('#approach-link-20').setValue('independent_patching');
  await w.get('[aria-label="Previous component page"]').trigger('click');
  await w.get('#expected-end').setValue('2041-01-01');
  await w.get('#support-assessment-form').trigger('submit'); await flushPromises();
  expect(service.create).not.toHaveBeenCalled();
  expect(w.get('.component-pagination').text()).toContain('21–24 of 24');
  expect((w.get('#approach-link-20').element as HTMLSelectElement).value).toBe('independent_patching');
  await w.get('input[type="search"]').setValue('Controller 0');
  expect(w.findAll('.component-row')).toHaveLength(1);
  expect(w.get('.component-row').text()).toContain('Controller 0');
});
it('removes previous check results if a recheck fails', async () => {
  const w = mountView(); await flushPromises();
  await w.get('#expected-end').setValue('2041-01-01');
  await button(w, 'Check draft').trigger('click'); await flushPromises();
  expect(w.get('#draft-check').text()).toContain('Checked draft');
  vi.mocked(service.preview).mockRejectedValue({ response: { status: 409, data: { error: { message: 'Source data changed while editing' } } } });
  await button(w, 'Check again').trigger('click'); await flushPromises();
  expect(w.get('#draft-check').text()).not.toContain('Checked draft');
  expect(w.get('[role="alert"]').text()).toContain('Source data changed');
});
