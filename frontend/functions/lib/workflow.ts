/**
 * Research Agent 워크플로우 (최적화 버전)
 * LLM 호출 3회 → 1회로 최적화
 */

import type {
  Env,
  AgentState,
  ResearchPlan,
  SearchResult,
  ParameterRecommendation,
} from './types';
import { callGemini, parseJsonResponse } from './gemini';
import { search3DPrintingWeb } from './tavily';
import { searchKnowledgeBase } from './knowledge-base';
import { FINAL_RESPONSE_TEMPLATE } from './prompts';

/**
 * 로컬 키워드 매칭으로 쿼리 분석 (LLM 호출 없음)
 */
function parseQueryLocal(query: string): ResearchPlan {
  const queryLower = query.toLowerCase();

  // 재료 타입 감지
  const materialPatterns: Record<string, string[]> = {
    'PLA': ['pla', '플라', 'polylactic'],
    'ABS': ['abs'],
    'PETG': ['petg', 'pet-g'],
    'TPU': ['tpu', '플렉시블', '유연'],
    'ASA': ['asa'],
    'NYLON': ['nylon', '나일론'],
  };

  let materialType: string | null = null;
  for (const [material, patterns] of Object.entries(materialPatterns)) {
    if (patterns.some(p => queryLower.includes(p))) {
      materialType = material;
      break;
    }
  }

  // 결함 타입 감지
  const defectPatterns: Record<string, string[]> = {
    'stringing': ['stringing', '스트링', '실', '거미줄', '늘어짐'],
    'warping': ['warping', '휨', '워핑', '뒤틀림', '변형'],
    'layer_adhesion': ['층간', '분리', 'adhesion', '접착', '탈락'],
    'under_extrusion': ['under', '언더', '압출 부족', '얇'],
    'over_extrusion': ['over', '오버', '압출 과다', '뭉침'],
    'clogging': ['막힘', 'clog', '노즐 막힘'],
    'elephant_foot': ['elephant', '코끼리 발', '첫층 넓음'],
    'z_banding': ['z밴딩', 'banding', '층 무늬'],
    'bridging': ['bridge', '브릿지', '브릿징'],
  };

  let defectType: string | null = null;
  for (const [defect, patterns] of Object.entries(defectPatterns)) {
    if (patterns.some(p => queryLower.includes(p))) {
      defectType = defect;
      break;
    }
  }

  // 파라미터 감지
  const parameterPatterns: Record<string, string[]> = {
    'nozzle_temp': ['노즐 온도', '노즐온도', 'nozzle temp', '핫엔드'],
    'bed_temp': ['베드 온도', '베드온도', 'bed temp', '히팅베드'],
    'print_speed': ['속도', 'speed', '빠르게', '느리게'],
    'retraction': ['retraction', '리트랙션', '당김'],
    'layer_height': ['레이어 높이', '적층 높이', 'layer height'],
    'fan_speed': ['팬 속도', 'fan', '쿨링', '냉각'],
    'flow_rate': ['flow', '플로우', '압출량'],
  };

  const parametersMentioned: string[] = [];
  for (const [param, patterns] of Object.entries(parameterPatterns)) {
    if (patterns.some(p => queryLower.includes(p))) {
      parametersMentioned.push(param);
    }
  }

  // 검색 전략 결정
  const searchStrategies: ResearchPlan['searchStrategies'] = ['web', 'kb'];

  // 논문 검색 키워드 감지
  const paperKeywords = ['논문', 'paper', '연구', 'ieee', 'research', '학술'];
  if (paperKeywords.some(k => queryLower.includes(k))) {
    searchStrategies.push('paper');
  }

  return {
    mainQuery: query,
    subQueries: [query],
    searchStrategies,
    materialType,
    defectType,
    parametersMentioned,
  };
}

/**
 * 검색 수행 (웹 + 지식베이스, 병렬)
 */
async function performSearch(
  plan: ResearchPlan,
  env: Env
): Promise<{
  webResults: SearchResult[];
  kbResults: SearchResult[];
}> {
  const searchPromises: Promise<SearchResult[]>[] = [];

  // 웹 검색 (결과 수 축소: 5 → 3)
  if (plan.searchStrategies.includes('web')) {
    searchPromises.push(search3DPrintingWeb(plan.mainQuery, env, 3));
  } else {
    searchPromises.push(Promise.resolve([]));
  }

  // 지식베이스 검색 (동기)
  const kbResults = searchKnowledgeBase(plan.materialType, plan.defectType);
  searchPromises.push(Promise.resolve(kbResults));

  const [webResults, kbResultsResolved] = await Promise.all(searchPromises);

  return {
    webResults: deduplicateResults(webResults),
    kbResults: deduplicateResults(kbResultsResolved)
  };
}

// 통합 프롬프트 (쿼리 분석 + 종합 + 추천 생성을 한 번에)
const UNIFIED_SYNTHESIS_PROMPT = `당신은 3D 프린팅 전문가입니다. 아래 질문과 검색 결과를 바탕으로 실용적인 답변을 제공하세요.

## 매우 중요: 문장별 출처 인용 규칙
- 각 문장 끝에 해당 정보의 출처 번호를 반드시 표시하세요
- 형식: "문장 내용입니다.[1]" (문장 바로 뒤에 [번호] 붙이기)
- 한 문장에 여러 출처가 있으면: "문장 내용입니다.[1][2]"
- 출처가 없는 일반적인 설명은 출처 번호 없이 작성

예시:
"PLA는 3D 프린팅에서 가장 보편적인 재료입니다.[1] 노즐 온도는 190-220°C가 권장됩니다.[2] 특히 210°C에서 최적의 결과를 얻을 수 있습니다.[1][3]"

## 답변 형식
JSON 형식으로 응답하세요:
{
  "synthesis": "문제 분석 (각 문장 끝에 [1], [2] 형식의 출처 번호 포함)",
  "recommendations": [
    {
      "parameter": "파라미터 이름 (한글)",
      "current_value": null,
      "recommended_value": "추천값 (단위 포함)",
      "confidence": 0.0~1.0 사이 신뢰도,
      "source_indices": [1, 2],
      "reasoning": "이 추천 이유 (문장별 출처 포함)[1]"
    }
  ]
}

## 규칙
1. 모든 구체적인 수치나 주장에는 반드시 문장 끝에 출처 번호 [1], [2] 등을 포함
2. synthesis는 2-3문단으로 핵심만 설명
3. recommendations는 3-5개 이내로 중요한 것만
4. 각 reasoning도 문장별로 출처 표시`;

// 소스 정보 타입
interface SourceInfo {
  index: number;
  url: string;
  title: string;
  isInternal: boolean;
}

/**
 * 단일 LLM 호출로 종합 및 추천 생성
 */
async function synthesizeOnce(
  query: string,
  allResults: SearchResult[],
  env: Env
): Promise<{
  synthesis: string;
  recommendations: ParameterRecommendation[];
  sources: SourceInfo[];
}> {
  // 결과가 없으면 기본 응답
  if (allResults.length === 0) {
    return {
      synthesis: '검색 결과를 찾을 수 없습니다. 질문을 더 구체적으로 작성해주세요.',
      recommendations: [],
      sources: [],
    };
  }

  // 검색 결과를 컨텍스트로 변환 (최대 10개, 번호 매기기)
  const sortedResults = [...allResults]
    .sort((a, b) => b.relevanceScore - a.relevanceScore)
    .slice(0, 10);

  // 소스 정보 저장 (나중에 [1], [2] 참조용)
  const sources: SourceInfo[] = sortedResults.map((r, idx) => ({
    index: idx + 1,
    url: r.url,
    title: r.title,
    isInternal: r.url.startsWith('internal://'),
  }));

  // 번호가 매겨진 검색 결과 텍스트 생성
  const resultsText = sortedResults
    .map((r, idx) => `[${idx + 1}] ${r.title}\n출처: ${r.source}\n내용: ${r.content.slice(0, 400)}`)
    .join('\n\n---\n\n');

  const prompt = `${UNIFIED_SYNTHESIS_PROMPT}

## 질문
${query}

## 검색 결과 (번호로 인용하세요)
${resultsText}`;

  const responseText = await callGemini(prompt, env);

  const parsed = parseJsonResponse<{
    synthesis: string;
    recommendations: Array<{
      parameter: string;
      current_value: string | null;
      recommended_value: string;
      confidence: number;
      source_indices?: number[];
      sources?: string[];
      reasoning: string;
    }>;
  }>(responseText);

  if (parsed) {
    return {
      synthesis: parsed.synthesis,
      recommendations: (parsed.recommendations || []).map((r) => ({
        parameter: r.parameter,
        currentValue: r.current_value,
        recommendedValue: r.recommended_value,
        confidence: r.confidence,
        sources: r.source_indices
          ? r.source_indices.map(i => sources[i - 1]?.url || '').filter(Boolean)
          : (r.sources || []),
        reasoning: r.reasoning,
      })),
      sources,
    };
  }

  // JSON 파싱 실패 시 원본 텍스트 반환
  return {
    synthesis: responseText,
    recommendations: [],
    sources,
  };
}

/**
 * 추천 검증 (범위 확인)
 */
function validateRecommendations(
  recommendations: ParameterRecommendation[]
): ParameterRecommendation[] {
  const VALID_RANGES: Record<string, [number, number]> = {
    '노즐 온도': [180, 300],
    nozzle_temp: [180, 300],
    '베드 온도': [40, 120],
    bed_temp: [40, 120],
    '출력 속도': [10, 200],
    print_speed: [10, 200],
    '레이어 높이': [0.05, 0.5],
    layer_height: [0.05, 0.5],
    'Retraction 거리': [0.5, 10],
    retraction_distance: [0.5, 10],
    'Retraction 속도': [10, 100],
    retraction_speed: [10, 100],
  };

  return recommendations.map((rec) => {
    try {
      let valueStr = rec.recommendedValue;
      for (const unit of ['°C', 'mm/s', 'mm', '%']) {
        valueStr = valueStr.replace(unit, '');
      }
      valueStr = valueStr.trim().split('-')[0];
      const value = parseFloat(valueStr);

      const range = VALID_RANGES[rec.parameter];
      if (range && (value < range[0] || value > range[1])) {
        return {
          ...rec,
          confidence: rec.confidence * 0.5,
          reasoning: `${rec.reasoning} (주의: 일반적 범위 ${range[0]}-${range[1]} 벗어남)`,
        };
      }
    } catch {
      // 파싱 실패 시 그대로 반환
    }
    return rec;
  });
}

/**
 * 문장 전체를 클릭 가능한 하이퍼링크로 변환
 * 입력: "PLA는 좋은 재료입니다.[1] 온도는 200°C입니다.[2]"
 * 출력: "[PLA는 좋은 재료입니다.](url1) [온도는 200°C입니다.](url2)"
 */
function convertSentencesToLinks(text: string, sources: SourceInfo[]): string {
  // 문장 단위로 분리하여 처리
  // 패턴: 텍스트 + 마침표류(선택) + [숫자] 조합
  const pattern = /([^[\]]+?)([.!?])?(\[(\d+)\](?:\[(\d+)\])?(?:\[(\d+)\])?)/g;

  return text.replace(pattern, (match, sentence, punctuation, fullCitation, num1, num2, num3) => {
    if (!num1) return match;

    const primaryIndex = parseInt(num1, 10) - 1;
    const source = sources[primaryIndex];
    const cleanSentence = (sentence + (punctuation || '')).trim();

    if (!cleanSentence) return match;

    if (source && !source.isInternal && source.url) {
      // 외부 소스: 문장 전체를 클릭 가능한 링크로
      const otherNums = [num2, num3].filter(Boolean);
      const otherRefs = otherNums.length > 0 ? ' ' + otherNums.map(n => `[[${n}]](${sources[parseInt(n, 10) - 1]?.url || '#'})`).join(' ') : '';
      return `[${cleanSentence}](${source.url})${otherRefs}`;
    } else if (source && source.isInternal) {
      // 내부 소스: 문장에 소스 이름 표시
      const refNums = [num1, num2, num3].filter(Boolean).map(n => `[${n}]`).join('');
      return `${cleanSentence} *(${source.title})*`;
    }

    return match;
  });
}

/**
 * [1], [2] 형식의 단순 인용을 링크로 변환 (테이블 등에서 사용)
 */
function convertSimpleCitations(text: string, sources: SourceInfo[]): string {
  return text.replace(/\[(\d+)\]/g, (match, num) => {
    const index = parseInt(num, 10) - 1;
    const source = sources[index];
    if (source && !source.isInternal) {
      return `[[${num}]](${source.url})`;
    }
    return `[${num}]`;
  });
}

/**
 * 최종 응답 생성
 */
function generateOutput(state: AgentState, sources: SourceInfo[]): string {
  const { recommendations, synthesizedKnowledge, confidenceScore } = state;

  // 내부/외부 소스 분리
  const externalSources = sources.filter(s => !s.isInternal);
  const internalSources = sources.filter(s => s.isInternal);

  // synthesis의 문장들을 클릭 가능한 링크로 변환
  const synthesisWithLinks = convertSentencesToLinks(synthesizedKnowledge || '', sources);

  // 추천 테이블
  let recTable: string;
  if (recommendations.length > 0) {
    recTable = '| 파라미터 | 현재값 | 추천값 | 신뢰도 |\n';
    recTable += '|----------|--------|--------|--------|\n';
    for (const rec of recommendations) {
      const current = rec.currentValue || 'N/A';
      recTable += `| ${rec.parameter} | ${current} | ${rec.recommendedValue} | ${Math.round(rec.confidence * 100)}% |\n`;
    }
  } else {
    recTable = '추천을 생성할 수 없습니다.';
  }

  // 상세 설명 (문장별 링크 변환)
  const detailed = recommendations
    .slice(0, 5)
    .map((r) => `**${r.parameter}**: ${convertSentencesToLinks(r.reasoning, sources)}`)
    .join('\n\n');

  // 소스 포맷
  let sourcesFormatted = '';

  // 외부 웹 소스 (클릭 가능)
  if (externalSources.length > 0) {
    sourcesFormatted += '**웹 검색 결과:**\n';
    sourcesFormatted += externalSources
      .slice(0, 5)
      .map((s) => `[${s.index}] [${getShortenedUrl(s.url)}](${s.url})`)
      .join('\n');
  }

  // 내장 지식베이스 소스
  if (internalSources.length > 0) {
    if (sourcesFormatted) sourcesFormatted += '\n\n';
    sourcesFormatted += '**내장 지식베이스:**\n';
    sourcesFormatted += internalSources
      .slice(0, 3)
      .map((s) => `[${s.index}] ${s.title}`)
      .join('\n');
  }

  return FINAL_RESPONSE_TEMPLATE
    .replace('{synthesis}', synthesisWithLinks || '분석 중...')
    .replace('{confidence}', `${Math.round(confidenceScore * 100)}%`)
    .replace('{recommendations_table}', recTable)
    .replace('{detailed_reasoning}', detailed || '상세 설명 없음')
    .replace('{additional_tips}', '- 필라멘트 건조 권장\n- 베드 레벨링 확인')
    .replace('{sources}', sourcesFormatted || '소스 없음')
    .replace('{num_sources}', String(sources.length))
    .replace('{iterations}', '1');
}

/**
 * URL을 짧게 표시 (도메인 + 일부 경로)
 */
function getShortenedUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const domain = parsed.hostname.replace('www.', '');
    const path = parsed.pathname.length > 20
      ? parsed.pathname.slice(0, 20) + '...'
      : parsed.pathname;
    return domain + path;
  } catch {
    return url.length > 40 ? url.slice(0, 40) + '...' : url;
  }
}

/**
 * 메인 리서치 실행 (최적화: LLM 1회 호출)
 */
export async function runResearch(query: string, env: Env): Promise<string> {
  // 초기 상태
  const state: AgentState = {
    originalQuery: query,
    researchPlan: null,
    webResults: [],
    kbResults: [],
    paperResults: [],
    iterationCount: 1,
    isSufficient: true,
    confidenceScore: 0.8,
    missingInfo: [],
    synthesizedKnowledge: '',
    recommendations: [],
    finalResponse: '',
    sourcesCited: [],
    errors: [],
  };

  try {
    // 1. 쿼리 분석 (로컬, LLM 호출 없음)
    state.researchPlan = parseQueryLocal(query);

    // 2. 검색 수행 (웹 + 지식베이스 병렬)
    const searchResults = await performSearch(state.researchPlan, env);
    state.webResults = searchResults.webResults;
    state.kbResults = searchResults.kbResults;

    // 3. 종합 및 추천 생성 (단일 LLM 호출)
    const allResults = [...state.webResults, ...state.kbResults];
    const synthesis = await synthesizeOnce(query, allResults, env);
    state.synthesizedKnowledge = synthesis.synthesis;
    state.recommendations = validateRecommendations(synthesis.recommendations);
    const sources = synthesis.sources;

    // 신뢰도 계산 (추천이 있으면 높게)
    if (state.recommendations.length > 0) {
      const avgConfidence = state.recommendations.reduce((sum, r) => sum + r.confidence, 0) / state.recommendations.length;
      state.confidenceScore = avgConfidence;
    }

    // 4. 최종 응답 생성
    state.finalResponse = generateOutput(state, sources);

    return state.finalResponse;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return `오류가 발생했습니다: ${errorMessage}\n\n잠시 후 다시 시도해주세요.`;
  }
}

/**
 * 결과 중복 제거
 */
function deduplicateResults(results: SearchResult[]): SearchResult[] {
  const seen = new Set<string>();
  return results.filter((r) => {
    if (seen.has(r.url)) return false;
    seen.add(r.url);
    return true;
  });
}
