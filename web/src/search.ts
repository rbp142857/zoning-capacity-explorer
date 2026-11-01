// Address search: an accessible combobox (WAI-ARIA "combobox with listbox").
//
// Keyboard: type at least 3 characters, Down/Up to move through matches,
// Enter to pick, Escape to close. Screen readers hear how many matches there
// are and which one is highlighted (aria-activedescendant).
// The address list (~340 kB) loads the first time the box gets focus.

export interface AddressIndex {
  address: string[];
  pid: number[];
  lng: number[];
  lat: number[];
}

export interface SearchHit {
  pid: number;
  address: string;
  lng: number;
  lat: number;
}

const MAX_RESULTS = 8;

/** Matches: every word typed must appear; addresses starting with the query rank first. */
export function searchAddresses(index: AddressIndex, query: string, parcelIds: string[]): SearchHit[] {
  const q = query.trim().toUpperCase().replace(/,/g, " ").replace(/\s+/g, " ");
  if (q.length < 3) return [];
  const words = q.split(" ");
  const starts: SearchHit[] = [];
  const contains: SearchHit[] = [];
  for (let i = 0; i < index.address.length && starts.length < MAX_RESULTS; i++) {
    const a = index.address[i];
    if (!words.every((w) => a.includes(w))) continue;
    const hit = { pid: index.pid[i], address: a, lng: index.lng[i], lat: index.lat[i] };
    (a.startsWith(q) ? starts : contains).push(hit);
  }
  // Also accept an assessor parcel number (AIN), with or without dashes.
  const digits = q.replace(/-/g, "");
  if (/^\d{10}$/.test(digits)) {
    const pid = parcelIds.indexOf(digits);
    const i = index.pid.indexOf(pid);
    if (pid >= 0 && i >= 0) starts.unshift({ pid, address: `Lot ${digits} (${index.address[i]})`, lng: index.lng[i], lat: index.lat[i] });
  }
  return [...starts, ...contains].slice(0, MAX_RESULTS);
}

export function setupSearch(
  input: HTMLInputElement,
  list: HTMLUListElement,
  status: HTMLElement,
  loadIndex: () => Promise<AddressIndex>,
  parcelIds: () => string[],
  onPick: (hit: SearchHit) => void,
): { reset(): void } {
  let index: AddressIndex | null = null;
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

  // Load the list once, on first focus or first keystroke (whichever comes
  // first); every caller awaits the same promise.
  let loading: Promise<AddressIndex | null> | null = null;
  const ensureIndex = () => {
    if (loading) return loading;
    const mine: Promise<AddressIndex | null> = loadIndex()
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
  input.addEventListener("focus", () => void ensureIndex());

  input.addEventListener("input", async () => {
    if (!index && !(await ensureIndex())) return;
    hits = searchAddresses(index as AddressIndex, input.value, parcelIds());
    active = -1;
    render();
    const q = input.value.trim();
    status.textContent = q.length < 3 ? "" : hits.length ? `${hits.length} matches. Use the arrow keys to choose.` : "No matching address.";
  });

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
      if (document.activeElement === input) void ensureIndex();
    },
  };
}
