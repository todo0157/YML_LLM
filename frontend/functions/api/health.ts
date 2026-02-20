/**
 * GET /api/health - 헬스 체크 엔드포인트
 */

export async function onRequest(): Promise<Response> {
  return new Response(JSON.stringify({ status: 'healthy' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
