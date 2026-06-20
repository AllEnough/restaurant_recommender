import { useEffect, useMemo, useRef, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
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

const recipeScenarioValues = {
  "宅家不出門": {
    smart_mode: "我不想出門", max_time: 25, max_calories: 800, max_missing: 0, only_cookable: true,
    ingredients: [
      { name: "雞蛋", days_stored: 5, shelf_life: 14, price: 60, perishability: "中" },
      { name: "白飯", days_stored: 1, shelf_life: 3, price: 20, perishability: "中" },
      { name: "蔥", days_stored: 3, shelf_life: 7, price: 25, perishability: "高" },
      { name: "醬油", days_stored: 30, shelf_life: 180, price: 70, perishability: "低" },
    ],
  },
  "清冰箱減浪費": { ...recipeDefaults, ingredients: recipeDefaults.ingredients.map((item) => ({ ...item })) },
  "健身低熱量": {
    smart_mode: "低熱量", max_time: 35, difficulty: "簡單", max_calories: 500, max_missing: 1, only_cookable: false,
    ingredients: [
      { name: "雞胸肉", days_stored: 2, shelf_life: 3, price: 95, perishability: "高" },
      { name: "生菜", days_stored: 3, shelf_life: 5, price: 55, perishability: "高" },
      { name: "玉米", days_stored: 2, shelf_life: 5, price: 35, perishability: "中" },
      { name: "番茄", days_stored: 4, shelf_life: 6, price: 45, perishability: "高" },
      { name: "地瓜", days_stored: 5, shelf_life: 14, price: 45, perishability: "中" },
    ],
  },
  "手動自訂": { smart_mode: "自訂" },
};

function detectMealTime(date = new Date()) {
  const hour = date.getHours();
  if (hour >= 5 && hour < 11) return "早餐";
  if (hour >= 11 && hour < 14) return "午餐";
  if (hour >= 14 && hour < 17) return "下午茶";
  if (hour >= 17 && hour < 22) return "晚餐";
  return "宵夜";
}

function Field({ label, children, hint }) {
  return <label className="grid min-w-0 gap-1.5 text-sm font-bold text-ink">{label}{children}{hint && <span className="text-xs font-normal text-muted">{hint}</span>}</label>;
}

function Select({ value, onChange, children }) {
  return <select className="focus-ring h-10 w-full min-w-0 rounded-md border border-line bg-white px-3 font-medium" value={value} onChange={onChange}>{children}</select>;
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

function FitMapBounds({ points }) {
  const map = useMap();
  const signature = points.map((point) => point.join(",")).join("|");
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 16);
    else if (points.length > 1) map.fitBounds(points, { padding: [36, 36], maxZoom: 16 });
  }, [map, signature]);
  return null;
}

function RestaurantMap({ rows, latitude, longitude }) {
  const restaurants = rows.filter((row) => Number.isFinite(Number(row.latitude)) && Number.isFinite(Number(row.longitude)));
  if (!restaurants.length) return null;

  const restaurantPoints = restaurants.map((row) => [Number(row.latitude), Number(row.longitude)]);
  const hasUserLocation = latitude !== null && longitude !== null && Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude));
  const userPoint = hasUserLocation ? [Number(latitude), Number(longitude)] : null;
  const allPoints = userPoint ? [...restaurantPoints, userPoint] : restaurantPoints;

  function markerColor(row, index) {
    if (index === 0) return "#dc5a3a";
    if (Number(row.cp_score) >= 80) return "#247a52";
    if (Number(row.cp_score) >= 65) return "#e9ad35";
    return "#3978b7";
  }

  return <section className="mt-5 overflow-hidden rounded-md border border-line bg-white">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
      <div><div className="flex items-center gap-2 font-black"><MapPin size={18}/>推薦餐廳互動地圖</div><p className="mt-1 text-sm text-muted">點選圖針查看推薦分數、距離與 CP 值。</p></div>
      <div className="flex flex-wrap gap-3 text-xs font-bold text-muted"><span><i className="map-legend bg-coral"/>第一名</span><span><i className="map-legend bg-leaf"/>高 CP</span><span><i className="map-legend bg-sun"/>中 CP</span><span><i className="map-legend bg-[#3978b7]"/>一般</span>{userPoint && <span><i className="map-legend bg-[#7048a8]"/>你的位置</span>}</div>
    </div>
    <MapContainer className="restaurant-map" center={restaurantPoints[0]} zoom={15} scrollWheelZoom={false}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      <FitMapBounds points={allPoints}/>
      {restaurants.map((row, index) => {
        const color = markerColor(row, index);
        return <CircleMarker key={row.name} center={[Number(row.latitude), Number(row.longitude)]} radius={index === 0 ? 13 : 10} pathOptions={{ color: "#fff", weight: 3, fillColor: color, fillOpacity: .96 }}>
          <Tooltip permanent direction="center" className="rank-tooltip">{index + 1}</Tooltip>
          <Popup minWidth={220}><div className="map-popup"><strong>{row.name}</strong><span>{row.category} · {row.price} 元</span><span>評分 {row.rating} · 距離 {row.distance} 分鐘</span><span>CP 值 {row.cp_score} · 推薦 {row.final_score ?? row.score}</span><a href={`https://www.google.com/maps/search/?api=1&query=${row.latitude},${row.longitude}`} target="_blank" rel="noreferrer">在 Google Maps 開啟</a></div></Popup>
        </CircleMarker>;
      })}
      {userPoint && <CircleMarker center={userPoint} radius={9} pathOptions={{ color: "#fff", weight: 3, fillColor: "#7048a8", fillOpacity: 1 }}><Popup>你目前的位置</Popup></CircleMarker>}
    </MapContainer>
  </section>;
}

function RankChange({ value }) {
  const number = Number(value || 0);
  const color = number > 0 ? "text-leaf" : number < 0 ? "text-coral" : "text-muted";
  return <span className={`font-black ${color}`}>{number > 0 ? `↑ ${number}` : number < 0 ? `↓ ${Math.abs(number)}` : "－"}</span>;
}

function ScoreBar({ label, value, max = 135, tone = "coral" }) {
  const width = Math.max(0, Math.min(Number(value || 0) / max * 100, 100));
  return <div className="grid grid-cols-[88px_minmax(0,1fr)_44px] items-center gap-2 text-xs">
    <span className="font-bold text-muted">{label}</span>
    <div className="h-2 overflow-hidden rounded bg-[#ece9e1]"><div className={`h-full ${tone === "green" ? "bg-leaf" : tone === "muted" ? "bg-sun" : "bg-coral"}`} style={{ width: `${width}%` }}/></div>
    <span className="text-right font-black">{value}</span>
  </div>;
}

function RestaurantAdvanced({ data }) {
  const analysis = data?.analysis;
  if (!analysis) return null;
  const dashboard = analysis.dashboard || {};
  const evaluation = analysis.evaluation || {};
  return <div className="mt-5 grid gap-6">
    <section>
      <h3 className="text-base font-black">外食決策 Dashboard</h3>
      <p className="mt-1 text-sm text-muted">整理目前候選池、評論風險與增強模型輸出。</p>
      <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Metric label="通過條件候選" value={dashboard.candidate_count ?? 0}/>
        <Metric label="Top 平均最終分" value={dashboard.average_final_score ?? 0} tone="green"/>
        <Metric label="Top 平均負評" value={`${dashboard.average_negative_ratio ?? 0}%`} tone="orange"/>
        <Metric label="低風險餐廳" value={`${dashboard.low_risk_count ?? 0} 間`} tone="green"/>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-sm">{Object.entries(analysis.risk_distribution || {}).map(([risk,count]) => <span key={risk} className="rounded border border-line bg-canvas px-3 py-1.5 font-bold">{risk}風險 {count}</span>)}</div>
    </section>

    <section className="border-t border-line pt-5">
      <h3 className="text-base font-black">模型評估：基礎排序 vs 評論與情境增強</h3>
      <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Metric label="Top 清單重疊率" value={`${evaluation.top_overlap ?? 0}%`}/>
        <Metric label="基礎平均負評" value={`${evaluation.baseline_average_negative ?? 0}%`}/>
        <Metric label="增強後平均負評" value={`${evaluation.enhanced_average_negative ?? 0}%`} tone="green"/>
        <Metric label="第一名是否改變" value={evaluation.first_changed ? "有改變" : "維持一致"} tone={evaluation.first_changed ? "orange" : "green"}/>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="analysis-table"><thead><tr><th>餐廳</th><th>基礎排名</th><th>增強排名</th><th>名次變化</th><th>基礎分</th><th>最終分</th><th>負評</th></tr></thead><tbody>{(evaluation.comparison || []).map((row) => <tr key={row.name}><td className="font-bold">{row.name}</td><td>{row.baseline_rank ?? "－"}</td><td>{row.enhanced_rank ?? "－"}</td><td><RankChange value={row.rank_change}/></td><td>{row.base_score}</td><td className="font-black text-coral">{row.final_score}</td><td>{row.negative_ratio}%</td></tr>)}</tbody></table>
      </div>
    </section>

    <section className="border-t border-line pt-5">
      <h3 className="text-base font-black">推薦分數拆解</h3>
      <div className="mt-3 grid gap-4 lg:grid-cols-2">{(analysis.score_breakdown || []).map((row) => <div key={row.name} className="border-b border-line pb-4">
        <div className="mb-2 flex items-center justify-between"><span className="font-black">{row.name}</span><span className="text-lg font-black text-coral">{row.final_score}</span></div>
        <div className="grid gap-2"><ScoreBar label="基礎分數" value={row.base_score}/><ScoreBar label="評論調整" value={row.review_adjustment} max={18} tone="green"/><ScoreBar label="情境調整" value={row.intent_adjustment} max={18} tone="muted"/></div>
      </div>)}</div>
    </section>

    <section className="border-t border-line pt-5">
      <h3 className="text-base font-black">權重敏感度分析</h3>
      <p className="mt-1 text-sm text-muted">使用相同候選池，觀察不同決策目標下的第一名。</p>
      <div className="mt-3 overflow-x-auto"><table className="analysis-table"><thead><tr><th>排序策略</th><th>第一名</th><th>指標值</th></tr></thead><tbody>{(analysis.sensitivity || []).map((row) => <tr key={row.strategy}><td>{row.strategy}</td><td className="font-black">{row.winner}</td><td>{row.value}</td></tr>)}</tbody></table></div>
    </section>
  </div>;
}

function RecipeAdvanced({ data }) {
  const analysis = data?.analysis;
  if (!analysis) return null;
  const dashboard = analysis.dashboard || {};
  const evaluation = analysis.evaluation || {};
  const coverage = analysis.knowledge_coverage || {};
  return <div className="mt-5 grid gap-6">
    <section>
      <h3 className="text-base font-black">內食決策 Dashboard</h3>
      <p className="mt-1 text-sm text-muted">同時檢查可料理性、缺料與保存加權。</p>
      <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Metric label="通過條件候選" value={dashboard.candidate_count ?? 0}/>
        <Metric label="可直接料理" value={`${dashboard.cookable_count ?? 0} 道`} tone="green"/>
        <Metric label="Top 平均缺料" value={`${dashboard.average_missing_count ?? 0} 項`} tone="orange"/>
        <Metric label="平均保存加權" value={`+${dashboard.average_priority_bonus ?? 0}`} tone="green"/>
      </div>
    </section>

    <section className="border-t border-line pt-5">
      <h3 className="text-base font-black">食材標準化與保存優先順序</h3>
      <div className="mt-3 overflow-x-auto"><table className="analysis-table"><thead><tr><th>食材</th><th>優先分數</th><th>剩餘天數</th><th>排程比值</th><th>風險級別</th><th>估計價格</th></tr></thead><tbody>{(analysis.priorities || []).map((row) => <tr key={row.ingredient}><td className="font-black">{row.ingredient}</td><td>{row.priority_score}</td><td>{row.remaining_days}</td><td>{row.scheduling_ratio}</td><td><span className={`font-black ${row.level === "高" ? "text-coral" : row.level === "中" ? "text-sun" : "text-leaf"}`}>{row.level}</span></td><td>{row.price} 元</td></tr>)}</tbody></table></div>
      <div className="mt-3 flex flex-wrap gap-2 text-sm">{(analysis.normalization || []).map((row,index) => <span key={`${row.original}-${index}`} className="rounded border border-line bg-canvas px-3 py-1.5"><b>{row.original}</b>{row.changed ? ` → ${row.normalized}` : "（已標準化）"}</span>)}</div>
    </section>

    <section className="border-t border-line pt-5">
      <h3 className="text-base font-black">模型評估：基礎排序 vs 保存優先級</h3>
      <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <Metric label="Top 清單重疊率" value={`${evaluation.top_overlap ?? 0}%`}/>
        <Metric label="基礎平均缺料" value={`${evaluation.baseline_average_missing ?? 0} 項`}/>
        <Metric label="增強後平均缺料" value={`${evaluation.enhanced_average_missing ?? 0} 項`} tone="green"/>
        <Metric label="高優先食材命中" value={`${evaluation.high_priority_usage ?? 0} 道`} tone="orange"/>
      </div>
      <div className="mt-4 overflow-x-auto"><table className="analysis-table"><thead><tr><th>食譜</th><th>基礎排名</th><th>增強排名</th><th>名次變化</th><th>基礎分</th><th>最終分</th><th>缺料</th></tr></thead><tbody>{(evaluation.comparison || []).map((row) => <tr key={row.name}><td className="font-bold">{row.name}</td><td>{row.baseline_rank ?? "－"}</td><td>{row.enhanced_rank ?? "－"}</td><td><RankChange value={row.rank_change}/></td><td>{row.base_score}</td><td className="font-black text-leaf">{row.final_score}</td><td>{row.missing_count}</td></tr>)}</tbody></table></div>
    </section>

    <section className="border-t border-line pt-5">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-base font-black">食譜分數拆解</h3><span className="text-sm font-bold text-leaf">可信內容 {coverage.covered ?? 0}/{coverage.total ?? 0}</span></div>
      <div className="mt-3 grid gap-4 lg:grid-cols-2">{(analysis.score_breakdown || []).map((row) => <div key={row.name} className="border-b border-line pb-4">
        <div className="mb-2 flex items-center justify-between"><span className="font-black">{row.name}</span><span className="text-lg font-black text-leaf">{row.final_score}</span></div>
        <div className="grid gap-2"><ScoreBar label="食材符合" value={row.ingredient_score} max={50} tone="green"/><ScoreBar label="料理時間" value={row.time_score} max={20}/><ScoreBar label="料理難度" value={row.difficulty_score} max={20} tone="muted"/><ScoreBar label="熱量" value={row.calorie_score} max={10} tone="green"/><ScoreBar label="缺料扣分" value={row.missing_penalty} max={20}/><ScoreBar label="保存加權" value={row.priority_bonus} max={25} tone="green"/></div>
      </div>)}</div>
    </section>
  </div>;
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

function FavoritesModal({ favorites, onRemove, onClose }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/55 p-4" role="dialog" aria-modal="true">
    <div className="w-full max-w-lg rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between"><div><p className="text-sm font-black text-coral">個人收藏</p><h2 className="text-2xl font-black">已收藏 {favorites.length} 筆</h2></div><button onClick={onClose} title="關閉" className="grid size-9 place-items-center rounded-md border border-line"><X size={18}/></button></div>
      {favorites.length === 0 ? <div className="py-10 text-center text-muted"><Heart className="mx-auto mb-3"/><p className="font-bold">還沒有收藏餐廳或食譜</p></div> : <div className="mt-5 max-h-[55vh] overflow-y-auto border-y border-line">{favorites.map((item) => <div key={`${item.kind}-${item.item_name}`} className="flex items-center justify-between gap-3 border-b border-line px-1 py-3 last:border-b-0"><div><span className={`text-xs font-black ${item.kind === "restaurant" ? "text-coral" : "text-leaf"}`}>{item.kind === "restaurant" ? "餐廳" : "食譜"}</span><div className="font-black">{item.item_name}</div></div><button onClick={()=>onRemove(item.kind,item.item_name)} className="rounded-md border border-line px-3 py-2 text-sm font-bold text-coral">移除</button></div>)}</div>}
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
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [emotionOpen, setEmotionOpen] = useState(false);
  const [emotionResult, setEmotionResult] = useState(null);
  const [analysisOpen, setAnalysisOpen] = useState(true);
  const [weatherInfo, setWeatherInfo] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [newIngredient, setNewIngredient] = useState("");

  useEffect(() => { api.options().then(setOptions).catch((err) => setError(err.message)); }, []);
  useEffect(() => { api.me().then(({user}) => { setUser(user); return api.favorites(); }).then(({favorites}) => setFavorites(favorites)).catch(() => {}); }, []);
  useEffect(() => {
    setRestaurantForm((form) => ({ ...form, meal_time: detectMealTime() }));
    refreshWeather("Xitun District, Taichung, Taiwan");
  }, []);

  const results = mode === "restaurant" ? restaurantData?.results : recipeData?.results;
  const top = results?.[0];
  const wasteSaved = useMemo(() => (recipeData?.priorities || []).filter((x) => x.level === "高").reduce((sum, x) => sum + Number(x.price || 0), 0), [recipeData]);

  const updateRestaurant = (key, value) => setRestaurantForm((form) => ({ ...form, [key]: value }));
  const updateRecipe = (key, value) => setRecipeForm((form) => ({ ...form, [key]: value }));

  function selectRestaurantScenario(value) {
    setRestaurantForm((form) => ({ ...form, scenario: value, ...(quickScenarioValues[value] || {}) }));
    setRestaurantData(null);
  }

  function selectRecipeScenario(value) {
    const preset = recipeScenarioValues[value] || {};
    setRecipeForm((form) => ({
      ...form,
      ...preset,
      scenario: value,
      ingredients: preset.ingredients ? preset.ingredients.map((item) => ({ ...item })) : form.ingredients,
    }));
    setRecipeData(null);
  }

  async function refreshWeather(location) {
    setWeatherLoading(true);
    try {
      const current = await api.weather(location);
      setWeatherInfo(current);
      setRestaurantForm((form) => ({ ...form, weather: current.weather || "普通" }));
    } catch (err) {
      setWeatherInfo({ ok: false, weather: "普通", location: "手動模式", error: err.message });
    } finally { setWeatherLoading(false); }
  }

  async function locate() {
    if (!navigator.geolocation) return setError("瀏覽器不支援定位");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setRestaurantForm((form) => ({ ...form, latitude: coords.latitude, longitude: coords.longitude }));
        refreshWeather(`${coords.latitude},${coords.longitude}`);
      },
      () => setError("無法取得定位，請檢查瀏覽器權限"),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  async function submit() {
    if (mode === "recipe" && !recipeForm.ingredients.some((item) => item.name.trim())) {
      setError("請至少輸入一項冰箱食材");
      return;
    }
    setLoading(true); setError("");
    try {
      if (mode === "restaurant") setRestaurantData(await api.restaurants(restaurantForm));
      else setRecipeData(await api.recipes(recipeForm));
      setAnalysisOpen(true);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  function addIngredient() {
    const name = newIngredient.trim();
    if (name) {
      setRecipeForm((form) => ({ ...form, ingredients: [...form.ingredients, { name, days_stored: 1, shelf_life: 7, price: 40, perishability: "中" }] }));
      setNewIngredient("");
    }
  }

  function updateIngredient(index, key, value) {
    setRecipeForm((form) => ({ ...form, ingredients: form.ingredients.map((item, i) => i === index ? { ...item, [key]: value } : item) }));
  }

  function removeIngredient(index) {
    setRecipeForm((form) => ({ ...form, ingredients: form.ingredients.filter((_, i) => i !== index) }));
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
    await api.logout(); setUser(null); setFavorites([]); setFavoritesOpen(false);
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
        {user ? <div className="flex items-center gap-2"><div className="hidden text-right sm:block"><div className="text-sm font-black">{user.display_name}</div><div className="text-xs text-muted">已登入個人帳號</div></div><button onClick={()=>setFavoritesOpen(true)} title="查看收藏" className="focus-ring flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-black"><Heart size={17} fill={favorites.length ? "currentColor" : "none"}/><span>{favorites.length}</span></button><button onClick={logout} title="登出" className="focus-ring grid size-10 place-items-center rounded-md border border-line bg-white"><LogOut size={17}/></button></div> : <button onClick={()=>setAuthOpen(true)} className="focus-ring flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-bold"><LogIn size={17}/>登入</button>}
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
        <aside className="min-w-0 self-start rounded-md border border-line bg-white p-4 lg:sticky lg:top-20">
          <div className="mb-4 flex items-center gap-2"><SlidersIcon/><h2 className="text-lg font-black">{mode === "restaurant" ? "外食條件" : "冰箱條件"}</h2></div>
          {mode === "restaurant" ? <div className="grid gap-4">
            <Field label="快速情境"><Select value={restaurantForm.scenario} onChange={(e) => selectRestaurantScenario(e.target.value)}>{(options?.restaurants.scenarios || []).map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <Field label={`預算上限 ${restaurantForm.budget} 元`}><input className="range" type="range" min="50" max="300" step="5" value={restaurantForm.budget} onChange={(e) => updateRestaurant("budget", Number(e.target.value))}/></Field>
            <Field label={`可接受距離 ${restaurantForm.max_distance} 分鐘`}><input className="range" type="range" min="1" max="20" value={restaurantForm.max_distance} onChange={(e) => updateRestaurant("max_distance", Number(e.target.value))}/></Field>
            <Field label="餐點類型"><Select value={restaurantForm.category} onChange={(e) => updateRestaurant("category", e.target.value)}><option>不限</option>{(options?.restaurants.categories || []).map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <Field label="目前心情"><Select value={restaurantForm.mood} onChange={(e) => updateRestaurant("mood", e.target.value)}>{["省錢","疲累","開心","心情不好","選擇困難"].map((x) => <option key={x}>{x}</option>)}</Select>{emotionResult && <span className="text-xs font-bold text-leaf">OpenCV：{emotionResult.expression_label}，已套用「{emotionResult.recommended_mood}」</span>}</Field>
            <button onClick={()=>setEmotionOpen(true)} className="focus-ring flex h-10 items-center justify-center gap-2 rounded-md border border-leaf/30 bg-leaf-soft text-sm font-black text-leaf"><Camera size={17}/>用表情帶入心情</button>
            <button onClick={locate} className="focus-ring flex h-10 items-center justify-center gap-2 rounded-md border border-line bg-white text-sm font-bold"><LocateFixed size={17}/>{restaurantForm.latitude ? "定位已套用" : "使用目前位置"}</button>
            <div className="rounded-md border border-line bg-canvas p-3 text-xs leading-6 text-muted">
              <div className="flex items-center justify-between gap-2"><span><b className="text-ink">自動天氣：</b>{weatherLoading ? "取得中" : `${restaurantForm.weather}${weatherInfo?.temperature_c != null ? ` · ${weatherInfo.temperature_c}°C` : ""}`}</span><button type="button" onClick={()=>refreshWeather(restaurantForm.latitude ? `${restaurantForm.latitude},${restaurantForm.longitude}` : "Xitun District, Taichung, Taiwan")} className="font-black text-leaf">更新</button></div>
              <div><b className="text-ink">自動時段：</b>{restaurantForm.meal_time} · 依裝置時間判斷</div>
              <div><b className="text-ink">距離基準：</b>{restaurantForm.latitude ? `${restaurantForm.latitude.toFixed(4)}, ${restaurantForm.longitude.toFixed(4)}` : "尚未定位，使用資料集預估距離"}</div>
            </div>
            <details className="border-t border-line pt-3"><summary className="cursor-pointer text-sm font-black">進階條件</summary><div className="mt-3 grid gap-3">
              <Field label="目前天氣"><Select value={restaurantForm.weather} onChange={(e) => updateRestaurant("weather", e.target.value)}>{["普通","熱","冷","雨天"].map((x) => <option key={x}>{x}</option>)}</Select></Field>
              <Field label="用餐時段"><Select value={restaurantForm.meal_time} onChange={(e) => updateRestaurant("meal_time", e.target.value)}>{["早餐","午餐","下午茶","晚餐","宵夜"].map((x) => <option key={x}>{x}</option>)}</Select></Field>
              <Field label="外帶需求"><Select value={restaurantForm.need_takeout} onChange={(e) => updateRestaurant("need_takeout", e.target.value)}><option value="不限">不限</option><option value="yes">需要外帶</option><option value="no">只找內用</option></Select></Field>
              <Field label={`可接受辣度 ${restaurantForm.max_spicy_level}`}><input className="range" type="range" min="0" max="5" value={restaurantForm.max_spicy_level} onChange={(e) => updateRestaurant("max_spicy_level", Number(e.target.value))}/></Field>
              <Field label="最低評分"><input className="focus-ring h-10 rounded-md border border-line px-3" type="number" min="0" max="5" step="0.1" value={restaurantForm.min_rating} onChange={(e) => updateRestaurant("min_rating", Number(e.target.value))}/></Field>
              <Field label="排序方式"><Select value={restaurantForm.sort_by} onChange={(e) => updateRestaurant("sort_by", e.target.value)}>{["綜合推薦","CP值優先","距離最近","評分最高"].map((x)=><option key={x}>{x}</option>)}</Select></Field>
              <Field label={`評論權重 ${restaurantForm.review_weight}%`}><input className="range" type="range" min="0" max="100" step="10" value={restaurantForm.review_weight} onChange={(e) => updateRestaurant("review_weight", Number(e.target.value))}/></Field>
              <Field label={`最高負評比例 ${restaurantForm.max_negative_ratio}%`}><input className="range" type="range" min="0" max="100" step="5" value={restaurantForm.max_negative_ratio} onChange={(e) => updateRestaurant("max_negative_ratio", Number(e.target.value))}/></Field>
              <Field label="顯示筆數"><Select value={restaurantForm.top_n} onChange={(e) => updateRestaurant("top_n", Number(e.target.value))}>{[3,5,8,10].map((x)=><option key={x}>{x}</option>)}</Select></Field>
              <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={restaurantForm.prefer_fast} onChange={(e) => updateRestaurant("prefer_fast", e.target.checked)}/>希望快速出餐</label>
              <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={restaurantForm.use_review_analysis} onChange={(e) => updateRestaurant("use_review_analysis", e.target.checked)}/>納入評論分析</label>
              <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={restaurantForm.hide_high_risk} onChange={(e) => updateRestaurant("hide_high_risk", e.target.checked)}/>隱藏高風險餐廳</label>
            </div></details>
          </div> : <div className="grid gap-4">
            <Field label="快速情境"><Select value={recipeForm.scenario} onChange={(e) => selectRecipeScenario(e.target.value)}>{(options?.recipes.scenarios || []).map((x) => <option key={x}>{x}</option>)}</Select><span className="text-xs font-bold text-leaf">已套用：{recipeForm.smart_mode} · 最多缺 {recipeForm.max_missing} 項 · {recipeForm.max_calories} kcal</span></Field>
            <div>
              <span className="text-sm font-black">冰箱食材</span>
              <div className="mt-2 flex gap-2"><input className="focus-ring h-10 min-w-0 flex-1 rounded-md border border-line px-3 text-sm" value={newIngredient} placeholder="輸入食材名稱" onChange={(e)=>setNewIngredient(e.target.value)} onKeyDown={(e)=>{if(e.key === "Enter"){e.preventDefault();addIngredient();}}}/><button type="button" className="h-10 rounded-md bg-leaf px-3 text-sm font-black text-white" onClick={addIngredient}>新增</button></div>
              <div className="mt-3 grid min-w-0 gap-2">{recipeForm.ingredients.map((item, index) => <div className="min-w-0 rounded-md border border-line p-3" key={`${item.name}-${index}`}>
                <div className="flex items-center justify-between gap-2"><input aria-label="食材名稱" className="min-w-0 flex-1 border-0 bg-transparent font-black outline-none" value={item.name} onChange={(e)=>updateIngredient(index,"name",e.target.value)}/><button type="button" title="移除食材" onClick={()=>removeIngredient(index)} className="grid size-7 place-items-center rounded text-coral"><X size={16}/></button></div>
                <div className="mt-2 grid min-w-0 grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2">
                  <Field label="已放天數"><input className="h-9 w-full min-w-0 rounded border border-line px-2 text-sm" type="number" min="0" value={item.days_stored} onChange={(e) => updateIngredient(index,"days_stored",Number(e.target.value))}/></Field>
                  <Field label="保存期限"><input className="h-9 w-full min-w-0 rounded border border-line px-2 text-sm" type="number" min="1" value={item.shelf_life} onChange={(e) => updateIngredient(index,"shelf_life",Number(e.target.value))}/></Field>
                  <Field label="估計價格"><input className="h-9 w-full min-w-0 rounded border border-line px-2 text-sm" type="number" min="0" value={item.price} onChange={(e) => updateIngredient(index,"price",Number(e.target.value))}/></Field>
                  <Field label="易腐程度"><select className="h-9 w-full min-w-0 rounded border border-line bg-white px-2 text-sm" value={item.perishability} onChange={(e)=>updateIngredient(index,"perishability",e.target.value)}>{["低","中","高"].map((x)=><option key={x}>{x}</option>)}</select></Field>
                </div>
              </div>)}</div>
            </div>
            <Field label={`料理時間 ${recipeForm.max_time} 分鐘`}><input className="range" type="range" min="5" max="60" step="5" value={recipeForm.max_time} onChange={(e) => updateRecipe("max_time",Number(e.target.value))}/></Field>
            <Field label={`熱量上限 ${recipeForm.max_calories} kcal`}><input className="range" type="range" min="150" max="900" step="50" value={recipeForm.max_calories} onChange={(e) => updateRecipe("max_calories",Number(e.target.value))}/></Field>
            <Field label="最多缺少食材"><Select value={recipeForm.max_missing} onChange={(e) => updateRecipe("max_missing",Number(e.target.value))}>{[0,1,2,3,4,5].map((x) => <option key={x}>{x}</option>)}</Select></Field>
            <details className="border-t border-line pt-3"><summary className="cursor-pointer text-sm font-black">進階條件</summary><div className="mt-3 grid gap-3">
              <Field label="料理難度"><Select value={recipeForm.difficulty} onChange={(e)=>updateRecipe("difficulty",e.target.value)}>{["不限","簡單","普通","困難"].map((x)=><option key={x}>{x}</option>)}</Select></Field>
              <Field label="顯示筆數"><Select value={recipeForm.top_n} onChange={(e)=>updateRecipe("top_n",Number(e.target.value))}>{[3,5,8,10].map((x)=><option key={x}>{x}</option>)}</Select></Field>
              <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={recipeForm.only_cookable} onChange={(e)=>updateRecipe("only_cookable",e.target.checked)}/>只顯示現有食材足夠的食譜</label>
            </div></details>
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

          {mode === "restaurant" && results?.length > 0 && <RestaurantMap
            rows={results}
            latitude={restaurantForm.latitude}
            longitude={restaurantForm.longitude}
          />}

          {results && <section className="mt-5 rounded-md border border-line bg-white p-4">
            <button type="button" onClick={()=>setAnalysisOpen((open)=>!open)} className="flex w-full items-center justify-between gap-3 text-left font-black" aria-expanded={analysisOpen}>
              <span className="flex items-center gap-2"><BarChart3 size={18}/>進階分析與模型資訊</span>
              <ChevronDown size={18} className={`transition-transform ${analysisOpen ? "rotate-180" : ""}`}/>
            </button>
            {analysisOpen && ((mode === "restaurant" ? restaurantData?.analysis : recipeData?.analysis)
              ? (mode === "restaurant" ? <RestaurantAdvanced data={restaurantData}/> : <RecipeAdvanced data={recipeData}/>)
              : <div className="mt-4 rounded-md border border-coral/25 bg-[#fff0eb] p-4">
                  <p className="font-black text-coral-dark">這筆結果來自舊版推薦資料，尚未包含模型分析。</p>
                  <p className="mt-1 text-sm text-muted">重新計算一次後，系統會載入 Dashboard、排名比較、分數拆解與敏感度分析。</p>
                  <button type="button" onClick={submit} disabled={loading} className="mt-3 h-10 rounded-md bg-coral px-4 text-sm font-black text-white">{loading ? "重新計算中..." : "重新計算並載入分析"}</button>
                </div>)}
          </section>}
        </section>
      </div>
    </main>
    {authOpen && <AuthModal mode={authMode} setMode={setAuthMode} form={authForm} setForm={setAuthForm} error={authError} busy={authBusy} onSubmit={submitAuth} onClose={()=>setAuthOpen(false)}/>} 
    {favoritesOpen && <FavoritesModal
      favorites={favorites}
      onRemove={async (kind,name)=>{await api.removeFavorite(kind,name);setFavorites((await api.favorites()).favorites);}}
      onClose={()=>setFavoritesOpen(false)}
    />}
    {emotionOpen && <EmotionModal onClose={()=>setEmotionOpen(false)} onApply={(result)=>{setEmotionResult(result);updateRestaurant("mood",result.recommended_mood);}}/>}
  </div>;
}

function SlidersIcon() { return <span className="grid size-8 place-items-center rounded-md bg-[#fff0eb] text-coral"><BarChart3 size={17}/></span>; }

export default App;
