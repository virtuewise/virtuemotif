/**
 * Minimal typing for environment variables referenced by the optional
 * server-side Whisper API integration. The runtime guard in WhisperEngine
 * ensures browser builds do not access this global when it is unavailable.
 */
declare const process:
  | {
      env?: Record<string, string | undefined>;
    }
  | undefined;
