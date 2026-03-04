import type {
  DownloadFormat,
  TailorRequest,
  TailorResponse,
  UploadResponse,
} from './types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Upload resume file + job description
// ---------------------------------------------------------------------------
export async function uploadResume(
  file: File,
  jobDescription: string,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('job_description', jobDescription);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Upload failed');
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Run the tailoring pipeline
// ---------------------------------------------------------------------------
export async function tailorResume(
  request: TailorRequest,
): Promise<TailorResponse> {
  const res = await fetch(`${API_BASE}/api/tailor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Tailoring failed');
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Download tailored resume file
// ---------------------------------------------------------------------------
export async function downloadFile(
  sessionId: string,
  format: DownloadFormat,
): Promise<Blob> {
  const res = await fetch(
    `${API_BASE}/api/download/${sessionId}/${format}`,
  );

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Download failed');
  }

  return res.blob();
}

// ---------------------------------------------------------------------------
// Trigger browser file download from a Blob
// ---------------------------------------------------------------------------
export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Delay revocation so the browser can initiate the download
  setTimeout(() => URL.revokeObjectURL(url), 100);
}
