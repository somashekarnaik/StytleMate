import type { Category, ClothingItem, ClothingStyle, Gender, OutfitRecommendation, Weather } from "../types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export interface NewClothingItem {
  name: string;
  category: Category | "auto";
  style: ClothingStyle | "auto";
  gender: Gender | "auto";
  color: string;
  season: string;
  occasions: string;
  photo: File;
}

export function getClothing(): Promise<ClothingItem[]> {
  return request("/api/clothing");
}

export function addClothing(item: NewClothingItem): Promise<ClothingItem> {
  const form = new FormData();
  Object.entries(item).forEach(([key, value]) => form.append(key, value));
  return request("/api/clothing", { method: "POST", body: form });
}

export function deleteClothing(id: number): Promise<void> {
  return request(`/api/clothing/${id}`, { method: "DELETE" });
}

export interface RecommendationFilters {
  weather: Weather | "";
  occasion: string;
  color: string;
  style: ClothingStyle | "";
  gender: Exclude<Gender, "unisex"> | "";
}

export async function getRecommendations(
  filters: RecommendationFilters,
): Promise<{ recommendations: OutfitRecommendation[]; message: string | null }> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return request(`/api/outfits/recommendations?${params.toString()}`);
}
