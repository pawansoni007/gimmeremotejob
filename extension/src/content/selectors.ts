// Stable anchors for reading the Wellfound job slide-in modal.
//
// We deliberately AVOID the hashed `styles_*` class names — they are per-build
// CSS-module hashes and change without notice. Everything below is a `data-test`,
// `id`, `name`, `href`, or semantic tag/utility class, which are far more stable.
// Keeping all selectors here means a Wellfound layout change is a one-file fix.
export const SELECTORS = {
  // The modal that opens when you click a job.
  modal: '[data-test="DiscoverModal"], [data-test="JobListingSlideIn"]',

  // Job identity.
  jobLink: 'a[href^="/jobs/"]', // href like /jobs/4230970-ai-native-fullstack-sde
  companyLink: 'a[href^="/company/"]', // href like /company/bullwhip-tech
  title: "h1",
  description: "#job-description",
  mailto: 'a[href^="mailto:"]', // emails in the JD -> future email feature

  // The labelled grid under the header ("Remote Work Policy", "Skills", ...).
  // Each label is a <span class="… font-semibold"> that is the first child of a
  // plain <div>, with the value in its following sibling(s).
  fieldLabel: "span.font-semibold",

  // The Apply form.
  questionFields: '[name^="customQuestionAnswers"]', // textarea/input per question
  submit: '[data-test="JobDescriptionSlideIn--SubmitButton"]',
} as const;

// Pull the numeric Wellfound job id out of a /jobs/<id>-<slug> href or path.
export function jobIdFromHref(href: string): string | null {
  const m = href.match(/\/jobs\/(\d+)/);
  return m ? m[1] : null;
}
