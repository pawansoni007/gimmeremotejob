import type { JobInfo } from "../shared/types";
import { SELECTORS, jobIdFromHref } from "./selectors";

// Reads a JobInfo out of the open slide-in modal. Pure DOM -> data; no side
// effects, so it's safe to call repeatedly while the modal is still loading.

function clean(text: string | null | undefined): string {
  return (text ?? "").replace(/ /g, " ").replace(/\s+/g, " ").trim();
}

/** Like clean(), but keeps paragraph breaks — used for the job description. */
function cleanBlock(text: string | null | undefined): string {
  return (text ?? "")
    .replace(/ /g, " ")
    .replace(/[ \t]+/g, " ")
    .replace(/\s*\n\s*/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** The meta row is the <ul> right after the <h1>; items are separated by "|". */
function readMetaItems(title: Element | null): string[] {
  const list = title?.nextElementSibling;
  if (!list || list.tagName !== "UL") return [];
  return Array.from(list.querySelectorAll("li"))
    .map((li) => clean(li.textContent).replace(/^\|\s*/, ""))
    .filter(Boolean);
}

/** Best-effort classification of the meta row items. */
function classifyMeta(items: string[]): {
  compensation: string | null;
  location: string | null;
  experience: string | null;
  jobType: string | null;
} {
  let compensation: string | null = null;
  let location: string | null = null;
  let experience: string | null = null;
  let jobType: string | null = null;

  for (const item of items) {
    if (!compensation && /[₹$€£]|\d\s*[kKL]\b/.test(item)) compensation = item;
    else if (!experience && /\bexp\b|experience/i.test(item)) experience = item;
    else if (!jobType && /full[- ]?time|part[- ]?time|contract|intern/i.test(item))
      jobType = item;
    else if (!location && /remote|on[- ]?site|hybrid|\(/i.test(item)) location = item;
  }
  // Whatever wasn't matched but mentions a place still beats nothing.
  if (!location) location = items.find((i) => /remote/i.test(i)) ?? null;
  return { compensation, location, experience, jobType };
}

/** First /company/ link that has visible text (the avatar link has none). */
function readCompany(modal: HTMLElement): JobInfo["company"] {
  const links = Array.from(
    modal.querySelectorAll<HTMLAnchorElement>(SELECTORS.companyLink),
  );
  const nameLink =
    links.find((a) => clean(a.textContent) && !/learn more|see all/i.test(a.textContent ?? "")) ??
    null;

  const href = (nameLink ?? links[0])?.getAttribute("href") ?? null;
  const slug = href?.match(/\/company\/([^/?#]+)/)?.[1] ?? null;

  // The tagline sits right under the row that holds the company-name link.
  const nameRow = nameLink?.closest("div");
  const taglineEl = nameRow?.nextElementSibling;
  const tagline =
    taglineEl && !taglineEl.querySelector("ul") ? clean(taglineEl.textContent) || null : null;

  return {
    name: clean(nameLink?.textContent) || "Unknown company",
    slug,
    url: slug ? `https://wellfound.com/company/${slug}` : null,
    tagline,
  };
}

/**
 * The labelled grid: <div><span class="… font-semibold">Label</span><value/></div>.
 * We take every font-semibold span that starts a plain <div>, and read its
 * following siblings as the value. "Skills" is chips, so it's split out.
 */
function readFields(modal: HTMLElement): { fields: Record<string, string>; skills: string[] } {
  const fields: Record<string, string> = {};
  let skills: string[] = [];

  for (const span of Array.from(modal.querySelectorAll<HTMLSpanElement>(SELECTORS.fieldLabel))) {
    const parent = span.parentElement;
    if (!parent || parent.tagName !== "DIV") continue;
    if (parent.firstElementChild !== span || !span.nextElementSibling) continue;

    const label = clean(span.textContent);
    if (!label) continue;

    if (/^skills$/i.test(label)) {
      skills = Array.from(span.nextElementSibling.children)
        .map((chip) => clean(chip.textContent))
        .filter(Boolean);
      continue;
    }

    let value = "";
    for (let el: Element | null = span.nextElementSibling; el; el = el.nextElementSibling) {
      value += " " + (el.textContent ?? "");
    }
    value = clean(value);
    if (value) fields[label] = value;
  }

  return { fields, skills };
}

/**
 * The current job's id. The page URL is the primary source (Wellfound pushes
 * /jobs/<id>-<slug> when a job opens); the modal's own job links are fallbacks —
 * we prefer the one whose text matches the modal title, since "Recent Jobs" can
 * list the company's other roles.
 */
function readJobId(modal: HTMLElement, title: string): { jobId: string | null; jobUrl: string | null } {
  const fromPath = jobIdFromHref(location.pathname);
  if (fromPath) {
    return { jobId: fromPath, jobUrl: `https://wellfound.com${location.pathname}` };
  }

  const links = Array.from(modal.querySelectorAll<HTMLAnchorElement>(SELECTORS.jobLink));
  const match =
    links.find((a) => title && clean(a.textContent) === title) ?? links[0] ?? null;
  const href = match?.getAttribute("href") ?? null;
  return {
    jobId: href ? jobIdFromHref(href) : null,
    jobUrl: href ? new URL(href, "https://wellfound.com").toString() : null,
  };
}

export function extractJob(modal: HTMLElement): JobInfo {
  const titleEl = modal.querySelector(SELECTORS.title);
  const title = clean(titleEl?.textContent);

  const metaItems = readMetaItems(titleEl);
  const { compensation, location: loc, experience, jobType } = classifyMeta(metaItems);

  // "Reposted: 1 month ago • Recruiter recently active" — the div after the meta
  // row. The separator's spacing is CSS margin, so re-space it in the text.
  const postedEl = titleEl?.nextElementSibling?.nextElementSibling;
  const postedInfo = clean(postedEl?.textContent).replace(/\s*•\s*/g, " • ") || null;

  const descriptionEl = modal.querySelector<HTMLElement>(SELECTORS.description);
  const description = descriptionEl
    ? cleanBlock(descriptionEl.innerText ?? descriptionEl.textContent)
    : "";

  const emails = Array.from(
    new Set(
      Array.from(descriptionEl?.querySelectorAll<HTMLAnchorElement>(SELECTORS.mailto) ?? [])
        .map((a) => a.getAttribute("href")?.replace(/^mailto:/, "").split("?")[0] ?? "")
        .filter(Boolean),
    ),
  );

  const { fields, skills } = readFields(modal);
  const { jobId, jobUrl } = readJobId(modal, title);

  return {
    jobId,
    jobUrl,
    title,
    company: readCompany(modal),
    metaItems,
    compensation,
    location: loc,
    experience,
    jobType,
    postedInfo,
    fields,
    skills,
    description,
    emails,
    capturedAt: Date.now(),
  };
}
