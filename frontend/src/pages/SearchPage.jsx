import { useState } from "react";
import API from "../api/axiosClient";

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleSearch = async () => {
        setLoading(true);
        const res = await API.post("/search/query", { query });
        setResults(res.data.results);
        setLoading(false);
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Legal Case Search</h1>
            <input className="border p-2 w-full mb-2" value={query}
                onChange={e => setQuery(e.target.value)} placeholder="Describe your case..." />
            <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={handleSearch}>
                {loading ? "Searching..." : "Search"}
            </button>
            <div className="mt-6 space-y-4">
                {results.map((r, i) => (
                    <div key={i} className="border rounded p-4 shadow">
                        <h2 className="font-semibold">{r.title}</h2>
                        <p className="text-sm text-gray-500">{r.court} | {r.year}</p>
                        <p className="mt-2">{r.summary}</p>
                        <p className="text-blue-500 text-sm">Score: {r.similarity_score}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
