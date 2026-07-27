export const PASSWORD_HINT = "At least 12 characters with uppercase, lowercase, number, and special character.";

export function passwordPolicyError(password: string): string | null {
  const valid = password.length >= 12
    && /[A-Z]/.test(password)
    && /[a-z]/.test(password)
    && /\d/.test(password)
    && /[^A-Za-z0-9\s]/.test(password);
  return valid ? null : PASSWORD_HINT;
}
