from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.annex_requirement import AnnexRequirement
from app.models.enums import AnnexPart


ANNEX_I_REQUIREMENTS: Sequence[dict[str, str | AnnexPart]] = (
    {
        "code": "ANNEX-I-PART-I-1",
        "title": "Risk-based cybersecurity by design",
        "description": "Products with digital elements shall be designed, developed and produced in such a way that they ensure an appropriate level of cybersecurity based on the risks.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-2",
        "title": "No known exploitable vulnerabilities",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall be made available on the market without known exploitable vulnerabilities.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-3",
        "title": "Secure by default configuration",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall be made available on the market with a secure by default configuration, unless otherwise agreed between manufacturer and business user in relation to a tailor-made product with digital elements, including the possibility to reset the product to its original state.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-4",
        "title": "Security updates and remediation capability",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall ensure that vulnerabilities can be addressed through security updates, including, where applicable, through automatic security updates that are installed within an appropriate timeframe enabled as a default setting, with a clear and easy-to-use opt-out mechanism, through the notification of available updates to users, and the option to temporarily postpone them.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-5",
        "title": "Protection from unauthorised access",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall ensure protection from unauthorised access by appropriate control mechanisms, including but not limited to authentication, identity or access management systems, and report on possible unauthorised access.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-6",
        "title": "Confidentiality of stored and transmitted data",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall protect the confidentiality of stored, transmitted or otherwise processed data, personal or other, such as by encrypting relevant data at rest or in transit by state of the art mechanisms, and by using other technical means.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-7",
        "title": "Integrity of data, commands and configuration",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall protect the integrity of stored, transmitted or otherwise processed data, personal or other, commands, programs and configuration against any manipulation or modification not authorised by the user, and report on corruptions.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-8",
        "title": "Data minimisation",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall process only data, personal or other, that are adequate, relevant and limited to what is necessary in relation to the intended purpose of the product with digital elements (data minimisation).",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-9",
        "title": "Availability and resilience of essential functions",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall protect the availability of essential and basic functions, also after an incident, including through resilience and mitigation measures against denial-of-service attacks.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-10",
        "title": "Limit impact on other devices and networks",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall minimise the negative impact by the products themselves or connected devices on the availability of services provided by other devices or networks.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-11",
        "title": "Limit attack surfaces",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall be designed, developed and produced to limit attack surfaces, including external interfaces.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-12",
        "title": "Incident impact reduction measures",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall be designed, developed and produced to reduce the impact of an incident using appropriate exploitation mitigation mechanisms and techniques.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-13",
        "title": "Security logging and monitoring",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall provide security related information by recording and monitoring relevant internal activity, including the access to or modification of data, services or functions, with an opt-out mechanism for the user.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-I-14",
        "title": "Secure data removal and transfer",
        "description": "On the basis of the cybersecurity risk assessment referred to in Article 13(2) and where applicable, products with digital elements shall provide the possibility for users to securely and easily remove on a permanent basis all data and settings and, where such data can be transferred to other products or systems, ensure that this is done in a secure manner.",
        "annex_part": AnnexPart.part_i,
    },
    {
        "code": "ANNEX-I-PART-II-1",
        "title": "Document vulnerabilities and components",
        "description": "Manufacturers of products with digital elements shall identify and document vulnerabilities and components contained in products with digital elements, including by drawing up a software bill of materials in a commonly used and machine-readable format covering at the very least the top-level dependencies of the products.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-2",
        "title": "Remediate vulnerabilities without delay",
        "description": "Manufacturers of products with digital elements shall, in relation to the risks posed to products with digital elements, address and remediate vulnerabilities without delay, including by providing security updates; where technically feasible, new security updates shall be provided separately from functionality updates.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-3",
        "title": "Regular security tests and reviews",
        "description": "Manufacturers of products with digital elements shall apply effective and regular tests and reviews of the security of the product with digital elements.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-4",
        "title": "Disclosure of fixed vulnerabilities",
        "description": "Manufacturers of products with digital elements shall, once a security update has been made available, share and publicly disclose information about fixed vulnerabilities, including a description of the vulnerabilities, information allowing users to identify the product with digital elements affected, the impacts of the vulnerabilities, their severity and clear and accessible information helping users to remediate the vulnerabilities; in duly justified cases, where manufacturers consider the security risks of publication to outweigh the security benefits, they may delay making public information regarding a fixed vulnerability until after users have been given the possibility to apply the relevant patch.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-5",
        "title": "Coordinated vulnerability disclosure policy",
        "description": "Manufacturers of products with digital elements shall put in place and enforce a policy on coordinated vulnerability disclosure.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-6",
        "title": "Vulnerability reporting contact and information sharing",
        "description": "Manufacturers of products with digital elements shall take measures to facilitate the sharing of information about potential vulnerabilities in their product with digital elements as well as in third-party components contained in that product, including by providing a contact address for the reporting of the vulnerabilities discovered in the product with digital elements.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-7",
        "title": "Secure update distribution mechanisms",
        "description": "Manufacturers of products with digital elements shall provide for mechanisms to securely distribute updates for products with digital elements to ensure that vulnerabilities are fixed or mitigated in a timely manner and, where applicable for security updates, in an automatic manner.",
        "annex_part": AnnexPart.part_ii,
    },
    {
        "code": "ANNEX-I-PART-II-8",
        "title": "Timely and free security updates with advisories",
        "description": "Manufacturers of products with digital elements shall ensure that, where security updates are available to address identified security issues, they are disseminated without delay and, unless otherwise agreed between a manufacturer and a business user in relation to a tailor-made product with digital elements, free of charge, accompanied by advisory messages providing users with the relevant information, including on potential action to be taken.",
        "annex_part": AnnexPart.part_ii,
    },
)


def sync_annex_i_requirements(db: Session) -> None:
    existing_by_code = {
        requirement.code: requirement for requirement in db.query(AnnexRequirement).all()
    }

    for item in ANNEX_I_REQUIREMENTS:
        code = item["code"]
        requirement = existing_by_code.get(code)
        if requirement is None:
            db.add(
                AnnexRequirement(
                    code=code,
                    title=item["title"],
                    description=item["description"],
                    annex_part=item["annex_part"],
                    is_active=True,
                )
            )
            continue

        requirement.title = item["title"]
        requirement.description = item["description"]
        requirement.annex_part = item["annex_part"]
        requirement.is_active = True

