async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "系統暫時無法完成請求");
  return data;
}

async function upload(path, formData) {
  const response = await fetch(path, { method: "POST", body: formData, credentials: "include" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "影像分析失敗");
  return data;
}

export const api = {
  options: () => request("/api/options"),
  weather: (location = "Xitun District, Taichung, Taiwan") => request(`/api/weather?location=${encodeURIComponent(location)}`),
  restaurants: (payload) => request("/api/recommend/restaurants", { method: "POST", body: JSON.stringify(payload) }),
  recipes: (payload) => request("/api/recommend/recipes", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/api/auth/me"),
  register: (payload) => request("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  favorites: () => request("/api/favorites"),
  addFavorite: (kind, itemName) => request("/api/favorites", { method: "POST", body: JSON.stringify({ kind, item_name: itemName }) }),
  removeFavorite: (kind, itemName) => request(`/api/favorites/${kind}/${encodeURIComponent(itemName)}`, { method: "DELETE" }),
  analyzeEmotion: (imageBlob) => {
    const form = new FormData();
    form.append("image", imageBlob, "camera.jpg");
    return upload("/api/emotion/analyze", form);
  },
};
