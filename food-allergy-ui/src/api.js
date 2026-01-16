// Use relative paths so the create-react-app dev proxy handles API requests in development
const API_BASE = "";

export async function apiFetch(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    credentials: "include",
    headers: {
      ...(options.headers || {})
    },
    ...options,
  });

  return res;
}

const api = {
  login: (data) =>
    apiFetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  register: (data) =>
    apiFetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  getAllergies: () => apiFetch("/allergies"),

  saveAllergies: (allergies) =>
    apiFetch("/allergies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ allergies }),
    }),

  logout: () => apiFetch("/logout"),

  scanImage: (file) => {
    const fd = new FormData();
    fd.append("image", file);

    return apiFetch("/predict_image", {
      method: "POST",
      body: fd,
    });
  },
};

export default api;



// const API_BASE = "http://127.0.0.1:5000";

// /**
//  * Generic fetch wrapper (THIS WAS MISSING)
//  */
// export async function apiFetch(url, options = {}) {
//   const res = await fetch(`${API_BASE}${url}`, {
//     credentials: "include",
//     ...options,
//   });

//   return res.json();
// }

// /**
//  * Structured API helpers
//  */
// const api = {
//   login: (data) =>
//     apiFetch("/login", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(data),
//     }),

//   register: (data) =>
//     apiFetch("/register", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(data),
//     }),

//   getAllergies: () => apiFetch("/allergies"),

//   saveAllergies: (allergies) =>
//     apiFetch("/allergies", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ allergies }),
//     }),

//   scanImage: (file) => {
//     const fd = new FormData();
//     fd.append("image", file);

//     return apiFetch("/predict_image", {
//       method: "POST",
//       body: fd,
//     });
//   },
// };

// export default api;


