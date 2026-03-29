import client from './client'
import type { FloorPlan } from '../types'

export async function getFloorPlans(): Promise<FloorPlan[]> {
  const response = await client.get<FloorPlan[]>('/api/floor-plans')
  return response.data
}

export async function getFloorPlan(id: number): Promise<FloorPlan> {
  const response = await client.get<FloorPlan>(`/api/floor-plans/${id}`)
  return response.data
}

export async function createFloorPlan(
  name: string,
  image: File,
  description?: string
): Promise<FloorPlan> {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('image', image)
  if (description) {
    formData.append('description', description)
  }

  const response = await client.post<FloorPlan>('/api/floor-plans', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function updateFloorPlan(
  id: number,
  data: { name?: string; description?: string; is_active?: boolean },
  image?: File
): Promise<FloorPlan> {
  const formData = new FormData()
  if (data.name !== undefined) formData.append('name', data.name)
  if (data.description !== undefined) formData.append('description', data.description)
  if (data.is_active !== undefined) formData.append('is_active', String(data.is_active))
  if (image) formData.append('image', image)

  const response = await client.put<FloorPlan>(`/api/floor-plans/${id}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function deleteFloorPlan(id: number): Promise<void> {
  await client.delete(`/api/floor-plans/${id}`)
}

export function getFloorPlanImageUrl(id: number): string {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const token = localStorage.getItem('access_token')
  return `${baseUrl}/api/floor-plans/${id}/image?token=${token}`
}
