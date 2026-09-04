/**
 * Shared TypeScript interfaces — mirrors Pydantic response schemas exactly.
 *
 * IMPORTANT: When a Pydantic schema field changes in the backend, update
 * the corresponding interface here in the same commit.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  user: UserResponse;
}

// ── Profile ───────────────────────────────────────────────────────────────────

export type ExperienceLevel = "fresher" | "junior" | "mid" | "senior";

export interface EducationEntry {
  degree: string;
  institution: string;
  year: string | null;
  field_of_study: string | null;
}

export interface ExperienceEntry {
  title: string;
  company: string;
  duration: string | null;
  description: string | null;
}

export interface ProjectEntry {
  name: string;
  description: string | null;
  technologies: string[];
  url: string | null;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  job_role: string | null;
  experience_level: ExperienceLevel | null;
  skills: string[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
  projects: ProjectEntry[];
  resume_filename: string | null;
  resume_parsed: boolean;
  updated_at: string;
}

// ── Session ───────────────────────────────────────────────────────────────────

export type SessionStatus = "active" | "processing" | "complete" | "failed";
export type InterviewType = "technical" | "hr" | "behavioral" | "mixed";

export interface InterviewSession {
  id: string;
  interview_type: InterviewType;
  job_role: string;
  status: SessionStatus;
  total_score: number | null;
  question_count: number;
  current_question_index: number;
  started_at: string;
  completed_at: string | null;
}

// ── Question ──────────────────────────────────────────────────────────────────

export interface Question {
  id: string;
  session_id: string;
  sequence_number: number;
  question_text: string;
  question_type: string;
  difficulty: "easy" | "medium" | "hard";
}

// ── Answer ────────────────────────────────────────────────────────────────────

export interface AnswerResponse {
  quick_score: number;
  next_question: Question | null;
}

// ── Report ────────────────────────────────────────────────────────────────────

export interface QuestionReview {
  question_text: string;
  answer_text: string;
  total_score: number;
  model_answer: string;
  feedback_text: string;
  improvement_tip: string;
}

export interface PerformanceReport {
  session_id: string;
  overall_score: number;
  radar_data: {
    accuracy: number;
    relevance: number;
    clarity: number;
    completeness: number;
  };
  question_review: QuestionReview[];
  strengths: string[];
  weaknesses: string[];
  improvement_areas: string[];
  executive_summary: string;
}
