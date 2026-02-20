/**
 * GET /api/materials - 재료 목록 조회
 */

import { getMaterialList } from '../../lib/knowledge-base';

export async function onRequestGet(): Promise<Response> {
  const materials = getMaterialList();

  return new Response(JSON.stringify(materials), {
    headers: { 'Content-Type': 'application/json' },
  });
}
