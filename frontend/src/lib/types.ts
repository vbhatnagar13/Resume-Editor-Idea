// TypeScript types matching backend Pydantic schemas

export interface UploadResponse {
  session_id: string;
  filename: string;
  message: string;
}

export interface TailorSettings {
  aggressiveness: 'conservative' | 'balanced' | 'aggressive';
  keyword_emphasis: boolean;
  no_reordering: boolean;
}

export interface TailorRequest extends TailorSettings {
  session_id: string;
  job_description: string;
}

export interface DiffChange {
  section: string;
  entry_id: string | null;
  bullet_id: string | null;
  change_type: 'rewrite' | 'reorder' | 'keyword_add';
  original: string;
  revised: string;
  reason: string;
}

export interface DiffReport {
  changes: DiffChange[];
  keywords_added: string[];
  keywords_preserved: string[];
  sections_reordered: string[];
  fabrication_check: string;
  ats_check: string;
}

export interface TailorResponse {
  session_id: string;
  diff_report: DiffReport;
  preview_html: string;
}

export type DownloadFormat = 'docx' | 'pdf';
