import { useState } from "react";
import type { JobInfo } from "../shared/types";

// Fields worth surfacing even when the description is the star. Shown in the
// order Wellfound renders them (we keep insertion order of the extracted map).
export function JobCard({ job }: { job: JobInfo }) {
  const [expanded, setExpanded] = useState(false);

  const meta = [job.compensation, job.location, job.experience, job.jobType].filter(
    (v): v is string => Boolean(v),
  );
  const fieldEntries = Object.entries(job.fields);

  return (
    <article className="job-card">
      <header className="job-header">
        <h2 className="job-title">{job.title}</h2>
        <div className="job-company">
          {job.company.url ? (
            <a href={job.company.url} target="_blank" rel="noreferrer">
              {job.company.name}
            </a>
          ) : (
            job.company.name
          )}
          {job.company.tagline && <span className="job-tagline">{job.company.tagline}</span>}
        </div>
        {meta.length > 0 && (
          <ul className="job-meta">
            {meta.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
        {job.postedInfo && <div className="job-posted">{job.postedInfo}</div>}
      </header>

      {fieldEntries.length > 0 && (
        <dl className="job-fields">
          {fieldEntries.map(([label, value]) => (
            <div className="job-field" key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}

      {job.skills.length > 0 && (
        <section className="job-section">
          <h3>Skills</h3>
          <ul className="job-skills">
            {job.skills.map((skill) => (
              <li key={skill}>{skill}</li>
            ))}
          </ul>
        </section>
      )}

      {job.description && (
        <section className="job-section">
          <h3>About the job</h3>
          <p className={expanded ? "job-desc" : "job-desc collapsed"}>{job.description}</p>
          <button className="link-button" onClick={() => setExpanded(!expanded)}>
            {expanded ? "Show less" : "Show more"}
          </button>
        </section>
      )}

      <footer className="job-footer">
        {job.jobUrl && (
          <a href={job.jobUrl} target="_blank" rel="noreferrer">
            {job.jobId ? `wellfound.com · job ${job.jobId}` : "View on Wellfound"}
          </a>
        )}
      </footer>
    </article>
  );
}
