// Address search: an accessible combobox (WAI-ARIA "combobox with listbox").
//
// Keyboard: type at least 3 characters, Down/Up to move through matches,
// Enter to pick, Escape to close. Screen readers hear how many matches there
// are and which one is highlighted (aria-activedescendant).
// The address list (several MB for a big city) loads on the first keystroke.

export interface AddressIndex {
  text: string; // line i is the lot with pid offset + i, blank if it has no address
  starts: Uint32Array; // where each line starts in the text
  lng: Float32Array;
  lat: Float32Array;
  offset: number;
}

export function makeAddressIndex(text: string, lng: Float32Array, lat: Float32Array, offset: number): AddressIndex {
  const starts = new Uint32Array(lng.length);
  let at = 0;
  for (let i = 1; i < lng.length; i++) {
    at = text.indexOf("\n", at) + 1;
    starts[i] = at;
  }
  return { text, starts, lng, lat, offset };
}

export interface SearchHit {
  pid: number;
  address: string;
  lng: number;
  lat: number;
}

const MAX_RESULTS = 8;
const lineAt = (ix: AddressIndex, line: number) =>
  ix.text.substring(ix.starts[line], line + 1 < ix.starts.length ? ix.starts[line + 1] - 1 : ix.text.length);

/** The line of the text that a position falls on. */
function lineOf(ix: AddressIndex, position: number): number {
  let lo = 0;
  let hi = ix.starts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (ix.starts[mid] <= position) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

/** Matches: every word typed must appear; addresses starting with the query rank first. */
export function searchAddresses(index: AddressIndex[], query: string, findParcel: (digits: string) => number): SearchHit[] {
  const q = query.trim().toUpperCase().replace(/,/g, " ").replace(/\s+/g, " ");
  if (q.length < 3) return [];
  const words = q.split(" ");
  // Scan for the word likely to match the fewest lines: a house number if there is
  // one, otherwise the longest word.
  const rarity = (w: string) => (/\d/.test(w) ? 100 : 0) + w.length;
  const needle = words.reduce((a, b) => (rarity(b) > rarity(a) ? b : a));
  const starts: SearchHit[] = [];
  const contains: SearchHit[] = [];
  for (const ix of index) {
    let from = 0;
    while (starts.length < MAX_RESULTS) {
      const found = ix.text.indexOf(needle, from);
      if (found < 0) break;
      const line = lineOf(ix, found);
      const a = lineAt(ix, line);
      from = ix.starts[line] + a.length + 1;
      if (!words.every((w) => a.includes(w))) continue;
      const hit = { pid: ix.offset + line, address: a, lng: ix.lng[line], lat: ix.lat[line] };
      if (a.startsWith(q)) starts.push(hit);
      else if (contains.length < MAX_RESULTS) contains.push(hit);
    }
  }
  const byAddress = (x: SearchHit, y: SearchHit) => x.address.localeCompare(y.address);
  starts.sort(byAddress);
  contains.sort(byAddress);
  // Also accept an assessor parcel number (AIN), with or without dashes.
  const digits = q.replace(/-/g, "");
  if (/^\d{10}$/.test(digits)) {
    const pid = findParcel(digits);
    const ix = index.find((c) => pid >= c.offset && pid < c.offset + c.lng.length);
    if (pid >= 0 && ix) {
      const line = pid - ix.offset;
      const a = lineAt(ix, line);
      starts.unshift({ pid, address: a ? `Lot ${digits} (${a})` : `Lot ${digits} (no address on record)`, lng: ix.lng[line], lat: ix.lat[line] });
    }
  }
  return [...starts, ...contains].slice(0, MAX_RESULTS);
}

export function setupSearch(
  input: HTMLInputElement,
  list: HTMLUListElement,
  status: HTMLElement,
  loadIndex: () => Promise<AddressIndex[]>,
  findParcel: (digits: string) => number,
  onPick: (hit: SearchHit) => void,
): { reset(): void } {
  let index: AddressIndex[] | null = null;
  let hits: SearchHit[] = [];
  let active = -1;

  const close = () => {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    active = -1;
  };

  const render = () => {
    list.replaceChildren(
      ...hits.map((h, i) => {
        const li = document.createElement("li");
        li.id = `search-opt-${i}`;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", String(i === active));
        li.textContent = h.address;
        // mousedown (not click) so the input doesn't lose focus first.
        li.addEventListener("mousedown", (e) => {
          e.preventDefault();
          pick(i);
        });
        return li;
      }),
    );
    const open = hits.length > 0;
    list.hidden = !open;
    input.setAttribute("aria-expanded", String(open));
    if (active >= 0) input.setAttribute("aria-activedescendant", `search-opt-${active}`);
    else input.removeAttribute("aria-activedescendant");
  };

  const pick = (i: number) => {
    const hit = hits[i];
    if (!hit) return;
    input.value = hit.address;
    close();
    status.textContent = `Showing ${hit.address}.`;
    onPick(hit);
  };

  // Load the list once, on the first keystroke; every caller awaits the same promise.
  let loading: Promise<AddressIndex[] | null> | null = null;
  const ensureIndex = () => {
    if (loading) return loading;
    const mine: Promise<AddressIndex[] | null> = loadIndex()
      .then((i) => {
        if (loading === mine) index = i; // ignore a list for an old city selection
        return i;
      })
      .catch(() => {
        status.textContent = "Couldn't load the address list.";
        if (loading === mine) loading = null; // allow a retry
        return null;
      });
    loading = mine;
    return mine;
  };

  // Wait for a pause in typing: searching every city on each keystroke would add up.
  let typing: ReturnType<typeof setTimeout> | undefined;
  input.addEventListener("input", () => {
    clearTimeout(typing);
    typing = setTimeout(runSearch, index ? 120 : 0);
  });
  const runSearch = async () => {
    if (!index && !(await ensureIndex())) return;
    hits = searchAddresses(index as AddressIndex[], input.value, findParcel);
    active = -1;
    render();
    const q = input.value.trim();
    status.textContent = q.length < 3 ? "" : hits.length ? `${hits.length} matches. Use the arrow keys to choose.` : "No matching address.";
  };

  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && hits.length) {
      active = (active + 1) % hits.length;
      render();
      e.preventDefault();
    } else if (e.key === "ArrowUp" && hits.length) {
      active = (active - 1 + hits.length) % hits.length;
      render();
      e.preventDefault();
    } else if (e.key === "Enter") {
      if (hits.length) pick(active >= 0 ? active : 0);
      e.preventDefault();
    } else if (e.key === "Escape") {
      close();
    }
  });

  input.addEventListener("blur", () => setTimeout(close, 100));

  return {
    /** The selected cities changed: forget the list and any open matches. */
    reset() {
      index = null;
      loading = null;
      hits = [];
      close();
    },
  };
}
