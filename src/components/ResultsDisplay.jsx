export default function ResultsDisplay({ results }) {
  const {
    transcript,
    abusive_table,
    violent_table,
    nsfw_audio_table,
    political_table,
    religious_table,
    video_nsfw_info,
    video_violence_info,
  } = results;

  return (
    <div className="space-y-6">
      {/* Transcript */}
      <ResultSection title="Transcript (Urdu)" content={transcript} type="text" />

      {/* Tables */}
      {abusive_table[0][1] !== "Not analyzed" && (
        <ResultSection title="Abusive Content Analysis" content={abusive_table} type="table" />
      )}
      {violent_table[0][1] !== "Not analyzed" && (
        <ResultSection title="Violent Content Analysis" content={violent_table} type="table" />
      )}
      {nsfw_audio_table[0][1] !== "Not analyzed" && (
        <ResultSection title="NSFW Content Analysis" content={nsfw_audio_table} type="table" />
      )}
      {political_table[0][1] !== "Not analyzed" && (
        <ResultSection title="Political Content Analysis" content={political_table} type="table" />
      )}
      {religious_table[0][1] !== "Not analyzed" && (
        <ResultSection title="Religious Content Analysis" content={religious_table} type="table" />
      )}

      {/* Video Analysis Results */}
      {video_nsfw_info && (
        <ResultSection title="Video NSFW Detection" content={video_nsfw_info} type="text" />
      )}
      {video_violence_info && (
        <ResultSection title="Video Violence Detection" content={video_violence_info} type="text" />
      )}
    </div>
  );
}

function ResultSection({ title, content, type }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      {type === "text" ? (
        <p className="text-gray-700 whitespace-pre-wrap">{content}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Field
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {content.map((row, i) => (
                <tr key={i}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {row[0]}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 whitespace-pre-wrap">
                    {row[1]}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}