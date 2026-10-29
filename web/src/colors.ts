// Colors and classes for the three map views.
//
// Rules we follow (see LEARNING.md -> "Color-blind-safe maps"):
// - Amounts (homes allowed, new homes) use ONE hue, light -> dark, in classes.
// - Categories (what limits a lot) use at most three hues, because on a map
//   every color can sit next to every other one; three is the most our
//   palette keeps distinguishable for color-blind viewers (checked with a
//   validator, not by eye). More detail is available through "Highlight one limit".
// - "Housing not allowed" and "not modeled" are grays, never a hue.
// - Every color in the legend comes with a text label and a count.

export type Theme = "light" | "dark";

// Blue sequential ramp. In dark mode the order flips so small numbers sit
// close to the dark background and big numbers stand out.
const BLUE_LIGHT = ["#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"];
const BLUE_DARK = ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"];

export const NEUTRAL = {
  light: { zero: "#c3c2b7", notModeled: "#ecebe6", outline: "#fcfcfb" },
  dark: { zero: "#4a4a46", notModeled: "#2c2c2a", outline: "#1a1a19" },
};

/** A class is a range of values that shares one color: [min, max] inclusive (max null = and up). */
export interface ValueClass {
  min: number;
  max: number | null;
  label: string;
}

export const MAX_UNITS_CLASSES: ValueClass[] = [
  { min: 1, max: 1, label: "1 home" },
  { min: 2, max: 2, label: "2" },
  { min: 3, max: 4, label: "3–4" },
  { min: 5, max: 9, label: "5–9" },
  { min: 10, max: 24, label: "10–24" },
  { min: 25, max: 49, label: "25–49" },
  { min: 50, max: null, label: "50 or more" },
];

export const NET_NEW_CLASSES: ValueClass[] = [
  { min: 1, max: 1, label: "1 more home" },
  { min: 2, max: 2, label: "2" },
  { min: 3, max: 3, label: "3" },
  { min: 4, max: 9, label: "4–9" },
  { min: 10, max: 24, label: "10–24" },
  { min: 25, max: 49, label: "25–49" },
  { min: 50, max: null, label: "50 or more" },
];

export function rampFor(theme: Theme): string[] {
  return theme === "dark" ? BLUE_DARK : BLUE_LIGHT;
}

// --- What limits a lot ---------------------------------------------------------

// Three groups get the first three categorical slots (blue, orange, aqua).
export const CATEGORICAL = {
  light: ["#2a78d6", "#eb6834", "#1baf7a"],
  dark: ["#3987e5", "#d95926", "#199e70"],
};

export interface BindingGroup {
  id: string;
  label: string;
  members: string[]; // binding-constraint names from the pipeline
  slot: number | "zero"; // categorical slot, or the "not allowed" gray
}

export const BINDING_GROUPS: BindingGroup[] = [
  {
    id: "state",
    label: "State law sets the maximum (SB 9 or ADU law)",
    members: ["state_law:sb9", "state_law:adu"],
    slot: 0,
  },
  {
    id: "density",
    label: "City density rules (homes per lot, land per home)",
    members: ["density", "lot_area_per_unit"],
    slot: 1,
  },
  {
    id: "physical",
    label: "Building size or parking rules",
    members: ["envelope", "parking"],
    slot: 2,
  },
  { id: "none", label: "Housing not allowed", members: ["use_not_permitted"], slot: "zero" },
];

/** Plain-language names for each binding constraint (popups, highlight menu). */
export const BINDING_LABELS: Record<string, string> = {
  "state_law:sb9": "State law SB 9 (2 homes, or 4 with a lot split)",
  "state_law:adu": "State ADU law (house + ADU + junior ADU)",
  density: "City cap on homes per lot or per acre",
  lot_area_per_unit: "City minimum land per home",
  envelope: "Building size limits (setbacks, height, coverage, gardens)",
  parking: "Required parking takes the room",
  use_not_permitted: "Housing not allowed in this zone",
};
