"use client";
/**
 * Dashboard page — session history and start new interview.
 * Navigation shell is complete here; interview functionality in ST-17.
 */
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/auth/login");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-sm">Loading…</div>
      </div>
    );
  }

  if (!user) return null;

  async function handleLogout() {
    await logout();
    router.replace("/auth/login");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Nav */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <span className="font-bold text-blue-400 text-lg tracking-tight">
            InterviewPro AI
          </span>
          <nav className="hidden sm:flex items-center gap-6 text-sm text-slate-400">
            <Link href="/dashboard" className="text-white font-medium">
              Dashboard
            </Link>
            <Link href="/profile" className="hover:text-white">
              Profile
            </Link>
            <Link href="/interview/setup" className="hover:text-white">
              Practice
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400 hidden sm:block">
              {user.full_name ?? user.email}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-slate-400 hover:text-white border border-slate-700 rounded-lg px-3 py-1.5 transition"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold">
            Welcome back{user.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}!
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Ready to practise your next interview?
          </p>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <Link
            href="/interview/setup"
            className="group bg-blue-600 hover:bg-blue-500 transition rounded-xl p-6 flex flex-col gap-3"
          >
            <div className="text-2xl">🎯</div>
            <div>
              <div className="font-semibold text-lg">Start Interview</div>
              <div className="text-blue-200 text-sm">
                Pick a role and begin a mock session
              </div>
            </div>
          </Link>

          <Link
            href="/profile"
            className="group bg-slate-800 hover:bg-slate-700 transition rounded-xl p-6 flex flex-col gap-3 border border-slate-700"
          >
            <div className="text-2xl">👤</div>
            <div>
              <div className="font-semibold text-lg">Edit Profile</div>
              <div className="text-slate-400 text-sm">
                Update skills, experience and resume
              </div>
            </div>
          </Link>

          <div className="bg-slate-800/50 rounded-xl p-6 flex flex-col gap-3 border border-slate-700/50 opacity-60">
            <div className="text-2xl">📊</div>
            <div>
              <div className="font-semibold text-lg">Past Sessions</div>
              <div className="text-slate-500 text-sm">Available after first interview</div>
            </div>
          </div>
        </div>

        {/* Empty state for sessions */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
          <div className="text-4xl mb-3">🚀</div>
          <h2 className="text-lg font-semibold mb-1">No sessions yet</h2>
          <p className="text-slate-400 text-sm mb-5">
            Complete your profile, then start your first mock interview.
          </p>
          <Link
            href="/interview/setup"
            className="inline-block bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-2.5 rounded-lg transition text-sm"
          >
            Start practising
          </Link>
        </div>
      </main>
    </div>
  );
}
