/**
 * POST /api/research - 3D 프린팅 연구 엔드포인트
 */

import { runResearch } from '../lib/workflow';
import type { Env, ResearchRequest, ResearchResponse } from '../lib/types';

interface CFContext {
  request: Request;
  env: Env;
}

export async function onRequestPost(context: CFContext): Promise<Response> {
  const { request, env } = context;

  try {
    // 요청 파싱
    const body: ResearchRequest = await request.json();

    if (!body.query || typeof body.query !== 'string') {
      return new Response(
        JSON.stringify({
          response: '',
          sources: [],
          success: false,
          error: 'query 필드가 필요합니다.',
        } as ResearchResponse),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // 쿼리 강화 (재료, 파라미터 정보 추가)
    let enhancedQuery = body.query;
    if (body.material) {
      enhancedQuery = `[재료: ${body.material}] ${enhancedQuery}`;
    }
    if (body.currentParams) {
      const paramsStr = Object.entries(body.currentParams)
        .map(([k, v]) => `${k}=${v}`)
        .join(', ');
      enhancedQuery = `${enhancedQuery} (현재 설정: ${paramsStr})`;
    }

    // 연구 실행
    const response = await runResearch(enhancedQuery, env);

    return new Response(
      JSON.stringify({
        response,
        sources: [],
        success: true,
      } as ResearchResponse),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Research error:', errorMessage);

    return new Response(
      JSON.stringify({
        response: '',
        sources: [],
        success: false,
        error: errorMessage,
      } as ResearchResponse),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
