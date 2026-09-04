"use client";
/**
 * Live interview session — Q&A loop with polling + quick score display.
 * Full implementation in ST-17.
 */
export default function InterviewSessionPage({
  params,
}: {
  params: { sessionId: string };
}) {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold text-gray-900">Interview Session</h1>
      <p className="mt-2 text-sm text-gray-500">
        Session: {params.sessionId} — Full implementation in ST-17
      </p>
    </main>
  );
}
