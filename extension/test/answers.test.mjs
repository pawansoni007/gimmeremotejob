// Unit test for the pure streaming logic (no browser needed — Node strips the
// types natively). Run with: npm run test:unit
import { strict as assert } from "node:assert";
import { SseDecoder, splitAnswers } from "../src/shared/answers.ts";

// --- SseDecoder: reassembles events across arbitrary chunk boundaries ---
// \r\n separators throughout: that's what sse-starlette actually sends.
{
  const decoder = new SseDecoder();
  const wire =
    ': ping\r\n\r\n' +
    'data: {"type":"text_delta","text":"### Answer 1\\nBecause"}\r\n\r\n' +
    'data: {"type":"text_delta","text":" it fits."}\r\n\r\n' +
    'data: not-json\r\n\r\n' +
    'data: {"type":"turn_complete","text":"### Answer 1\\nBecause it fits.","usage":{"input_tokens":1,"output_tokens":2}}\r\n\r\n' +
    'data: {"type":"done"}\r\n\r\n';

  // Feed it in awkward 7-byte chunks to prove buffering works — including
  // \r\n pairs landing split across two chunks.
  const events = [];
  for (let i = 0; i < wire.length; i += 7) {
    events.push(...decoder.push(wire.slice(i, i + 7)));
  }

  assert.deepEqual(
    events.map((e) => e.type),
    ["text_delta", "text_delta", "turn_complete", "done"],
  );
  assert.equal(events[0].text + events[1].text, "### Answer 1\nBecause it fits.");
  assert.deepEqual(events[2].usage, { input_tokens: 1, output_tokens: 2 });

  // Plain \n endings still work too.
  const lfDecoder = new SseDecoder();
  const lfEvents = lfDecoder.push('data: {"type":"done"}\n\n');
  assert.deepEqual(lfEvents, [{ type: "done" }]);
}

// --- splitAnswers: the ### Answer <n> contract ---
{
  const text =
    "### Answer 1\nFirst answer, two sentences.\nStill the first.\n\n" +
    "### answer 2\nSecond answer.\n\n" +
    "### Answer 3\nThird.";
  assert.deepEqual(splitAnswers(text, 3), [
    "First answer, two sentences.\nStill the first.",
    "Second answer.",
    "Third.",
  ]);

  // Missing section stays empty; out-of-range heading is ignored.
  assert.deepEqual(splitAnswers("### Answer 2\nOnly the second.", 2), [
    "",
    "Only the second.",
  ]);
  assert.deepEqual(splitAnswers("### Answer 9\nnope", 2), ["", ""]);

  // No headings at all -> whole text becomes answer 1 (model drift, single question).
  assert.deepEqual(splitAnswers("  Just prose, no headings.  ", 1), [
    "Just prose, no headings.",
  ]);

  // Zero questions -> nothing to fill.
  assert.deepEqual(splitAnswers("### Answer 1\nhello", 0), []);
}

console.log("answers.test: all assertions passed");
