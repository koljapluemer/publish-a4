import type { Card, Collage, Metadata, Placement } from './types'

interface ApiErrorBody {
  error?: { message?: string }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`
    try {
      const body = await response.json() as ApiErrorBody
      message = body.error?.message || message
    } catch {
      // Keep the HTTP status when the response is not JSON.
    }
    throw new Error(message)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

function cardUrl(collage: string, card: string): string {
  return `/api/collages/${encodeURIComponent(collage)}/cards/${encodeURIComponent(card)}`
}

export async function listCollages(): Promise<Collage[]> {
  const result = await request<{ collages: Collage[] }>('/api/collages')
  return result.collages
}

export function createCollage(name: string): Promise<Collage> {
  return request<Collage>('/api/collages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function updateMetadata(collage: string, value: Metadata): Promise<Metadata> {
  return request<Metadata>(`/api/collages/${encodeURIComponent(collage)}/metadata`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(value),
  })
}

export function renameCollage(collage: string, name: string): Promise<{ name: string }> {
  return request<{ name: string }>(`/api/collages/${encodeURIComponent(collage)}/name`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export async function exportAll(): Promise<number> {
  const result = await request<{ collages: unknown[] }>('/api/export', { method: 'POST' })
  return result.collages.length
}

export function getCard(collage: string, card: string): Promise<Card> {
  return request<Card>(cardUrl(collage, card))
}

export function createCard(
  collage: string,
  value: { name: string; source: string; top: number; left: number },
): Promise<Card> {
  return request<Card>(`/api/collages/${encodeURIComponent(collage)}/cards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(value),
  })
}

export function createImageCard(
  collage: string,
  value: { name: string; image: Blob; top: number; left: number },
): Promise<Card> {
  const body = new FormData()
  body.append('name', value.name)
  body.append('image', value.image)
  body.append('top', String(value.top))
  body.append('left', String(value.left))
  return request<Card>(`/api/collages/${encodeURIComponent(collage)}/image-cards`, {
    method: 'POST',
    body,
  })
}

export function updateCard(collage: string, card: string, source: string): Promise<Card> {
  return request<Card>(cardUrl(collage, card), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source }),
  })
}

export function deleteCard(collage: string, card: string): Promise<void> {
  return request<void>(cardUrl(collage, card), { method: 'DELETE' })
}

export type { Card, Collage, Metadata, Placement }
