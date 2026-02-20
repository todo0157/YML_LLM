/**
 * TypeScript 타입 정의
 */

export interface Env {
  GOOGLE_API_KEY: string;
  TAVILY_API_KEY: string;
}

export interface SearchResult {
  source: 'web' | 'kb' | 'paper' | 'community';
  url: string;
  title: string;
  content: string;
  relevanceScore: number;
}

export interface ResearchPlan {
  mainQuery: string;
  subQueries: string[];
  searchStrategies: ('web' | 'kb' | 'paper' | 'community')[];
  materialType: string | null;
  defectType: string | null;
  parametersMentioned: string[];
}

export interface ParameterRecommendation {
  parameter: string;
  currentValue: string | null;
  recommendedValue: string;
  confidence: number;
  sources: string[];
  reasoning: string;
}

export interface AgentState {
  originalQuery: string;
  researchPlan: ResearchPlan | null;
  webResults: SearchResult[];
  kbResults: SearchResult[];
  paperResults: SearchResult[];
  iterationCount: number;
  isSufficient: boolean;
  confidenceScore: number;
  missingInfo: string[];
  synthesizedKnowledge: string;
  recommendations: ParameterRecommendation[];
  finalResponse: string;
  sourcesCited: string[];
  errors: string[];
}

export interface ResearchRequest {
  query: string;
  material?: string;
  currentParams?: Record<string, number | string>;
}

export interface ResearchResponse {
  response: string;
  sources: string[];
  success: boolean;
  error?: string;
}

export interface MaterialGuide {
  name: string;
  nozzleTemp: { min: number; max: number; optimal: number };
  bedTemp: { min: number; max: number; optimal: number };
  printSpeed: { min: number; max: number; optimal: number };
  retraction: { distance: number; speed: number };
  fanSpeed: number;
  tips: string[];
}

export interface DefectGuide {
  name: string;
  description: string;
  causes: string[];
  solutions: { action: string; priority: number }[];
}
