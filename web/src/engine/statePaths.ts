// Ported from pipeline/src/zce/engine/state_paths.py. Keep in step (shared/fixtures/state_paths.json).

const SB79_STANDARDS: Record<string, [number, number, number]> = {
  "1-quarter": [75, 120, 3.5],
  "1-half": [65, 100, 3],
  "2-quarter": [65, 100, 3],
  "2-half": [55, 80, 2.5],
};
const QUARTER_MILE_FT = 1320;
const HALF_MILE_FT = 2640;
const ADJACENT_FT = 200;
const MIN_HOMES = 5;
const SQFT_PER_ACRE = 43560;

export function sb79Units(
  areaSqft: number,
  distT1Ft: number | null,
  distT2Ft: number | null,
  zoneEligible: boolean,
  halfMileApplies: boolean,
  grossSqftPerUnit: number,
): number | null {
  if (!zoneEligible) return null;
  let best: number | null = null;
  for (const [tier, dist] of [[1, distT1Ft], [2, distT2Ft]] as [number, number | null][]) {
    if (dist === null) continue;
    let band: string;
    if (dist <= QUARTER_MILE_FT) band = "quarter";
    else if (dist <= HALF_MILE_FT && halfMileApplies) band = "half";
    else continue;
    let [, perAcre, far] = SB79_STANDARDS[`${tier}-${band}`];
    if (dist <= ADJACENT_FT) [perAcre, far] = [perAcre + 40, far + 1];
    const units = Math.min(Math.floor((areaSqft / SQFT_PER_ACRE) * perAcre), Math.floor((areaSqft * far) / grossSqftPerUnit));
    if (best === null || units > best) best = units;
  }
  return best !== null && best >= MIN_HOMES ? best : null;
}

export function densityBonusUnits(limits: Record<string, number | null>, share: number): number | null {
  const base = ["density", "lot_area_per_unit"].map((k) => limits[k]).filter((v): v is number => v !== null && v !== undefined);
  if (!base.length || Math.min(...base) < MIN_HOMES) return null;
  return Math.ceil(Number((Math.min(...base) * (1 + share)).toFixed(6)));
}
