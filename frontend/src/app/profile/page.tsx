"use client";
/**
 * Candidate Profile page — full profile form including all required fields.
 */
import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api-client";
import type { CandidateProfile, ExperienceLevel } from "@/lib/types";

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "fresher", label: "Fresher (0 years)" },
  { value: "junior", label: "Junior (1–2 years)" },
  { value: "mid", label: "Mid-level (3–5 years)" },
  { value: "senior", label: "Senior (5+ years)" },
];

export default function ProfilePage() {
  const { user, token, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [jobRole, setJobRole] = useState("");
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel | "">("");
  const [skillsText, setSkillsText] = useState(""); // comma-separated input

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!token) return;
    api
      .authGet<CandidateProfile>("/api/v1/profiles/me", token)
      .then((p) => {
        setProfile(p);
        setJobRole(p.job_role ?? "");
        setExperienceLevel(p.experience_level ?? "");
        setSkillsText((p.skills ?? []).join(", "));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [token]);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    setSaved(false);

    const skills = skillsText
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const updated = await api.authPut<CandidateProfile>(
        "/api/v1/profiles/me",
        token,
        {
          job_role: jobRole || null,
          experience_level: experienceLevel || null,
          skills,
        }
      );
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    await logout();
    router.replace("/auth/login");
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-sm">Loading…</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Nav */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-3 flex items-center justify-between">
          <span className="font-bold text-blue-400 text-lg tracking-tight">
            InterviewPro AI
          </span>
          <nav className="hidden sm:flex items-center gap-6 text-sm text-slate-400">
            <Link href="/dashboard" className="hover:text-white">Dashboard</Link>
            <Link href="/profile" className="text-white font-medium">Profile</Link>
            <Link href="/interview/setup" className="hover:text-white">Practice</Link>
          </nav>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-400 hover:text-white border border-slate-700 rounded-lg px-3 py-1.5 transition"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Candidate Profile</h1>
          <p className="text-slate-400 text-sm mt-1">
            Your profile is used to personalise interview questions.
          </p>
        </div>

        {/* Account info (read-only) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Account
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-slate-500">Name</div>
              <div className="text-white mt-0.5">{user.full_name ?? "—"}</div>
            </div>
            <div>
              <div className="text-slate-500">Email</div>
              <div className="text-white mt-0.5">{user.email}</div>
            </div>
          </div>
        </div>

        {/* Profile form */}
        <form
          onSubmit={handleSave}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6"
        >
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Interview Preferences
          </h2>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}
          {saved && (
            <div className="rounded-lg bg-green-500/10 border border-green-500/30 px-4 py-3 text-sm text-green-400">
              Profile saved successfully!
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Target Job Role
              </label>
              <input
                type="text"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="e.g. Software Engineer"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Experience Level
              </label>
              <select
                value={experienceLevel}
                onChange={(e) =>
                  setExperienceLevel(e.target.value as ExperienceLevel | "")
                }
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
              >
                <option value="">Select level</option>
                {EXPERIENCE_LEVELS.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Technical Skills
              <span className="text-slate-500 font-normal ml-2">
                (comma-separated)
              </span>
            </label>
            <input
              type="text"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              placeholder="Python, FastAPI, PostgreSQL, React"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
            />
            {skillsText && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {skillsText
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .map((skill) => (
                    <span
                      key={skill}
                      className="bg-blue-600/20 text-blue-300 border border-blue-600/30 px-2 py-0.5 rounded-full text-xs"
                    >
                      {skill}
                    </span>
                  ))}
              </div>
            )}
          </div>

          {/* Resume status */}
          {profile && (
            <div className="bg-slate-800/50 rounded-lg p-4 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-slate-300">
                  Resume Upload
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {profile.resume_filename
                    ? `Uploaded: ${profile.resume_filename}`
                    : "No resume uploaded yet"}
                  {profile.resume_parsed && (
                    <span className="text-green-400 ml-2">✓ Parsed</span>
                  )}
                </div>
              </div>
              <span className="text-xs text-slate-500 bg-slate-700 rounded px-2 py-1">
                Available in next update
              </span>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold px-6 py-2.5 rounded-lg transition text-sm"
            >
              {saving ? "Saving…" : "Save Profile"}
            </button>
          </div>
        </form>

        {/* Education / Experience / Projects — placeholder for ST-16 */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {["Education", "Work Experience", "Projects"].map((section) => (
            <div
              key={section}
              className="bg-slate-900/50 border border-slate-800 border-dashed rounded-xl p-5 text-center"
            >
              <div className="text-slate-500 text-sm">{section}</div>
              <div className="text-slate-600 text-xs mt-1">
                Full editor coming soon
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
