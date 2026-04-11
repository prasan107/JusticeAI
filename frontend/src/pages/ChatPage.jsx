import { useState } from "react";
import API from "../api/axiosClient";

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");

    const sendMessage = async () => {
        if (!input.trim()) return;
        const userMsg = { role: "user", text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");

        const res = await API.post("/chat/message", { message: input });
        setMessages(prev => [...prev, { role: "ai", text: res.data.reply }]);
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Legal Chatbot</h1>
            <div className="border rounded p-4 h-96 overflow-y-auto mb-4 space-y-2">
                {messages.map((m, i) => (
                    <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                        <span className={`inline-block px-3 py-2 rounded ${m.role === "user" ? "bg-blue-100" : "bg-gray-100"}`}>
                            {m.text}
                        </span>
                    </div>
                ))}
            </div>
            <div className="flex gap-2">
                <input className="border p-2 flex-1 rounded" value={input}
                    onChange={e => setInput(e.target.value)} placeholder="Ask a legal question..." />
                <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={sendMessage}>Send</button>
            </div>
        </div>
    );
}
