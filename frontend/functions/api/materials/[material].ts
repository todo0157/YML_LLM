/**
 * GET /api/materials/:material - 재료 가이드 조회
 */

import { getMaterialGuide } from '../../lib/knowledge-base';

interface CFContext {
  params: {
    material: string;
  };
}

export async function onRequestGet(context: CFContext): Promise<Response> {
  const { material } = context.params;
  const guide = getMaterialGuide(material);

  return new Response(
    JSON.stringify({
      material: material.toUpperCase(),
      guide,
      found: guide !== null,
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
}
