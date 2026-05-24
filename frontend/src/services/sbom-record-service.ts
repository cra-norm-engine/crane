import { apiClient } from "@/services/api";
import type {
  SbomRecordCreate,
  SbomRecordRead,
  SbomRecordUpdate,
  SbomScanResult,
  SbomVulnerabilityFindingRead,
} from "@/types/product";

export const sbomRecordService = {
  async list(opts?: { productReleaseId?: string; productId?: string }): Promise<SbomRecordRead[]> {
    const params: Record<string, string> = {};
    if (opts?.productReleaseId) params.product_release_id = opts.productReleaseId;
    else if (opts?.productId) params.product_id = opts.productId;
    const { data } = await apiClient.get<SbomRecordRead[]>("/sbom-records/", {
      params: Object.keys(params).length ? params : undefined,
    });
    return data;
  },

  async get(sbomId: string): Promise<SbomRecordRead> {
    const { data } = await apiClient.get<SbomRecordRead>(`/sbom-records/${sbomId}`);
    return data;
  },

  async create(payload: SbomRecordCreate): Promise<SbomRecordRead> {
    const { data } = await apiClient.post<SbomRecordRead>("/sbom-records/", payload);
    return data;
  },

  async update(sbomId: string, payload: SbomRecordUpdate): Promise<SbomRecordRead> {
    const { data } = await apiClient.put<SbomRecordRead>(`/sbom-records/${sbomId}`, payload);
    return data;
  },

  async remove(sbomId: string): Promise<void> {
    await apiClient.delete(`/sbom-records/${sbomId}`);
  },

  /** Trigger a multi-scanner vulnerability scan (OSV + Trivy + NVD) for this SBOM (CRA Art. 13(2)).
   *  Extended timeout: Trivy downloads its DB on first cold run; NVD enrichment adds latency. */
  async scanVulnerabilities(sbomId: string): Promise<SbomScanResult> {
    const { data } = await apiClient.post<SbomScanResult>(
      `/sbom-records/${sbomId}/scan-vulnerabilities`,
      null,
      { timeout: 300_000 },  // 5 minutes — Trivy + NVD enrichment can take 2–3 min cold
    );
    return data;
  },

  /** List all CVE findings discovered during vulnerability scans of this SBOM. */
  async listVulnerabilityFindings(sbomId: string): Promise<SbomVulnerabilityFindingRead[]> {
    const { data } = await apiClient.get<SbomVulnerabilityFindingRead[]>(
      `/sbom-records/${sbomId}/vulnerability-findings`,
    );
    return data;
  },
};
