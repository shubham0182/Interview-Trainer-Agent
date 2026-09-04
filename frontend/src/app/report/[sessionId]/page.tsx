/**
 * Performance report — radar chart + question review + improvement tips.
 * Full implementation in ST-18.
 */
export default function ReportPage({
  params,
}: {
  params: { sessionId: string };
}) {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold text-gray-900">Performance Report</h1>
      <p className="mt-2 text-sm text-gray-500">
        Session: {params.sessionId} — Full implementation in ST-18
      </p>
    </main>
  );
}
