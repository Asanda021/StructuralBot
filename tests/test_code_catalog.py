from codes.catalog import (
    IMPLEMENTED,
    METADATA_ONLY,
    all_code_packs,
    by_country,
    by_language,
    get_code_pack,
    is_implemented,
)


def test_catalog_covers_all_configured_languages():
    languages = {p.language for p in all_code_packs()}
    assert {"fa", "en", "tr", "ar", "ru", "de", "zh-CN"} <= languages


def test_iran_catalog_entries_require_edition_specific_adapters():
    assert not is_implemented("ir-seismic-2800-5")
    assert not is_implemented("ir-concrete-m9-1399")
    assert not is_implemented("ir-steel-m10-1401")


def test_non_implemented_codes_never_claim_compliance():
    pack = get_code_pack("tr-tbdy-2018")
    assert pack is not None
    assert pack.status == METADATA_ONLY
    assert not is_implemented("tr-tbdy-2018")


def test_country_and_language_filters_are_deterministic():
    assert any(p.code_id == "cn-gb-50010" for p in by_country("China"))
    assert any(p.code_id == "de-eurocodes-din" for p in by_language("de"))


def test_unknown_code_returns_none():
    assert get_code_pack("does-not-exist") is None
