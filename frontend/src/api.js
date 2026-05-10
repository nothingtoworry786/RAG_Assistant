import axios from "axios";

const BASE = import.meta.env.VITE_BACKEND_URL;

console.log("🔧 API Base URL:", BASE);

export async function ingestFile(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);

  console.log("📤 [REQUEST] POST /api/ingest", {
    file: file.name,
    size: file.size,
    type: file.type,
    url: `${BASE}/api/ingest`,
  });

  try {
    const { data } = await axios.post(`${BASE}/api/ingest`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    });
    console.log("✅ [RESPONSE] /api/ingest", data);
    return data;
  } catch (error) {
    console.error("❌ [ERROR] /api/ingest", error.response?.data || error.message);
    throw error;
  }
}

export async function queryDocument(docId, question) {
  const payload = { docId, question };
  console.log("📤 [REQUEST] POST /api/query", {
    url: `${BASE}/api/query`,
    payload,
  });

  try {
    const { data } = await axios.post(`${BASE}/api/query`, payload);
    console.log("✅ [RESPONSE] /api/query", data);
    return data;
  } catch (error) {
    console.error("❌ [ERROR] /api/query", error.response?.data || error.message);
    throw error;
  }
}
