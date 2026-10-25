export type Category = "top" | "bottom" | "shoes" | "outerwear" | "accessory";
export type Weather = "hot" | "mild" | "cold" | "rainy";
export type ClothingStyle =
  | "western"
  | "casual"
  | "traditional"
  | "formal"
  | "sports"
  | "winter"
  | "summer"
  | "party"
  | "wedding"
  | "loungewear"
  | "streetwear"
  | "college";
export type Gender = "men" | "women" | "unisex";

export interface ClothingItem {
  id: number;
  name: string;
  category: Category;
  style: ClothingStyle;
  gender: Gender;
  color: string;
  season: string;
  occasions: string[];
  image_url: string;
  created_at: string;
}

export interface RecommendedItem {
  id: number;
  name: string;
  category: Category;
  style: ClothingStyle;
  gender: Gender;
  color: string;
  image_url: string;
}

export interface OutfitRecommendation {
  items: RecommendedItem[];
  missing_categories: Category[];
  score: number;
  reason: string;
  preview_url: string;
}

export interface OutfitAnalysis {
  summary: string;
  items: string[];
  color_palette: string;
  strengths: string[];
  suggestions: string[];
}
