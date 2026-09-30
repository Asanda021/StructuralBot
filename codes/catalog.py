"""StructuralBot multi-country design-code catalog.

This catalog is deliberately metadata-first. A code is marked IMPLEMENTED only
when a deterministic adapter and numeric regression tests exist in the repo.
Never silently fall back from one country's code to another country's rules.
"""

from dataclasses import dataclass
from typing import Optional


IMPLEMENTED = "IMPLEMENTED"
METADATA_ONLY = "METADATA_ONLY"


@dataclass(frozen=True)
class CodePack:
    code_id: str
    country: str
    language: str
    title: str
    edition: str
    family: str
    status: str
    scope: tuple[str, ...]
    note: str = ""


CODE_PACKS: tuple[CodePack, ...] = (
    CodePack(
        "ir-seismic-2800-5",
        "Iran", "fa",
        "استاندارد ۲۸۰۰ طراحی ساختمان‌ها در برابر زلزله",
        "Edition 5 / ابلاغ 1404-12-27", "Iran",
        METADATA_ONLY,
        ("seismic",),
        "Catalog entry only; edition-specific seismic adapter and numeric regression tests are not yet present.",
    ),
    CodePack(
        "ir-concrete-m9-1399",
        "Iran", "fa",
        "مبحث نهم مقررات ملی ساختمان — طرح و اجرای ساختمان‌های بتن‌آرمه",
        "1399", "Iran", METADATA_ONLY,
        ("concrete", "rebar", "detailing"),
        "Generic Iran concrete/rebar helpers exist, but this catalog entry is not yet an edition-specific compliance adapter.",
    ),
    CodePack(
        "ir-steel-m10-1401",
        "Iran", "fa",
        "مبحث دهم مقررات ملی ساختمان — طرح و اجرای ساختمان‌های فولادی",
        "1401", "Iran", METADATA_ONLY,
        ("steel", "detailing"),
        "Structural-steel material helpers exist, but an edition-specific M10 adapter and regression suite are not yet present.",
    ),
    CodePack(
        "ir-loads-m6",
        "Iran", "fa",
        "مبحث ششم مقررات ملی ساختمان — بارهای وارد بر ساختمان",
        "current project edition required", "Iran", METADATA_ONLY,
        ("loads",),
    ),
    CodePack(
        "tr-tbdy-2018",
        "Turkey", "tr",
        "Türkiye Bina Deprem Yönetmeliği (TBDY)",
        "2018", "Turkey", METADATA_ONLY,
        ("seismic",),
    ),
    CodePack(
        "tr-ts500",
        "Turkey", "tr",
        "TS 500 — Requirements for Design and Construction of Reinforced Concrete Structures",
        "TS 500", "Turkey", METADATA_ONLY,
        ("concrete", "rebar"),
    ),
    CodePack(
        "de-eurocodes-din",
        "Germany", "de",
        "Eurocodes with German National Annexes",
        "country edition required", "Eurocode/DIN", METADATA_ONLY,
        ("loads", "concrete", "steel", "geotechnical", "seismic"),
        "Eurocodes must be applied with the applicable German National Annex.",
    ),
    CodePack(
        "ru-sp-structural",
        "Russia", "ru",
        "SP/GOST structural design family",
        "country edition required", "SP/GOST", METADATA_ONLY,
        ("loads", "concrete", "steel", "seismic"),
    ),
    CodePack(
        "cn-gb-50010",
        "China", "zh-CN",
        "GB 50010 — Code for Design of Concrete Structures",
        "project edition required", "GB", METADATA_ONLY,
        ("concrete", "rebar"),
    ),
    CodePack(
        "cn-gb-50011",
        "China", "zh-CN",
        "GB 50011 — Code for Seismic Design of Buildings",
        "project edition required", "GB", METADATA_ONLY,
        ("seismic",),
    ),
    CodePack(
        "cn-gb-50017",
        "China", "zh-CN",
        "GB 50017 — Standard for Design of Steel Structures",
        "project edition required", "GB", METADATA_ONLY,
        ("steel",),
    ),
    CodePack(
        "us-aci318",
        "United States", "en",
        "ACI 318 — Building Code Requirements for Structural Concrete",
        "project edition required", "ACI", METADATA_ONLY,
        ("concrete", "rebar", "detailing"),
    ),
    CodePack(
        "us-asce7",
        "United States", "en",
        "ASCE/SEI 7 — Minimum Design Loads and Associated Criteria",
        "project edition required", "ASCE", METADATA_ONLY,
        ("loads", "seismic"),
    ),
    CodePack(
        "us-aisc360",
        "United States", "en",
        "AISC 360 — Specification for Structural Steel Buildings",
        "project edition required", "AISC", METADATA_ONLY,
        ("steel",),
    ),
    CodePack(
        "uk-eurocodes",
        "United Kingdom", "en",
        "Eurocodes with UK National Annexes",
        "country edition required", "Eurocode/BS EN", METADATA_ONLY,
        ("loads", "concrete", "steel", "geotechnical", "seismic"),
    ),
    CodePack(
        "sa-sbc",
        "Saudi Arabia", "ar",
        "Saudi Building Code — Structural provisions",
        "project edition required", "SBC", METADATA_ONLY,
        ("loads", "concrete", "steel", "seismic"),
    ),
    CodePack(
        "ae-uae-structural",
        "United Arab Emirates", "ar",
        "UAE structural/building regulations",
        "authority/project edition required", "UAE", METADATA_ONLY,
        ("loads", "concrete", "steel", "seismic"),
    ),
    CodePack(
        "eg-egyptian-code",
        "Egypt", "ar",
        "Egyptian Code for structural design",
        "authority/project edition required", "ECP", METADATA_ONLY,
        ("loads", "concrete", "steel", "seismic"),
    ),
)


def all_code_packs() -> tuple[CodePack, ...]:
    return CODE_PACKS


def get_code_pack(code_id: str) -> Optional[CodePack]:
    key = code_id.strip().lower()
    return next((p for p in CODE_PACKS if p.code_id.lower() == key), None)


def by_language(language: str) -> tuple[CodePack, ...]:
    return tuple(p for p in CODE_PACKS if p.language == language)


def by_country(country: str) -> tuple[CodePack, ...]:
    key = country.strip().lower()
    return tuple(p for p in CODE_PACKS if p.country.lower() == key)


def is_implemented(code_id: str) -> bool:
    pack = get_code_pack(code_id)
    return bool(pack and pack.status == IMPLEMENTED)


__all__ = [
    "IMPLEMENTED",
    "METADATA_ONLY",
    "CodePack",
    "CODE_PACKS",
    "all_code_packs",
    "get_code_pack",
    "by_language",
    "by_country",
    "is_implemented",
]
