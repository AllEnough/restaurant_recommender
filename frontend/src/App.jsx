import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  ChefHat,
  Camera,
  ChevronDown,
  Clock3,
  CookingPot,
  Heart,
  LocateFixed,
  LogIn,
  LogOut,
  MapPin,
  Salad,
  Search,
  ShieldCheck,
  ShoppingBasket,
  Sparkles,
  Star,
  Utensils,
  UserPlus,
  X,
} from "lucide-react";
import { api } from "./api";

const restaurantDefaults = {
  scenario: "大學生省錢午餐", smart_mode: "省錢外食", budget: 150,
  max_distance: 10, category: "不限", weather: "普通", mood: "省錢",
  meal_time: "午餐", need_takeout: "不限", max_spicy_level: 2,
  prefer_fast: false, sort_by: "綜合推薦", min_rating: 0,
  top_n: 5, use_review_analysis: true, review_weight: 60,
  max_negative_ratio: 60, hide_high_risk: false, latitude: null, longitude: null,
};

const recipeDefaults = {
  scenario: "清冰箱減浪費", smart_mode: "清冰箱模式", max_time: 40,
  difficulty: "不限", max_calories: 750, max_missing: 2,
  only_cookable: false, top_n: 5,
  ingredients: [
    { name: "雞蛋", days_stored: 4, shelf_life: 14, price: 60, perishability: "中" },
    { name: "豆腐", days_stored: 2, shelf_life: 3, price: 35, perishability: "高" },
    { name: "蔥", days_stored: 3, shelf_life: 7, price: 25, perishability: "高" },
  ],
};

const quickScenarioValues = {
  "大學生省錢午餐": { smart_mode: "省錢外食", budget: 120, max_distance: 10, mood: "省錢", meal_time: "午餐", sort_by: "CP值優先" },
  "上班族快速外帶": { smart_mode: "快速午餐", budget: 160, max_distance: 7, mood: "疲累", meal_time: "午餐", need_takeout: "yes", prefer_fast: true, sort_by: "距離最近" },
  "老師聚餐不踩雷": { smart_mode: "不想踩雷", budget: 240, max_distance: 14, mood: "選擇困難", meal_time: "晚餐", sort_by: "評分最高", min_rating: 4 },
  "手動自訂": { smart_mode: "自訂" },
};

function Field({ label, children, hint }) {
  return <label className="grid gap-1.5 text-sm font-bold text-ink">{label}{children}{hint && <span className="text-xs font-normal text-muted">{hint}</span>}</label>;
}

function Select({ value, onChange, children }) {
  return <select className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-medium" value={value} onChange={onChange}>{children}</select>;
}

function Metric({ label, value, tone = "plain" }) {
  const toneClass = tone === "green" ? "border-leaf/25 bg-leaf-soft" : tone === "orange" ? "border-coral/25 bg-[#fff0eb]" : "border-line bg-white";
  return <div className={`rounded-md border p-3 ${toneClass}`}><div className="text-xs font-bold text-muted">{label}</div><div className="mt-1 text-xl font-black text-ink">{value}</div></div>;
}

function EmptyState({ mode }) {
  return <div className="border-y border-line bg-white px-5 py-12 text-center"><Search className="mx-auto mb-3 text-muted"/><p className="font-bold">調整條件後開始推薦</p><p className="mt-1 text-sm text-muted">系統會在這裡優先顯示{mode === "restaurant" ? "餐廳" : "食譜"}清單。</p></div>;
}

function SaveButton({ saved, onClick }) {
  return <button onClick={onClick} title={saved ? "取消收藏" : "加入收藏"} className={`focus-ring grid size-9 place-items-center rounded-md border ${saved ? "border-coral bg-[#fff0eb] text-coral" : "border-line bg-white text-muted"}`}><Heart size={17} fill={saved ? "currentColor" : "none"}/></button>;
}

function RestaurantCard({ row, rank, saved, onSave, canSave }) {
  return <article className="rounded-md border border-line bg-white p-4 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><div className="text-xs font-black text-coral">推薦 #{rank}</div><h3 className="mt-1 text-xl font-black">{row.name}</h3><p className="mt-1 text-sm text-muted">{row.category} · {row.serve_speed}速出餐 · {row.takeout === "yes" ? "可外帶" : "適合內用"}</p></div>
      <div className="flex items-start gap-3"><SaveButton saved={saved} onClick={onSave}/><div className="text-right"><div className="text-2xl font-black text-coral">{row.final_score ?? row.score}</div><div className="text-xs font-bold text-muted">最終分數</div></div></div>
    </div>
    <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Metric label="價格" value={`${row.price} 元`} />
      <Metric label="距離" value={`${row.distance} 分鐘`} />
      <Metric label="評分" value={row.rating} tone="green" />
      <Metric label="負評比例" value={`${row.negative_ratio ?? 0}%`} tone={(row.negative_ratio ?? 0) > 35 ? "orange" : "green"} />
    </div>
    <p className="mt-4 border-l-4 border-leaf bg-leaf-soft px-3 py-2 text-sm leading-6">{row.reason}</p>
    <details className="mt-3 border-t border-line pt-3 text-sm"><summary className="flex cursor-pointer items-center gap-2 font-bold"><ChevronDown size={16}/>評論與分數細節</summary><div className="mt-3 grid gap-2 text-muted"><p>{row.review_summary || "目前沒有評論摘要"}</p><p>評論風險：{row.review_risk || "--"} · 情境調整：{row.intent_adjustment ?? 0}</p></div></details>
  </article>;
}

function RecipeCard({ row, rank, saved, onSave, canSave }) {
  return <article className="rounded-md border border-line bg-white p-4 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><div className="text-xs font-black text-leaf">推薦 #{rank}</div><h3 className="mt-1 text-xl font-black">{row.name}</h3><p className="mt-1 text-sm text-muted">{row.category} · {row.difficulty} · {row.time} 分鐘</p></div>
      <div className="flex items-start gap-3"><SaveButton saved={saved} onClick={onSave}/><div className="text-right"><div className="text-2xl font-black text-leaf">{row.final_score}</div><div className="text-xs font-bold text-muted">混合分數</div></div></div>
    </div>
    <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Metric label="召回相似度" value={`${row.recall_score}%`} />
      <Metric label="熱量" value={`${row.calories} kcal`} />
      <Metric label="缺少食材" value={`${row.missing_count} 項`} tone={row.missing_count === 0 ? "green" : "orange"} />
      <Metric label="保存加權" value={`+${row.priority_bonus || 0}`} tone="green" />
    </div>
    <p className="mt-4 border-l-4 border-coral bg-[#fff0eb] px-3 py-2 text-sm leading-6">{row.reason}</p>
    <details className="mt-3 border-t border-line pt-3 text-sm"><summary className="flex cursor-pointer items-center gap-2 font-bold"><CookingPot size={16}/>料理步驟與可信來源</summary><ol className="mt-3 grid gap-2 pl-5 text-muted">{(row.steps || []).map((step, index) => <li className="list-decimal" key={index}>{step}</li>)}</ol><p className="mt-3 text-xs text-muted">{row.knowledge_id} · {row.source_name} · 審核 {row.verified_date}</p></details>
  </article>;
}

function AuthModal({ mode, setMode, form, setForm, error, busy, onSubmit, onClose }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/55 p-4" role="dialog" aria-modal="true">
    <div className="w-full max-w-md rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between"><div><p className="text-sm font-black text-coral">個人帳號</p><h2 className="text-2xl font-black">{mode === "login" ? "登入系統" : "建立帳號"}</h2></div><button onClick={onClose} title="關閉" className="grid size-9 place-items-center rounded-md border border-line"><X size={18}/></button></div>
      <form className="mt-5 grid gap-4" onSubmit={onSubmit}>
        {mode === "register" && <Field label="顯示名稱"><input required minLength="2" className="focus-ring h-11 rounded-md border border-line px-3" value={form.display_name} onChange={(e)=>setForm({...form,display_name:e.target.value})}/></Field>}
        <Field label="Email"><input required type="email" className="focus-ring h-11 rounded-md border border-line px-3" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})}/></Field>
        <Field label="密碼" hint="至少 8 個字元"><input required minLength="8" type="password" className="focus-ring h-11 rounded-md border border-line px-3" value={form.password} onChange={(e)=>setForm({...form,password:e.target.value})}/></Field>
        {error && <p className="rounded-md bg-[#fff0eb] p-3 text-sm text-coral-dark">{error}</p>}
        <button disabled={busy} className="flex h-11 items-center justify-center gap-2 rounded-md bg-coral font-black text-white">{mode === "login" ? <LogIn size={18}/> : <UserPlus size={18}/>} {busy ? "處理中..." : mode === "login" ? "登入" : "註冊"}</button>
      </form>
      <button onClick={()=>setMode(mode === "login" ? "register" : "login")} className="mt-4 w-full text-sm font-bold text-leaf">{mode === "login" ? "還沒有帳號？建立一個" : "已經有帳號？直接登入"}</button>
    </div>
  </div>;
}

function EmotionModal({ onApply, onClose }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let activeStream;
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: "user", width: 640, height: 480 }, audio: false })
      .then((mediaStream) => {
        activeStream = mediaStream; setStream(mediaStream);
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
      })
      .catch(() => setError("無法開啟攝影機，請允許瀏覽器相機權限。"));
    return () => activeStream?.getTracks().forEach((track) => track.stop());
  }, []);

  function close() { stream?.getTracks().forEach((track) => track.stop()); onClose(); }

  async function capture() {
    if (!videoRef.current || !canvasRef.current) return;
    setBusy(true); setError("");
    const video = videoRef.current, canvas = canvasRef.current;
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", .88));
    try { setResult(await api.analyzeEmotion(blob)); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/65 p-4" role="dialog" aria-modal="true">
    <div className="w-full max-w-2xl rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between"><div><p className="text-sm font-black text-leaf">OpenCV 表情辨識</p><h2 className="text-2xl font-black">拍一張現在的表情</h2><p className="mt-1 text-sm text-muted">照片只用於本次分析，不會儲存。結果仍可手動修改。</p></div><button onClick={close} title="關閉" className="grid size-9 place-items-center rounded-md border border-line"><X size={18}/></button></div>
      <div className="mt-4 overflow-hidden rounded-md bg-black"><video ref={videoRef} autoPlay playsInline muted className="aspect-video w-full object-cover"/></div>
      <canvas ref={canvasRef} className="hidden"/>
      {error && <p className="mt-3 rounded-md bg-[#fff0eb] p-3 text-sm text-coral-dark">{error}</p>}
      {result && <div className="mt-3 rounded-md border border-leaf/25 bg-leaf-soft p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-sm font-bold text-muted">辨識結果</div><div className="text-2xl font-black">{result.expression_label} · {(result.confidence * 100).toFixed(0)}%</div><p className="mt-1 text-sm text-muted">建議套用心情：{result.recommended_mood}</p></div><button onClick={()=>{onApply(result);close();}} className="h-10 rounded-md bg-leaf px-4 font-black text-white">套用到推薦</button></div><p className="mt-3 text-xs text-muted">{result.notice}</p></div>}
      <button onClick={capture} disabled={busy || !stream} className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-md bg-coral font-black text-white"><Camera size={18}/>{busy ? "分析中..." : "拍照並分析"}</button>
    </div>
  </div>;
}

function App() {
  const [mode, setMode] = useState("restaurant");
  const [options, setOptions] = useState(null);
  const [restaurantForm, setRestaurantForm] = useState(restaurantDefaults);
  const [recipeForm, setRecipeForm] = useState(recipeDefaults);
  const [restaurantData, setRestaurantData] = useState(null);
  const [recipeData, setRecipeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ display_name: "", email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [emotionOpen, setEmotionOpen] = useState(false);
  const [emotionResult, setEmotionResult] = useState(null);

  useEffect(() => { api.options().then(setOptions).catch((err) => setError(err.message)); }, []);
  useEffect(() => { api.me().then(({user}) => { setUser(user); return api.favorites(); }).then(({favorites}) => setFavorites(favorites)).catch(() => {}); }, []);

  const results = mode === "restaurant" ? restaurantData?.results : recipeData?.results;
  const top = results?.[0];
  const wasteSaved = useMemo(() => (recipeData?.priorities || []).filter((x) => x.level === "高").reduce((sum, x) => sum + Number(x.price || 0), 0), [recipeData]);

  const updateRestaurant = (key, value) => setRestaurantForm((form) => ({ ...form, [key]: value }));
  const updateRecipe = (key, value) => setRecipeForm((form) => ({ ...form, [key]: value }));

  function selectRestaurantScenario(value) {
    setRestaurantForm((form) => ({ ...form, scenario: value, ...(quickScenarioValues[value] || {}) }));
  }

  async function locate() {
    if (!navigator.geolocation) return setError("瀏覽器不支援定位");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setRestaurantForm((form) => ({ ...form, latitude: coords.latitude, longitude: coords.longitude })),
      () => setError("無法取得定位，請檢查瀏覽器權限"),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  async function submit() {
    setLoading(true); setError("");
    try {
      if (mode === "restaurant") setRestaurantData(await api.restaurants(restaurantForm));
      else setRecipeData(await api.recipes(recipeForm));
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  function addIngredient() {
    const name = window.prompt("輸入食材名稱");
    if (name?.trim()) setRecipeForm((form) => ({ ...form, ingredients: [...form.ingredients, { name: name.trim(), days_stored: 1, shelf_life: 7, price: 40, perishability: "中" }] }));
  }

  function updateIngredient(index, key, value) {
    setRecipeForm((form) => ({ ...form, ingredients: form.ingredients.map((item, i) => i === index ? { ...item, [key]: value } : item) }));
  }

  async function submitAuth(event) {
    event.preventDefault(); setAuthBusy(true); setAuthError("");
    try {
      const response = authMode === "login" ? await api.login(authForm) : await api.register(authForm);
      setUser(response.user); setAuthOpen(false); setAuthForm({ display_name: "", email: "", password: "" });
      setFavorites((await api.favorites()).favorites);
    } catch (err) { setAuthError(err.message); }
    finally { setAuthBusy(false); }
  }

  async function logout() {
    await api.logout(); setUser(null); setFavorites([]);
  }

  function isSaved(kind, name) { return favorites.some((item) => item.kind === kind && item.item_name === name); }

  async function toggleFavorite(kind, name) {
    if (!user) { setAuthOpen(true); return; }
    if (isSaved(kind, name)) await api.removeFavorite(kind, name); else await api.addFavorite(kind, name);
    setFavorites((await api.favorites()).favorites);
  }

  return <div className="min-h-screen bg-canvas">
    <header className="sticky top-0 z-30 border-b border-line bg-canvas/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3"><div className="grid size-9 place-items-center rounded-md bg-coral text-white"><Utensils size={20}/></div><div><div className="font-black">智慧飲食決策</div><div className="text-xs text-muted">外食避雷 · 內食減浪費</div></div></div>
        {user ? <div className="flex items-center gap-2"><div className="hidden text-right sm:block"><div className="text-sm font-black">{user.display_name}</div><div className="text-xs text-muted">收藏 {favorites.length} 筆</div></div><button onClick={logout} title="登出" className="focus-ring grid size-10 place-items-center rounded-md border border-line bg-white"><LogOut size={17}/></button></div> : <button onClick={()=>setAuthOpen(true)} className="focus-ring flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-bold"><LogIn size={17}/>登入</button>}
      </div>
    </header>

    <main className="mx-auto max-w-[1440px] px-4 pb-16 sm:px-6">
      <section className="hero-photo mt-5 min-h-48 rounded-md p-5 text-white sm:p-7">
        <div className="max-w-2xl"><p className="text-sm font-black text-[#ffd7c8]">今天吃什麼，交給資料決定</p><h1 className="mt-2 text-3xl font-black sm:text-4xl">先看答案，再決定要不要研究模型</h1><p className="mt-3 max-w-xl text-sm leading-6 text-white/85">條件送出後，推薦清單會直接出現在前面；評論分析、保存排程與模型細節保留在後段。</p></div>
      </section>

      <div className="mt-5 inline-grid grid-cols-2 rounded-md border border-line bg-white p-1">
        <button onClick={() => setMode("restaurant")} className={`flex min-h-10 items-center gap-2 rounded px-4 text-sm font-black ${mode === "restaurant" ? "bg-coral text-white" : "text-muted"}`}><MapPin size={17}/>我要外食</button>
        <button onClick={() => setMode("recipe")} className={`flex min-h-10 items-center gap-2 rounded px-4 text-sm font-black ${mode === "recipe" ? "bg-leaf text-white" : "text-muted"}`}><ChefHat size={17}/>我要自己煮</button>
      </div>

      <div className="mt-4 grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="self-start rounded-md border border-line bg-white p-4 lg:sticky lg:top-20">
          <div className="mb-4 flex items-center gap-2"><SlidersIcon/><h2 className="text-lg font-black">{mode === "restaurant" ? "外食條件" : "冰箱條件"}</h2></div>
          {mode === "restaurant" ? <div className="grid gap-4">
            <Field label="快速情境"><Select value={restaurantForm.scenario} onChange={(e) => selectRestaurantScenario(e.target.value)}>{(options?.restaurants.scenarios || []).map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <Field label={`預算上限 ${restaurantForm.budget} 元`}><input className="range" type="range" min="50" max="300" step="5" value={restaurantForm.budget} onChange={(e) => updateRestaurant("budget", Number(e.target.value))}/></Field>
            <Field label={`可接受距離 ${restaurantForm.max_distance} 分鐘`}><input className="range" type="range" min="1" max="20" value={restaurantForm.max_distance} onChange={(e) => updateRestaurant("max_distance", Number(e.target.value))}/></Field>
            <Field label="餐點類型"><Select value={restaurantForm.category} onChange={(e) => updateRestaurant("category", e.target.value)}><option>不限</option>{(options?.restaurants.categories || []).map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <Field label="目前心情"><Select value={restaurantForm.mood} onChange={(e) => updateRestaurant("mood", e.target.value)}>{["省錢","疲累","開心","心情不好","選擇困難"].map((x) => <option key={x}>{x}</option>)}</Select>{emotionResult && <span className="text-xs font-bold text-leaf">OpenCV：{emotionResult.expression_label}，已套用「{emotionResult.recommended_mood}」</span>}</Field>
            <button onClick={()=>setEmotionOpen(true)} className="focus-ring flex h-10 items-center justify-center gap-2 rounded-md border border-leaf/30 bg-leaf-soft text-sm font-black text-leaf"><Camera size={17}/>用表情帶入心情</button>
            <button onClick={locate} className="focus-ring flex h-10 items-center justify-center gap-2 rounded-md border border-line bg-white text-sm font-bold"><LocateFixed size={17}/>{restaurantForm.latitude ? "定位已套用" : "使用目前位置"}</button>
            <details className="border-t border-line pt-3"><summary className="cursor-pointer text-sm font-black">進階條件</summary><div className="mt-3 grid gap-3">
              <Field label="目前天氣"><Select value={restaurantForm.weather} onChange={(e) => updateRestaurant("weather", e.target.value)}>{["普通","熱","冷","雨天"].map((x) => <option key={x}>{x}</option>)}</Select></Field>
              <Field label="用餐時段"><Select value={restaurantForm.meal_time} onChange={(e) => updateRestaurant("meal_time", e.target.value)}>{["早餐","午餐","下午茶","晚餐","宵夜"].map((x) => <option key={x}>{x}</option>)}</Select></Field>
              <Field label="最低評分"><input className="focus-ring h-10 rounded-md border border-line px-3" type="number" min="0" max="5" step="0.1" value={restaurantForm.min_rating} onChange={(e) => updateRestaurant("min_rating", Number(e.target.value))}/></Field>
              <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={restaurantForm.prefer_fast} onChange={(e) => updateRestaurant("prefer_fast", e.target.checked)}/>希望快速出餐</label>
            </div></details>
          </div> : <div className="grid gap-4">
            <Field label="快速情境"><Select value={recipeForm.scenario} onChange={(e) => updateRecipe("scenario", e.target.value)}>{(options?.recipes.scenarios || []).map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <div><div className="mb-2 flex items-center justify-between"><span className="text-sm font-black">冰箱食材</span><button className="text-sm font-black text-leaf" onClick={addIngredient}>＋ 新增</button></div><div className="grid gap-2">{recipeForm.ingredients.map((item, index) => <div className="rounded-md border border-line p-2" key={`${item.name}-${index}`}><div className="font-bold">{item.name}</div><div className="mt-2 grid grid-cols-2 gap-2"><input title="已放天數" className="h-9 rounded border border-line px-2 text-sm" type="number" value={item.days_stored} onChange={(e) => updateIngredient(index,"days_stored",Number(e.target.value))}/><input title="保存期限" className="h-9 rounded border border-line px-2 text-sm" type="number" value={item.shelf_life} onChange={(e) => updateIngredient(index,"shelf_life",Number(e.target.value))}/></div></div>)}</div></div>
            <Field label={`料理時間 ${recipeForm.max_time} 分鐘`}><input className="range" type="range" min="5" max="60" step="5" value={recipeForm.max_time} onChange={(e) => updateRecipe("max_time",Number(e.target.value))}/></Field>
            <Field label={`熱量上限 ${recipeForm.max_calories} kcal`}><input className="range" type="range" min="150" max="900" step="50" value={recipeForm.max_calories} onChange={(e) => updateRecipe("max_calories",Number(e.target.value))}/></Field>
            <Field label="最多缺少食材"><Select value={recipeForm.max_missing} onChange={(e) => updateRecipe("max_missing",Number(e.target.value))}>{[0,1,2,3,4,5].map((x) => <option key={x}>{x}</option>)}</Select></Field>
          </div>}
          <button onClick={submit} disabled={loading} className="focus-ring mt-5 flex h-11 w-full items-center justify-center gap-2 rounded-md bg-coral font-black text-white hover:bg-coral-dark"><Sparkles size={18}/>{loading ? "計算中..." : "開始智慧推薦"}</button>
          {error && <p className="mt-3 flex gap-2 rounded-md bg-[#fff0eb] p-3 text-sm text-coral-dark"><AlertTriangle size={18}/>{error}</p>}
        </aside>

        <section className="min-w-0">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="text-sm font-black text-leaf">推薦結果</p><h2 className="text-2xl font-black">{top ? `今天優先選 ${top.name}` : "送出條件後立即看答案"}</h2></div>{top && <div className="flex gap-2 text-sm font-bold text-muted"><ShieldCheck size={18} className="text-leaf"/>{results.length} 筆符合條件</div>}</div>

          {top && <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Metric label="第一名" value={top.name}/>
            <Metric label="最高分數" value={top.final_score ?? top.score} tone="green"/>
            <Metric label={mode === "restaurant" ? "評論風險" : "高風險食材"} value={mode === "restaurant" ? (top.review_risk || "--") : `${(recipeData?.priorities || []).filter((x) => x.level === "高").length} 項`} tone="orange"/>
            <Metric label={mode === "restaurant" ? "平均價格" : "預估避免浪費"} value={mode === "restaurant" ? `${Math.round(results.reduce((s,x)=>s+x.price,0)/results.length)} 元` : `${wasteSaved} 元`}/>
          </div>}

          {!results ? <EmptyState mode={mode}/> : results.length === 0 ? <div className="rounded-md border border-coral/30 bg-[#fff0eb] p-5"><h3 className="font-black">目前條件沒有結果</h3><p className="mt-1 text-sm text-muted">放寬距離、評分或可缺少食材數後再試一次。</p></div> : <div className="grid gap-3">{results.map((row,index) => mode === "restaurant" ? <RestaurantCard key={row.name} row={row} rank={index+1} saved={isSaved("restaurant",row.name)} canSave={Boolean(user)} onSave={()=>toggleFavorite("restaurant",row.name)}/> : <RecipeCard key={row.name} row={row} rank={index+1} saved={isSaved("recipe",row.name)} canSave={Boolean(user)} onSave={()=>toggleFavorite("recipe",row.name)}/>)}</div>}

          {results && <details className="mt-5 rounded-md border border-line bg-white p-4"><summary className="flex cursor-pointer items-center gap-2 font-black"><BarChart3 size={18}/>進階分析與模型資訊</summary><div className="mt-4 grid gap-3 sm:grid-cols-3"><Metric label="候選結果" value={mode === "restaurant" ? restaurantData?.meta?.candidate_count : recipeData?.meta?.result_count}/><Metric label="排序策略" value={mode === "restaurant" ? restaurantForm.smart_mode : "混合式推薦"}/><Metric label="可信內容覆蓋" value={mode === "recipe" ? `${results.filter((x)=>x.knowledge_status === "已檢索可信內容").length}/${results.length}` : "評論分析啟用"}/></div></details>}
        </section>
      </div>
    </main>
    {authOpen && <AuthModal mode={authMode} setMode={setAuthMode} form={authForm} setForm={setAuthForm} error={authError} busy={authBusy} onSubmit={submitAuth} onClose={()=>setAuthOpen(false)}/>} 
    {emotionOpen && <EmotionModal onClose={()=>setEmotionOpen(false)} onApply={(result)=>{setEmotionResult(result);updateRestaurant("mood",result.recommended_mood);}}/>}
  </div>;
}

function SlidersIcon() { return <span className="grid size-8 place-items-center rounded-md bg-[#fff0eb] text-coral"><BarChart3 size={17}/></span>; }

export default App;
