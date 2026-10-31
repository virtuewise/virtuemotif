// src/api/whisper.ts
// Cloud fallback endpoint client for Whisper speech-to-text transcription.
// Can be activated via USE_CLOUD environment toggle or explicit configuration.

export interface WhisperResponse {
  text: string;
  segments?: Array<{ start: number; end: number; text: string }>;
}

/**
 * Transcribes audio via a cloud or serverless endpoint.
 */
export async function transcribeCloudAudio(
  audioBlob: Blob,
  endpointUrl: string = '/api/whisper'
): Promise<WhisperResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');

  const res = await fetch(endpointUrl, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Whisper cloud request failed with status ${res.status}: ${res.statusText}`);
  }

  return (await res.json()) as WhisperResponse;
}
