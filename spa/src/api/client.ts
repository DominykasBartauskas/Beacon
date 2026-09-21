import type { components } from './openapi'

export type Dashboard = components['schemas']['DashboardResponse']
export type NewsItem = components['schemas']['NewsItem']
export type NewsList = components['schemas']['NewsListResponse']

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const beaconApi = {
  dashboard: () => get<Dashboard>('/api/v1/dashboard'),
  news: () => get<NewsList>('/api/v1/news'),
}
