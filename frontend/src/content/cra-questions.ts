import type { CraLearningEdge, CraLearningNode } from "./cra-learning";

export type CraQuestionCategory = "scope" | "roles" | "classification" | "security" | "vulnerability" | "reporting" | "conformity" | "market" | "timeline" | "lifecycle";
export interface CraQuestion { id: string; category: CraQuestionCategory; question: string; concepts: string[] }

const q = (id: string, category: CraQuestionCategory, question: string, concepts: string[]): CraQuestion => ({ id, category, question, concepts });

export const craQuestionCategories: { id: CraQuestionCategory; label: string }[] = [
  { id: "scope", label: "Scope" }, { id: "roles", label: "Who is responsible" },
  { id: "classification", label: "Product classes" }, { id: "security", label: "Secure design" },
  { id: "vulnerability", label: "Vulnerabilities" }, { id: "reporting", label: "Incident reporting" },
  { id: "conformity", label: "Conformity" }, { id: "market", label: "After market entry" },
  { id: "timeline", label: "Dates" }, { id: "lifecycle", label: "End-to-end" },
];

export const craQuestions: CraQuestion[] = [
  q("S01", "scope", "When does software become a product with digital elements under the CRA?", ["software", "pde"]),
  q("S02", "scope", "Can a separately marketed software or hardware component fall within CRA scope?", ["component", "pde"]),
  q("S03", "scope", "When is a remote cloud function treated as part of a product with digital elements?", ["remote_processing", "pde"]),
  q("S04", "scope", "Why does an indirect network connection matter when deciding whether a product is in scope?", ["data_connection", "pde"]),
  q("S05", "scope", "What is the difference between placing a product on the market and making it available?", ["placing_market", "making_available"]),
  q("S06", "scope", "Can supplying a digital product free of charge still count as making it available commercially?", ["making_available", "commercial_activity"]),
  q("S07", "scope", "How do intended purpose and reasonably foreseeable use affect CRA scope?", ["intended_use", "pde"]),
  q("S08", "scope", "When is free and open-source software outside the CRA?", ["foss", "commercial_activity"]),
  q("S09", "scope", "Why can open-source software used in commercial activity receive different CRA treatment?", ["foss", "commercial_activity", "steward"]),
  q("S10", "scope", "Which sector-specific product areas are excluded or specially treated by Article 2?", ["sector_exclusions", "pde"]),

  q("R01", "roles", "Who carries the central CRA duties for product design, documentation and vulnerability handling?", ["manufacturer", "risk", "vulnerability_handling"]),
  q("R02", "roles", "When can an organisation be a manufacturer even if another company physically builds the product?", ["manufacturer"]),
  q("R03", "roles", "What may an authorised representative do, and what determines those tasks?", ["manufacturer", "authorised_rep"]),
  q("R04", "roles", "What must an importer verify before placing a third-country product on the Union market?", ["importer", "placing_market"]),
  q("R05", "roles", "How does a distributor's role differ from that of an importer or manufacturer?", ["economic_operator", "distributor", "importer", "manufacturer"]),
  q("R06", "roles", "Which actors are included under the CRA term economic operator?", ["economic_operator", "manufacturer", "authorised_rep", "importer", "distributor"]),
  q("R07", "roles", "What distinguishes an open-source software steward from a manufacturer?", ["foss", "steward", "manufacturer"]),
  q("R08", "roles", "When does a notified body become relevant to a CRA conformity assessment?", ["conformity", "notified_body"]),
  q("R09", "roles", "Which authority supervises products after they enter the market?", ["market_surveillance", "market_authority"]),
  q("R10", "roles", "How do the designated CSIRT and ENISA differ in the CRA reporting architecture?", ["reporting", "csirt", "reporting_platform", "enisa"]),

  q("C01", "classification", "How does CRA product classification change the available conformity route?", ["classification", "conformity"]),
  q("C02", "classification", "What are the three broad CRA product-classification outcomes?", ["classification", "other_products", "important", "critical"]),
  q("C03", "classification", "When may a product outside the important and critical lists use internal control?", ["other_products", "internal_control"]),
  q("C04", "classification", "Where are important products with digital elements listed?", ["important", "class_i", "class_ii"]),
  q("C05", "classification", "Why is the Class I conformity route conditional on standards or common specifications?", ["class_i", "conformity", "harmonised", "common_specs"]),
  q("C06", "classification", "Why does a Class II product require third-party conformity assessment?", ["class_ii", "conformity", "notified_body"]),
  q("C07", "classification", "Where are critical product categories identified?", ["classification", "critical"]),
  q("C08", "classification", "How can European cybersecurity certification affect a critical product?", ["critical", "cyber_certification"]),
  q("C09", "classification", "Is every product with digital elements an important or critical product?", ["classification", "other_products"]),
  q("C10", "classification", "Which legal lists and provisions should be checked before choosing an assessment procedure?", ["classification", "important", "critical", "conformity"]),

  q("D01", "security", "How must a manufacturer use cybersecurity risk assessment throughout development and maintenance?", ["manufacturer", "risk", "product_security"]),
  q("D02", "security", "Does the CRA prescribe one mandatory cybersecurity risk-assessment methodology?", ["risk"]),
  q("D03", "security", "What does an appropriate level of cybersecurity mean in the CRA structure?", ["risk", "product_security", "appropriate_security"]),
  q("D04", "security", "When must a product be supplied with a secure-by-default configuration?", ["product_security", "secure_default"]),
  q("D05", "security", "Does the CRA require a product to contain no vulnerabilities at all when marketed?", ["product_security", "known_exploitable"]),
  q("D06", "security", "Which CRA concept connects authentication and identity management to product security?", ["product_security", "access_control"]),
  q("D07", "security", "How does the CRA distinguish confidentiality protection from integrity protection?", ["product_security", "confidentiality", "integrity"]),
  q("D08", "security", "Why is data minimisation a cybersecurity requirement under the CRA?", ["product_security", "data_minimisation"]),
  q("D09", "security", "What must remain available after a cybersecurity incident?", ["product_security", "availability"]),
  q("D10", "security", "How do attack-surface limitation and security monitoring complement each other?", ["product_security", "attack_surface", "logging"]),

  q("V01", "vulnerability", "For how long must CRA vulnerability-handling requirements be performed?", ["vulnerability_handling", "support"]),
  q("V02", "vulnerability", "When may the CRA support period be shorter than five years?", ["support"]),
  q("V03", "vulnerability", "What minimum dependency depth and format does the CRA require for an SBOM?", ["vulnerability_handling", "sbom"]),
  q("V04", "vulnerability", "How quickly must a manufacturer remediate a vulnerability?", ["vulnerability_handling", "remediation"]),
  q("V05", "vulnerability", "When should a security update be separated from a functionality update?", ["remediation", "security_updates"]),
  q("V06", "vulnerability", "Must CRA security updates always be free of charge?", ["security_updates"]),
  q("V07", "vulnerability", "How long must an issued security update remain available to users?", ["security_updates", "update_availability"]),
  q("V08", "vulnerability", "What makes distribution of a security update CRA-compliant?", ["security_updates", "secure_distribution"]),
  q("V09", "vulnerability", "What is the relationship between a coordinated vulnerability disclosure policy and its contact point?", ["vulnerability_handling", "cvd_policy", "contact_point"]),
  q("V10", "vulnerability", "What must a manufacturer do when it discovers a vulnerability in an integrated third-party component?", ["manufacturer", "components", "upstream"]),

  q("P01", "reporting", "Which two types of security event trigger the CRA mandatory reporting process?", ["reporting", "active_vulnerability", "severe_incident"]),
  q("P02", "reporting", "Does every discovered vulnerability have to be reported under Article 14?", ["reporting", "active_vulnerability"]),
  q("P03", "reporting", "What evidence makes a vulnerability actively exploited for CRA purposes?", ["active_vulnerability"]),
  q("P04", "reporting", "What makes an incident affecting product security severe enough for CRA reporting?", ["severe_incident"]),
  q("P05", "reporting", "What is the first CRA reporting deadline after awareness of a reportable event?", ["reporting", "warning_24"]),
  q("P06", "reporting", "What is the progressive sequence from early warning to final report?", ["warning_24", "notice_72", "final_report"]),
  q("P07", "reporting", "How do final-report deadlines differ for an exploited vulnerability and a severe incident?", ["active_vulnerability", "final_report", "severe_incident"]),
  q("P08", "reporting", "When must affected users receive information about a reportable event?", ["reporting", "user_information"]),
  q("P09", "reporting", "Through which infrastructure are CRA reports submitted, and to whom are they routed?", ["reporting", "reporting_platform", "csirt", "enisa"]),
  q("P10", "reporting", "Are CRA reporting duties retroactive for exploitation known before they start applying?", ["reporting", "reporting_date"]),

  q("A01", "conformity", "How does product classification determine the conformity-assessment procedure?", ["classification", "conformity"]),
  q("A02", "conformity", "What is the internal-control route and which products can generally use it?", ["conformity", "internal_control", "other_products"]),
  q("A03", "conformity", "How do EU-type examination and conformity to type work together?", ["conformity", "eu_type", "conformity_type"]),
  q("A04", "conformity", "What is the full-quality-assurance conformity route?", ["conformity", "full_quality"]),
  q("A05", "conformity", "How can harmonised standards create a presumption of conformity?", ["harmonised", "conformity"]),
  q("A06", "conformity", "How can common specifications support presumption of conformity?", ["common_specs", "conformity"]),
  q("A07", "conformity", "How can a European cybersecurity certificate support CRA conformity?", ["cyber_certification", "conformity"]),
  q("A08", "conformity", "Which technical documentation must the manufacturer prepare for conformity?", ["manufacturer", "documentation"]),
  q("A09", "conformity", "What information and instructions must accompany a product?", ["manufacturer", "user_instructions"]),
  q("A10", "conformity", "What sequence connects conformity assessment, the EU declaration and CE marking?", ["conformity", "declaration", "ce"]),

  q("M01", "market", "What must happen before a product with digital elements is first placed on the Union market?", ["conformity", "declaration", "ce", "placing_market"]),
  q("M02", "market", "When can modifying an existing product create manufacturer obligations?", ["substantial_modification", "manufacturer"]),
  q("M03", "market", "How are identical spare parts treated under Commission CRA guidance?", ["component", "spare_parts"]),
  q("M04", "market", "What must an economic operator do when it believes a product is non-compliant?", ["economic_operator", "corrective_action"]),
  q("M05", "market", "When can corrective action include withdrawal or recall?", ["corrective_action", "withdrawal"]),
  q("M06", "market", "Who can require corrective action after evaluating a product?", ["market_surveillance", "corrective_action"]),
  q("M07", "market", "What is the purpose of CRA market surveillance?", ["cra", "market_surveillance"]),
  q("M08", "market", "What is a simultaneous coordinated control action or compliance sweep?", ["market_surveillance", "compliance_sweep"]),
  q("M09", "market", "How do CRA penalties reinforce market surveillance?", ["market_surveillance", "penalties"]),
  q("M10", "market", "How do importer and distributor checks help prevent non-compliant products reaching users?", ["importer", "economic_operator", "distributor", "corrective_action"]),

  q("T01", "timeline", "When did the Cyber Resilience Act enter into force?", ["cra", "entry_force"]),
  q("T02", "timeline", "Why is entry into force different from general application?", ["entry_force", "application_date"]),
  q("T03", "timeline", "When do the CRA notified-body provisions begin to apply?", ["entry_force", "notified_date"]),
  q("T04", "timeline", "When do mandatory vulnerability and incident reporting duties begin?", ["reporting", "reporting_date"]),
  q("T05", "timeline", "When do most CRA obligations generally begin to apply?", ["cra", "application_date"]),
  q("T06", "timeline", "What is the chronological order of the four main CRA milestones?", ["entry_force", "notified_date", "reporting_date", "application_date"]),
  q("T07", "timeline", "Which CRA duties apply before the general application date?", ["notified_date", "reporting_date", "application_date"]),
  q("T08", "timeline", "Must a manufacturer report exploitation already known before 11 September 2026?", ["reporting", "reporting_date"]),
  q("T09", "timeline", "How does the reporting start date affect an Article 14 implementation plan?", ["reporting_date", "reporting", "warning_24"]),
  q("T10", "timeline", "How much time separates the reporting start date from general CRA application?", ["reporting_date", "application_date"]),

  q("L01", "lifecycle", "What is the end-to-end CRA path from determining scope to placing a CE-marked product on the market?", ["pde", "classification", "conformity", "declaration", "ce", "placing_market"]),
  q("L02", "lifecycle", "How do risk assessment, essential requirements and technical documentation connect?", ["manufacturer", "risk", "product_security", "documentation"]),
  q("L03", "lifecycle", "How do pre-market security duties continue into post-market vulnerability handling?", ["product_security", "manufacturer", "vulnerability_handling", "support"]),
  q("L04", "lifecycle", "How does a component vulnerability move from discovery to an upstream notification and remediation?", ["components", "upstream", "manufacturer", "vulnerability_handling", "remediation"]),
  q("L05", "lifecycle", "How does an actively exploited vulnerability move through reporting and user notification?", ["active_vulnerability", "reporting", "warning_24", "notice_72", "final_report", "user_information"]),
  q("L06", "lifecycle", "How do classification, harmonised standards and CE marking fit together?", ["classification", "conformity", "harmonised", "declaration", "ce"]),
  q("L07", "lifecycle", "What happens when market surveillance finds a product that is not CRA-compliant?", ["market_surveillance", "corrective_action", "withdrawal"]),
  q("L08", "lifecycle", "How can a substantial modification change who carries manufacturer duties?", ["substantial_modification", "manufacturer", "risk"]),
  q("L09", "lifecycle", "How do the manufacturer, CSIRT, ENISA and affected users connect during CRA reporting?", ["manufacturer", "reporting", "csirt", "reporting_platform", "enisa", "user_information"]),
  q("L10", "lifecycle", "Which CRA controls cover a product from secure design through updates, conformity and market oversight?", ["product_security", "vulnerability_handling", "conformity", "market_surveillance"]),
];

export function validateCraQuestions(nodes: CraLearningNode[], edges: CraLearningEdge[]): string[] {
  const errors: string[] = [];
  const nodeIds = new Set(nodes.map(node => node.id));
  const connected = new Set(edges.flatMap(edge => [edge.from, edge.to]));
  const questionIds = new Set<string>();
  for (const item of craQuestions) {
    if (questionIds.has(item.id)) errors.push(`Duplicate question: ${item.id}`);
    questionIds.add(item.id);
    if (!item.question.endsWith("?")) errors.push(`Question has no question mark: ${item.id}`);
    for (const id of item.concepts) {
      if (!nodeIds.has(id)) errors.push(`Unknown concept: ${item.id}/${id}`);
      else if (!connected.has(id)) errors.push(`Disconnected concept: ${item.id}/${id}`);
    }
  }
  if (craQuestions.length !== 100) errors.push(`Expected 100 questions, found ${craQuestions.length}`);
  return errors;
}
