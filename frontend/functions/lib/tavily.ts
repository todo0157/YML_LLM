/**
 * Tavily 웹 검색 API
 */

import type { Env, SearchResult } from './types';

const WEB_DOMAINS = [
  'prusa3d.com',
  'help.prusa3d.com',
  'reddit.com/r/3Dprinting',
  'reddit.com/r/FixMyPrint',
  'all3dp.com',
  'simplify3d.com',
  'community.ultimaker.com',
  'matterhackers.com',
];

const PAPER_DOMAINS = [
  'arxiv.org',
  'ieee.org',
  'sciencedirect.com',
  'springer.com',
  'mdpi.com',
  'researchgate.net',
];

interface TavilyResponse {
  results: Array<{
    title: string;
    url: string;
    content: string;
    score: number;
  }>;
}

async function tavilySearch(
  query: string,
  env: Env,
  options: {
    searchDepth?: 'basic' | 'advanced';
    maxResults?: number;
    includeDomains?: string[];
  } = {}
): Promise<SearchResult[]> {
  const { searchDepth = 'advanced', maxResults = 5, includeDomains } = options;

  try {
    const response = await fetch('https://api.tavily.com/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_key: env.TAVILY_API_KEY,
        query,
        search_depth: searchDepth,
        max_results: maxResults,
        include_domains: includeDomains,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Tavily API error');
    }

    const data: TavilyResponse = await response.json();

    return data.results.map((r) => ({
      source: 'web' as const,
      url: r.url,
      title: r.title,
      content: r.content,
      relevanceScore: r.score,
    }));
  } catch (error) {
    console.error('Tavily search error:', error);
    return [];
  }
}

/**
 * 3D 프린팅 웹 검색
 */
export async function search3DPrintingWeb(
  query: string,
  env: Env,
  maxResults = 5
): Promise<SearchResult[]> {
  const enhancedQuery = `3D printing FDM ${query}`;
  const results = await tavilySearch(enhancedQuery, env, {
    searchDepth: 'advanced',
    maxResults,
    includeDomains: WEB_DOMAINS,
  });
  return results.map((r) => ({ ...r, source: 'web' as const }));
}

/**
 * 학술 논문 검색
 */
export async function search3DPrintingPapers(
  query: string,
  env: Env,
  maxResults = 3
): Promise<SearchResult[]> {
  const enhancedQuery = `FDM 3D printing ${query} research paper`;
  const results = await tavilySearch(enhancedQuery, env, {
    searchDepth: 'advanced',
    maxResults,
    includeDomains: PAPER_DOMAINS,
  });
  return results.map((r) => ({ ...r, source: 'paper' as const }));
}
