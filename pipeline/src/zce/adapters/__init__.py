"""Data adapters turn one publisher's format into the project's common schema.

Zoning adapters are chosen per city by `sources.zoning.adapter` in city.yaml.
Each exposes attach_zoning(parcels, raw_dir, city) returning
(zone columns per lot, the zoning table for reports, data-quality notes).
"""

from zce.adapters import la_city_zoning, pasadena_zoning, scag_zoning

ZONING_ADAPTERS = {
    "la_city_zoning": la_city_zoning.attach_zoning,
    "pasadena_zoning": pasadena_zoning.attach_zoning,
    "scag_zoning": scag_zoning.attach_zoning,
}
