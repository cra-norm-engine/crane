import { apiClient } from "./api";
import type {
  CertificationRecord,
  CertificationRecordCreate,
  CertificationRecordUpdate,
  CertificationStatus,
} from "@/types/certification-record";

export const certificationRecordService = {
  list(params?: { product_id?: string; status?: CertificationStatus }): Promise<CertificationRecord[]> {
    return apiClient.get("/certification-records/", { params }).then((r) => r.data);
  },

  get(id: string): Promise<CertificationRecord> {
    return apiClient.get(`/certification-records/${id}`).then((r) => r.data);
  },

  create(payload: CertificationRecordCreate): Promise<CertificationRecord> {
    return apiClient.post("/certification-records/", payload).then((r) => r.data);
  },

  update(id: string, payload: CertificationRecordUpdate): Promise<CertificationRecord> {
    return apiClient.patch(`/certification-records/${id}`, payload).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return apiClient.delete(`/certification-records/${id}`).then(() => undefined);
  },
};
