// Shared shapes passed between content script -> background -> side panel.

export interface JobInfo {
  /** Numeric Wellfound job id, e.g. "4230970". Null if we couldn't find one. */
  jobId: string | null;
  /** Full /jobs/<id>-<slug> URL on wellfound.com. */
  jobUrl: string | null;
  title: string;
  company: {
    name: string;
    /** Slug from /company/<slug>. */
    slug: string | null;
    url: string | null;
    tagline: string | null;
  };
  /**
   * The raw items of the meta row under the title, in page order —
   * e.g. ["₹15L – ₹22.5L", "Remote (India)", "2 years of exp", "Full Time"].
   * Wellfound varies these per job, so we keep the raw list and best-effort
   * picks below.
   */
  metaItems: string[];
  compensation: string | null;
  location: string | null;
  experience: string | null;
  jobType: string | null;
  /** "Reposted: 1 month ago • Recruiter recently active" etc. */
  postedInfo: string | null;
  /**
   * The labelled grid under the header: "Remote Work Policy" -> "Remote only",
   * "Visa Sponsorship" -> "Not Available", ... (Skills excluded — see `skills`.)
   */
  fields: Record<string, string>;
  skills: string[];
  /** Plain text of #job-description. */
  description: string;
  /** mailto: addresses found in the description — for the future email feature. */
  emails: string[];
  /** When we read it (ms epoch). */
  capturedAt: number;
}

// Messages the content script sends to the background worker.
export type ContentMessage =
  | { type: "JOB_UPDATED"; job: JobInfo }
  | { type: "JOB_CLEARED" };

/** Key in chrome.storage.session where the background keeps the current job. */
export const CURRENT_JOB_KEY = "currentJob";
