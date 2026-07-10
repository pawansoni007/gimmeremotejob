// DOM test for the content-script extraction, run against a saved copy of a
// real Wellfound job modal (test/fixtures/job-modal.html) in headless Chromium.
//
// Run with: npm run test:dom
// Uses your installed Chrome by default; set CHROMIUM_PATH to point at a
// specific binary instead.
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "fixtures/job-modal.html"), "utf-8");

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH
    ? { executablePath: process.env.CHROMIUM_PATH }
    : { channel: "chrome" },
);

try {
  const page = await browser.newPage();
  await page.setContent(html);
  await page.addScriptTag({ path: join(here, "../dist-test/extract.iife.js") });

  const job = await page.evaluate(() => {
    const modal = document.querySelector(
      '[data-test="DiscoverModal"], [data-test="JobListingSlideIn"]',
    );
    return window.WF.extractJob(modal);
  });

  assert.equal(job.jobId, "4230970");
  assert.equal(job.jobUrl, "https://wellfound.com/jobs/4230970-ai-native-fullstack-sde");
  assert.equal(job.title, "AI-Native Fullstack SDE");
  assert.equal(job.company.name, "Bullwhip");
  assert.equal(job.company.slug, "bullwhip-tech");
  assert.match(job.company.tagline, /yield optimization/);
  assert.deepEqual(job.metaItems, [
    "₹15L – ₹22.5L",
    "Remote (India)",
    "2 years of exp",
    "Full Time",
  ]);
  assert.equal(job.compensation, "₹15L – ₹22.5L");
  assert.equal(job.location, "Remote (India)");
  assert.equal(job.experience, "2 years of exp");
  assert.equal(job.jobType, "Full Time");
  assert.equal(job.postedInfo, "Reposted: 1 month ago • Recruiter recently active");
  assert.deepEqual(job.fields, {
    "Hires remotely in": "India",
    "Remote Work Policy": "Remote only",
    "Company Location": "India • New York City",
    "Visa Sponsorship": "Not Available",
    "Preferred Timezones": "Coordinated Universal Time",
    "Collaboration Hours": "09:30 - 18:30 Coordinated Universal Time",
    Relocation: "Not Allowed",
  });
  assert.deepEqual(job.skills, [
    "Python",
    "Node.js",
    "PostgreSQL",
    "TypeScript",
    "Google Cloud Platform (GCP)",
    "Claude Code",
  ]);
  assert.match(job.description, /^TL;DR\nWe're looking for an AI-Native Fullstack/);
  assert.ok(job.description.length > 5000, "description looks truncated");
  assert.deepEqual(job.emails, ["talent@bullwhip.io"]);

  // --- Step 3: the Apply form's questions ---
  assert.equal(job.hasApplyForm, true);
  assert.deepEqual(job.questions, [
    {
      id: "263701",
      question: "What interests you about working for this company?",
      kind: "textarea",
      fieldName: "customQuestionAnswers[263701][answer]",
      currentValue: "",
    },
  ]);

  // Text the user already typed must come back in currentValue.
  const typed = await page.evaluate(() => {
    document.querySelector('[name^="customQuestionAnswers"]').value = "I love analytics.";
    const modal = document.querySelector('[data-test="DiscoverModal"]');
    return window.WF.extractJob(modal).questions[0].currentValue;
  });
  assert.equal(typed, "I love analytics.");

  // With the form gone (external-application jobs), we must say so.
  const noForm = await page.evaluate(() => {
    document.querySelector("form").remove();
    const modal = document.querySelector('[data-test="DiscoverModal"]');
    const job = window.WF.extractJob(modal);
    return { hasApplyForm: job.hasApplyForm, questions: job.questions };
  });
  assert.equal(noForm.hasApplyForm, false);
  assert.deepEqual(noForm.questions, []);

  console.log("extract.dom.test: all assertions passed");
} finally {
  await browser.close();
}
