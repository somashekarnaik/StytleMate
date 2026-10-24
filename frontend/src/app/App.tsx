import { useCallback, useEffect, useRef, useState } from "react";
import {
  Check,
  ChevronDown,
  CloudSun,
  Heart,
  Plus,
  Shirt,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";
import {
  addClothing,
  deleteClothing,
  getClothing,
  getRecommendations,
  type RecommendationFilters,
} from "../services/api";
import type {
  Category,
  ClothingStyle,
  ClothingItem,
  Gender,
  OutfitRecommendation,
  Weather,
} from "../types";

interface PhotoDraft {
  id: string;
  file: File;
  previewUrl: string;
  name: string;
  category: Category | "auto";
}

const categories: Category[] = ["top", "bottom", "shoes", "outerwear", "accessory"];
const styles: { value: ClothingStyle; label: string }[] = [
  { value: "western", label: "Western wear" },
  { value: "casual", label: "Casual wear" },
  { value: "traditional", label: "Traditional wear" },
  { value: "formal", label: "Formal wear" },
  { value: "sports", label: "Sports wear" },
  { value: "winter", label: "Winter wear" },
  { value: "summer", label: "Summer wear" },
  { value: "party", label: "Party wear" },
  { value: "wedding", label: "Wedding wear" },
  { value: "loungewear", label: "Loungewear" },
  { value: "streetwear", label: "Streetwear" },
  { value: "college", label: "College wear" },
];

function getStyleLabel(style: ClothingStyle): string {
  return styles.find((option) => option.value === style)?.label ?? style;
}

function getMissingCategoryLabels(categoriesMissing: Category[]): string {
  const labels: Record<Category, string> = {
    top: "a top",
    bottom: "a bottom",
    shoes: "shoes",
    outerwear: "outerwear",
    accessory: "an accessory",
  };
  return categoriesMissing.map((category) => labels[category]).join(" and ");
}

function App() {
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [recommendations, setRecommendations] = useState<OutfitRecommendation[]>([]);
  const [weather, setWeather] = useState<Weather | "">("");
  const [occasion, setOccasion] = useState("Any occasion");
  const [preferredColor, setPreferredColor] = useState("");
  const [preferredStyle, setPreferredStyle] = useState<ClothingStyle | "">("");
  const [preferredGender, setPreferredGender] = useState<Exclude<Gender, "unisex"> | "">("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [findingOutfits, setFindingOutfits] = useState(false);
  const [recommendationMessage, setRecommendationMessage] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeTab, setActiveTab] = useState<"wardrobe" | "outfits">("wardrobe");
  const [photoDrafts, setPhotoDrafts] = useState<PhotoDraft[]>([]);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const photoDraftsRef = useRef(photoDrafts);
  photoDraftsRef.current = photoDrafts;

  const refreshItems = useCallback(async () => {
    setItems(await getClothing());
  }, []);

  const refreshRecommendations = useCallback(async (
    filters: RecommendationFilters = {
      weather,
      occasion: occasion === "Any occasion" ? "" : occasion,
      color: preferredColor.trim(),
      style: preferredStyle,
      gender: preferredGender,
    },
  ) => {
    setFindingOutfits(true);
    try {
      const result = await getRecommendations(filters);
      setRecommendations(result.recommendations);
      setRecommendationMessage(result.message);
      return result;
    } finally {
      setFindingOutfits(false);
    }
  }, [weather, occasion, preferredColor, preferredStyle, preferredGender]);

  useEffect(() => {
    Promise.all([refreshItems(), refreshRecommendations()])
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "Could not load StyleMate."),
      )
      .finally(() => setLoading(false));
  }, [refreshItems, refreshRecommendations]);

  useEffect(() => () => {
    photoDraftsRef.current.forEach((draft) => URL.revokeObjectURL(draft.previewUrl));
  }, []);

  async function handleAddClothing(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!photoDrafts.length) {
      setError("Choose at least one clothing photo.");
      return;
    }
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setSaving(true);
    let uploadedCount = 0;
    try {
      for (const draft of photoDrafts) {
        await addClothing({
          name: draft.name,
          category: draft.category,
          style: String(form.get("style")) as ClothingStyle | "auto",
          gender: String(form.get("gender")) as Gender | "auto",
          color: "",
          season: String(form.get("season")),
          occasions: String(form.get("occasions")),
          photo: draft.file,
        });
        uploadedCount += 1;
      }
      photoDrafts.forEach((draft) => URL.revokeObjectURL(draft.previewUrl));
      setPhotoDrafts([]);
      formElement.reset();
      setWeather("");
      setOccasion("Any occasion");
      setPreferredColor("");
      setPreferredStyle("");
      setPreferredGender("");
      const [, outfitResult] = await Promise.all([
        refreshItems(),
        refreshRecommendations({
          weather: "",
          occasion: "",
          color: "",
          style: "",
          gender: "",
        }),
      ]);
      setSuccess(
        outfitResult.recommendations.length
          ? `Added ${uploadedCount} ${uploadedCount === 1 ? "item" : "items"} and generated ${outfitResult.recommendations.length} outfit ${outfitResult.recommendations.length === 1 ? "combination" : "combinations"}.`
          : `Added ${uploadedCount} ${uploadedCount === 1 ? "item" : "items"}. ${outfitResult.message ?? "Add more wardrobe pieces to build a complete outfit."}`,
      );
      setActiveTab("outfits");
    } catch (reason) {
      setError(
        `${uploadedCount} of ${photoDrafts.length} photos were saved. ${
          reason instanceof Error ? reason.message : "Could not process the remaining photos."
        }`,
      );
      if (uploadedCount) {
        const remaining = photoDrafts.slice(uploadedCount);
        photoDrafts.slice(0, uploadedCount).forEach((draft) => URL.revokeObjectURL(draft.previewUrl));
        setPhotoDrafts(remaining);
        setWeather("");
        setOccasion("Any occasion");
        setPreferredColor("");
        setPreferredStyle("");
        setPreferredGender("");
        await Promise.all([
          refreshItems(),
          refreshRecommendations({
            weather: "",
            occasion: "",
            color: "",
            style: "",
            gender: "",
          }),
        ]);
        setActiveTab("outfits");
      }
    } finally {
      setSaving(false);
    }
  }

  function handlePhotosSelected(files: FileList | null) {
    setError("");
    setSuccess("");
    if (!files?.length) {
      return;
    }
    const validFiles: File[] = [];
    const oversizedFiles: string[] = [];
    Array.from(files).forEach((file) => {
      if (file.size > 8 * 1024 * 1024) {
        oversizedFiles.push(file.name);
      } else {
        validFiles.push(file);
      }
    });
    if (oversizedFiles.length) {
      setError(`${oversizedFiles.join(", ")} ${oversizedFiles.length === 1 ? "is" : "are"} larger than 8 MB and ${oversizedFiles.length === 1 ? "was" : "were"} skipped.`);
    }
    const newDrafts = validFiles.map((file) => ({
      id: `${file.name}-${file.lastModified}-${crypto.randomUUID()}`,
      file,
      previewUrl: URL.createObjectURL(file),
      name: "",
      category: "auto" as const,
    }));
    setPhotoDrafts((current) => [...current, ...newDrafts]);
    if (photoInputRef.current) photoInputRef.current.value = "";
  }

  function updatePhotoDraft(id: string, update: Partial<Pick<PhotoDraft, "name" | "category">>) {
    setPhotoDrafts((drafts) =>
      drafts.map((draft) => draft.id === id ? { ...draft, ...update } : draft),
    );
  }

  function removePhotoDraft(id: string) {
    const removed = photoDrafts.find((draft) => draft.id === id);
    if (removed) URL.revokeObjectURL(removed.previewUrl);
    setPhotoDrafts((drafts) => drafts.filter((draft) => draft.id !== id));
  }

  async function handleDelete(id: number) {
    setError("");
    try {
      await deleteClothing(id);
      await Promise.all([refreshItems(), refreshRecommendations()]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not remove this item.");
    }
  }

  async function handleFiltersChanged() {
    setError("");
    try {
      await refreshRecommendations();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not get outfit ideas.");
    }
  }

  const categoryCounts = categories.reduce<Record<string, number>>((counts, category) => {
    counts[category] = items.filter((item) => item.category === category).length;
    return counts;
  }, {});

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#home" aria-label="StyleMate home">
          <span className="brand-mark"><Shirt size={21} /></span>
          <span>stylemate<span className="brand-dot">.</span></span>
        </a>
        <div className="sidebar-label">YOUR SPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          <button
            className={`nav-item ${activeTab === "wardrobe" ? "selected" : ""}`}
            onClick={() => setActiveTab("wardrobe")}
          >
            <Shirt size={18} /> My wardrobe
            <span className="nav-count">{items.length}</span>
          </button>
          <button
            className={`nav-item ${activeTab === "outfits" ? "selected" : ""}`}
            onClick={() => setActiveTab("outfits")}
          >
            <Sparkles size={18} /> Outfit ideas
          </button>
        </nav>
        <div className="sidebar-tip">
          <div className="tip-icon"><Heart size={17} /></div>
          <strong>Wear what you have.</strong>
          <p>Your next favorite outfit might already be in your closet.</p>
        </div>
        <div className="sidebar-footer"><span className="avatar">S</span><span>My StyleMate</span></div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <span className="breadcrumb">YOUR STYLE / <strong>{activeTab === "wardrobe" ? "WARDROBE" : "OUTFIT IDEAS"}</strong></span>
          <div className="weather-chip"><CloudSun size={17} /><span>Style for the day</span></div>
        </header>
        <div className="page-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">A LITTLE INSPIRATION, JUST FOR YOU</p>
              <h1>Your wardrobe,<br /><span>reimagined.</span></h1>
              <p className="intro">Make the most of what you already own. Find fresh combinations, one outfit at a time.</p>
            </div>
            <div className="welcome-art" aria-hidden="true">
              <div className="sun-orbit" />
              <span className="art-star star-one">✳</span>
              <span className="art-star star-two">✳</span>
              <span className="art-shirt"><Shirt size={94} strokeWidth={1} /></span>
              <span className="art-caption">YOUR CLOSET<br />IS FULL OF POSSIBILITIES</span>
            </div>
          </section>

          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {success && <div className="notice success-notice"><Check size={16} />{success}</div>}

          <div className="tab-row">
            <button className={activeTab === "wardrobe" ? "tab active" : "tab"} onClick={() => setActiveTab("wardrobe")}>My wardrobe <span>{items.length}</span></button>
            <button className={activeTab === "outfits" ? "tab active" : "tab"} onClick={() => setActiveTab("outfits")}>Outfit ideas</button>
          </div>

          {activeTab === "wardrobe" ? (
            <>
            <div className="workspace-grid">
              <section className="wardrobe-panel">
                <div className="section-heading">
                  <div><p className="eyebrow">THE GOOD STUFF</p><h2>Your pieces</h2></div>
                  <span className="item-total">{items.length} {items.length === 1 ? "piece" : "pieces"}</span>
                </div>
                <div className="category-row">
                  {categories.map((category) => (
                    <div className="category-pill" key={category}>
                      <span>{category}</span><b>{categoryCounts[category]}</b>
                    </div>
                  ))}
                </div>
                {loading ? <div className="empty-state">Opening your wardrobe…</div> : items.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon"><Shirt size={27} /></div>
                    <h3>Your wardrobe starts here</h3>
                    <p>Add a few favorites and StyleMate will start building outfit ideas from them.</p>
                  </div>
                ) : (
                  <div className="clothing-grid">
                    {items.map((item) => (
                      <article className="clothing-card" key={item.id}>
                        <div className="clothing-image-wrap">
                          <img src={item.image_url} alt={item.name} className="clothing-image" />
                          <button className="remove-button" title={`Delete ${item.name}`} aria-label={`Delete ${item.name}`} onClick={() => void handleDelete(item.id)}><Trash2 size={15} /><span>Delete</span></button>
                        </div>
                        <div className="clothing-meta">
                          <div><strong>{item.name}</strong><span>{getStyleLabel(item.style)} · {item.gender} · {item.category}</span></div>
                          <span className="color-dot" style={{ backgroundColor: item.color }} title={item.color} />
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <aside className="add-panel">
                <div className="add-panel-title"><span className="add-icon"><Plus size={19} /></span><div><h2>Add a piece</h2><p>Bring something from your closet</p></div></div>
                <form onSubmit={(event) => void handleAddClothing(event)} className="add-form">
                  <label className="upload-box">
                    <input
                      ref={photoInputRef}
                      type="file"
                      accept="image/*"
                      multiple
                      aria-label="Choose clothing photos from your device"
                      onChange={(event) => {
                        handlePhotosSelected(event.target.files);
                        event.target.value = "";
                      }}
                    />
                    <Upload size={22} />
                    <strong>{photoDrafts.length ? "Add more clothing photos" : "Choose clothing photos"}</strong>
                    <span>Analyzed privately on this device · up to 8 MB each</span>
                  </label>
                  <p className="upload-help">{photoDrafts.length ? "StyleMate will identify each garment, color, style, audience, and season on your computer. You can override any detected details." : "Select clothing photos. StyleMate analyzes each garment locally, then finds the best outfit combinations from your wardrobe."}</p>
                  {photoDrafts.length > 0 && (
                    <div className="photo-draft-list">
                      {photoDrafts.map((draft) => (
                        <article className="photo-draft" key={draft.id}>
                          <img src={draft.previewUrl} alt={`Preview of ${draft.name}`} />
                          <div className="photo-draft-fields">
                            <label className="field-label">ITEM NAME (OPTIONAL)<input value={draft.name} placeholder={draft.file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ")} onChange={(event) => updatePhotoDraft(draft.id, { name: event.target.value })} maxLength={100} /></label>
                            <label className="field-label">CATEGORY<select value={draft.category} onChange={(event) => updatePhotoDraft(draft.id, { category: event.target.value as Category | "auto" })}><option value="auto">Auto-detect</option>{categories.map((category) => <option value={category} key={category}>{category}</option>)}</select></label>
                          </div>
                          <button className="remove-draft-button" type="button" aria-label={`Remove ${draft.name} from upload`} title="Remove photo" onClick={() => removePhotoDraft(draft.id)}><Trash2 size={15} /></button>
                        </article>
                      ))}
                    </div>
                  )}
                  <div className="field-row">
                    <label className="field-label">STYLE<select name="style" defaultValue="auto"><option value="auto">Auto-detect</option>{styles.map((style) => <option value={style.value} key={style.value}>{style.label}</option>)}</select><ChevronDown className="select-icon" size={14} /></label>
                    <label className="field-label">FOR<select name="gender" defaultValue="auto"><option value="auto">Auto-detect</option><option value="women">Women</option><option value="men">Men</option><option value="unisex">Unisex</option></select><ChevronDown className="select-icon" size={14} /></label>
                  </div>
                  <div className="field-row">
                    <label className="field-label">SEASON<select name="season" defaultValue="auto"><option value="auto">Auto-detect</option><option value="all">All year</option><option value="spring">Spring</option><option value="summer">Summer</option><option value="autumn">Autumn</option><option value="winter">Winter</option></select><ChevronDown className="select-icon" size={14} /></label>
                    <label className="field-label">OCCASION<input name="occasions" placeholder="Casual, work..." /></label>
                  </div>
                  {photoDrafts.length > 0 && <button className="primary-button" type="submit" disabled={saving}>{saving ? `Analyzing ${photoDrafts.length} photo${photoDrafts.length === 1 ? "" : "s"}…` : `Analyze photos & build outfits (${photoDrafts.length})`} <Sparkles size={16} /></button>}
                </form>
              </aside>
            </div>
            {recommendations[0] && (
              <section className="best-match-panel">
                <div className="best-match-copy">
                  <p className="eyebrow"><Sparkles size={13} /> BEST OUTFIT MATCH</p>
                  <h2>A new outfit idea from your wardrobe</h2>
                  <p className="best-match-items">{recommendations[0].items.map((item) => item.name).join(" + ")}</p>
                  <p className="best-match-reason">{recommendations[0].reason}</p>
                  {recommendations[0].missing_categories.length > 0 && (
                    <p className="best-match-reason">Pair it with {getMissingCategoryLabels(recommendations[0].missing_categories)} to complete the look.</p>
                  )}
                  <span className="best-match-score">{recommendations[0].score}% match</span>
                  <button className="text-button" onClick={() => setActiveTab("outfits")}>See more outfit ideas →</button>
                </div>
                <div className="best-match-preview">
                  <span>OUTFIT BOARD · YOUR CLOTHES</span>
                  <img src={recommendations[0].preview_url} alt="Example outfit combination made from your uploaded clothing photos" />
                </div>
              </section>
            )}
            </>
          ) : (
            <section className="outfit-panel">
              <div className="section-heading">
                <div><p className="eyebrow">NEW WAYS TO STYLE YOUR PIECES</p><h2>Fresh ways to wear it</h2></div>
                <Sparkles className="heading-sparkle" size={25} />
              </div>
              <p className="outfit-intro">StyleMate builds outfit ideas from your clothes and suggests what would complete each look.</p>
              <div className="filter-row">
                <label className="filter-field">WEATHER<select value={weather} onChange={(event) => setWeather(event.target.value as Weather | "")}><option value="">Any weather</option><option value="hot">Warm & sunny</option><option value="mild">Mild</option><option value="cold">Cold</option><option value="rainy">Rainy</option></select></label>
                <label className="filter-field">OCCASION<select value={occasion} onChange={(event) => setOccasion(event.target.value)}><option>Any occasion</option><option>Everyday</option><option>Work</option><option>Casual</option><option>Formal</option></select></label>
                <label className="filter-field">STYLE<select value={preferredStyle} onChange={(event) => setPreferredStyle(event.target.value as ClothingStyle | "")}><option value="">Any style</option>{styles.map((style) => <option value={style.value} key={style.value}>{style.label}</option>)}</select></label>
                <label className="filter-field">FOR<select value={preferredGender} onChange={(event) => setPreferredGender(event.target.value as Exclude<Gender, "unisex"> | "")}><option value="">Everyone</option><option value="women">Women</option><option value="men">Men</option></select></label>
                <label className="filter-field">COLOR<input value={preferredColor} onChange={(event) => setPreferredColor(event.target.value)} placeholder="Any color" /></label>
                <button className="primary-button find-button" onClick={() => void handleFiltersChanged()} disabled={findingOutfits}><Sparkles size={16} /> {findingOutfits ? "Finding outfits…" : "Find outfits"}</button>
              </div>
              {recommendations.length === 0 ? (
                <div className="empty-state outfit-empty"><div className="empty-icon"><Sparkles size={25} /></div><h3>No outfit generated yet</h3><p>{recommendationMessage ?? "No outfits are available for these filters. Try changing your selections."}</p><button className="text-button" onClick={() => setActiveTab("wardrobe")}>Go to my wardrobe →</button></div>
              ) : (
                <div className="outfit-grid">
                  {recommendations.map((outfit, index) => (
                    <article className={`outfit-card ${index === 0 ? "featured" : ""}`} key={`${outfit.items.map((item) => item.id).join("-")}-${index}`}>
                      <div className="outfit-images"><img className="outfit-preview" src={outfit.preview_url} alt={`Example combination: ${outfit.items.map((item) => item.name).join(", ")}`} /></div>
                      <div className="outfit-details"><div className="outfit-number">LOOK {String(index + 1).padStart(2, "0")}<span>{outfit.score}% MATCH</span></div><h3>{outfit.items.map((item) => item.name).join(" + ")}</h3><p>{outfit.reason}</p>{outfit.missing_categories.length > 0 && <p className="outfit-missing">To complete this look: add {getMissingCategoryLabels(outfit.missing_categories)}.</p>}</div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}
          <footer className="page-footer"><span>Made for the clothes you already love.</span><span>STYLEMATE © 2026</span></footer>
        </div>
      </section>
    </main>
  );
}

export default App;
