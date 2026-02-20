/**
 * Gemini API 클라이언트
 */

import type { Env } from './types';

const FALLBACK_MODELS = ['gemini-2.0-flash', 'gemini-flash-latest'];

export async function callGemini(prompt: string, env: Env): Promise<string> {
  for (const model of FALLBACK_MODELS) {
    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GOOGLE_API_KEY}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contents: [
              {
                parts: [{ text: prompt }],
              },
            ],
            generationConfig: {
              temperature: 0.7,
              maxOutputTokens: 2048,
            },
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        // 모델을 찾을 수 없으면 다음 모델 시도
        if (error.error?.message?.includes('not found')) {
          continue;
        }
        throw new Error(error.error?.message || 'Gemini API error');
      }

      const data = await response.json();
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

      if (!text) {
        throw new Error('Empty response from Gemini');
      }

      return text;
    } catch (error) {
      // 마지막 모델이면 에러 throw
      if (model === FALLBACK_MODELS[FALLBACK_MODELS.length - 1]) {
        throw error;
      }
      // 아니면 다음 모델 시도
      continue;
    }
  }

  throw new Error('All Gemini models failed');
}

/**
 * JSON 응답 파싱 헬퍼
 */
export function parseJsonResponse<T>(text: string): T | null {
  try {
    // JSON 코드 블록 추출
    let content = text;
    if (content.includes('```json')) {
      content = content.split('```json')[1].split('```')[0];
    } else if (content.includes('```')) {
      content = content.split('```')[1].split('```')[0];
    }
    return JSON.parse(content.trim());
  } catch {
    return null;
  }
}
