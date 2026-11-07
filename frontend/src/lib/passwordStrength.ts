import { ZxcvbnFactory } from "@zxcvbn-ts/core";
import * as common from "@zxcvbn-ts/language-common";
import * as english from "@zxcvbn-ts/language-en";
// Public policy constants only; this JSON contains no backend configuration.
import policy from "../../../backend/app/data/password_policy.json";

const estimator = new ZxcvbnFactory({
  translations: english.translations,
  graphs: common.adjacencyGraphs,
  dictionary: { ...common.dictionary, ...english.dictionary },
  maxLength: policy.maximum_utf8_bytes,
});

export type PasswordAssessment = {
  score: number;
  label: string;
  accepted: boolean;
  hint: string;
  length: number;
};

export function assessPassword(password: string, email = ""): PasswordAssessment {
  const length = Array.from(password).length;
  const base = { score: 0, accepted: false, length };
  if (!password) return { ...base, label: "Not entered", hint: "Use at least 15 characters. Try several unrelated words." };
  if (Array.from(password).some(character => {
    const point = character.codePointAt(0)!;
    return point >= 0xd800 && point <= 0xdfff;
  })) return { ...base, label: "Invalid characters", hint: "Use valid Unicode characters in your password." };
  // Reject oversized values before asking the estimator to examine them.
  if (new TextEncoder().encode(password).length > policy.maximum_utf8_bytes)
    return { ...base, label: "Too long", hint: "Use up to 72 UTF-8 bytes. Unicode characters can use more than one byte." };
  if (policy.blocked_passwords.includes(password.toLowerCase().trim()))
    return { ...base, label: "Too predictable", hint: "This is a commonly guessed or well-known password. Choose your own unrelated words or use a password manager." };
  const local = email.toLowerCase().split("@")[0];
  const context = [...policy.context_words, email.toLowerCase(), local,
    ...local.split(/[^a-z0-9]+/).filter(word => word.length >= 3)].filter(Boolean);
  const result = estimator.check(password, context);
  const accepted = length >= policy.minimum_length && result.score >= policy.minimum_score;
  const labels = ["Very weak", "Weak", "Fair", "Strong", "Very strong"];
  return {
    score: length < policy.minimum_length ? Math.min(result.score, 1) : result.score,
    label: length < policy.minimum_length ? "Too short" : labels[result.score],
    accepted,
    length,
    hint: length < policy.minimum_length
      ? `Use at least ${policy.minimum_length} characters; you have ${length}.`
      : accepted ? "Good length and low predictability. Use this password only for JOMO."
      : result.feedback.warning || "Try several unrelated words. Avoid repeated patterns, your email, or the app name.",
  };
}
