import { useEffect, useState } from "react";
import type { JobInfo } from "../shared/types";
import { CURRENT_JOB_KEY } from "../shared/types";

// The background worker keeps the current job in chrome.storage.session.
// Read it once on mount (the panel may open after the job was captured) and
// follow updates via onChanged.
export function useCurrentJob(): JobInfo | null {
  const [job, setJob] = useState<JobInfo | null>(null);

  useEffect(() => {
    void chrome.storage.session.get(CURRENT_JOB_KEY).then((items) => {
      setJob((items[CURRENT_JOB_KEY] as JobInfo | undefined) ?? null);
    });

    const onChanged = (
      changes: { [key: string]: chrome.storage.StorageChange },
      area: string,
    ) => {
      if (area !== "session" || !(CURRENT_JOB_KEY in changes)) return;
      setJob((changes[CURRENT_JOB_KEY].newValue as JobInfo | undefined) ?? null);
    };
    chrome.storage.onChanged.addListener(onChanged);
    return () => chrome.storage.onChanged.removeListener(onChanged);
  }, []);

  return job;
}
