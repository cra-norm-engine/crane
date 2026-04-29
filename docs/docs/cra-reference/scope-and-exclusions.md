---
id: scope-and-exclusions
title: Scope and Exclusions
sidebar_position: 2
---

# CRA Scope and Exclusions

## In-Scope Products

The CRA applies to **products with digital elements** (PDEs). A PDE is defined in Article 3(1) as:

> A software or hardware product and its remote data processing solutions, including software or hardware components to be placed on the market separately.

The defining characteristic is a **direct or indirect logical or physical data connection** to a device or network. Both consumer and professional/industrial products are within scope.

### Connectivity Criterion

The connectivity requirement is broad. A product with digital elements includes:

- Products that connect directly to the internet or a local network
- Products that connect to another device that connects to a network (indirect connectivity)
- Products that connect via Bluetooth, NFC, or other short-range radio protocols
- Software products that are installed on networked devices

Purely offline software with no network connectivity and no capability to receive updates remotely is unlikely to meet the connectivity criterion, but the specific facts of each product must be assessed.

## Excluded Categories

Article 2(2) and 2(3) list the following product categories as outside the CRA scope:

| Category | Basis |
|---|---|
| Medical devices regulated under Regulation (EU) 2017/745 | Article 2(2)(a) |
| In vitro diagnostic medical devices regulated under Regulation (EU) 2017/746 | Article 2(2)(b) |
| Civil aviation products regulated under Regulation (EU) 2018/1139 | Article 2(2)(c) |
| Automotive products regulated under Regulation (EU) 2019/2144 | Article 2(2)(d) |
| Marine equipment regulated under Directive 2014/90/EU | Article 2(2)(e) |
| Products for national security or military purposes | Article 2(3)(a) |
| Products for law enforcement purposes | Article 2(3)(b) |
| Products processed in the context of classified information | Article 2(3)(c) |

:::warning
Sector-specific exclusions require that the sector regulation provides equivalent or greater cybersecurity requirements. The exclusion is not automatic — it must be substantiated with reference to the specific sector regulation's cybersecurity provisions.
:::

## Free and Open Source Software

Software developed outside the course of a commercial activity is out of scope. Free and open source software (FOSS) supplied outside a commercial context — for example, software made available on a public repository without commercial support — is not within the CRA scope.

However, FOSS that is integrated into a commercial product is addressed through the manufacturer's obligations. Manufacturers are responsible for the cybersecurity of all components in their product, including FOSS components, and must account for them in their risk assessment and SBOM.

## Products Intended for Development Only

Software development tools, compilers, and similar products whose sole purpose is to assist in the development of other software are out of scope.

## Using the Scope Evaluation

The platform's [Scope Evaluation](/user-guide/scope-evaluation) workflow maps the above criteria to a structured questionnaire and generates a documented determination. The evaluation outcome is a recommendation; the manufacturer retains responsibility for the final classification.
