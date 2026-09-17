import { useEffect, useState } from "react";

import { subscribeToApiWakeState } from "../lib/api";

export function ApiWakingBanner() {
  const [waking, setWaking] = useState(false);

  useEffect(() => subscribeToApiWakeState(setWaking), []);

  if (!waking) return null;

  return (
    <div className="fixed inset-x-0 top-0 z-50 bg-ink px-4 py-2 text-center font-mono text-[11px] uppercase tracking-[0.14em] text-paper-raised">
      Waking up the SmartLearn server, this can take up to a minute...
    </div>
  );
}
