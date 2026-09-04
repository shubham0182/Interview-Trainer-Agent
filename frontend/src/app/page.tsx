/**
 * Landing page — public, no auth required.
 * Full implementation in ST-16/ST-17.
 */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900">
        InterviewPro AI
      </h1>
      <p className="mt-4 text-lg text-gray-600 text-center max-w-xl">
        AI-powered interview preparation powered by IBM Granite.
        <br />
        Practice mock interviews and get detailed performance feedback.
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/auth/login"
          className="rounded-md bg-blue-600 px-6 py-3 text-white font-medium hover:bg-blue-700"
        >
          Sign In
        </a>
        <a
          href="/auth/register"
          className="rounded-md border border-gray-300 px-6 py-3 text-gray-700 font-medium hover:bg-gray-50"
        >
          Get Started
        </a>
      </div>
    </main>
  );
}
