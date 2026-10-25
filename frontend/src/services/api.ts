import type { Category, ClothingItem, ClothingStyle, Gender, OutfitAnalysis, OutfitRecommendation, Weather } from "../types";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new ApiError(body?.detail ?? `Request failed (${response.status})`, response.status);
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

export interface AuthUser {
  id: number;
  email: string;
}

export function getCurrentUser(): Promise<{ user: AuthUser }> {
  return request("/api/auth/me");
}

export function registerAccount(email: string, password: string): Promise<{ user: AuthUser }> {
  return request("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function loginAccount(email: string, password: string): Promise<{ user: AuthUser }> {
  return request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function logoutAccount(): Promise<void> {
  return request("/api/auth/logout", { method: "POST" });
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

export function analyzeOutfit(photo: File): Promise<OutfitAnalysis> {
  const form = new FormData();
  form.append("photo", photo);
  return request("/api/outfits/analyze", { method: "POST", body: form });
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
