"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { sampleMessages } from "@/assets/samples/texts/text";

export default function ChatBot() {
  const [messages, setMessages] = useState<{ role: "user" | "bot"; text: string }[]>([]);
  const [input, setInput] = useState("");

  // const handleSend = () => {
  //   if (!input.trim()) return;
  //   setMessages([...messages, { role: "user", text: input }]);
  //   setInput("");
  //   // TODO: replace with API call to backend
  //   setMessages(prev => [...prev, { role: "bot", text: "This is a placeholder text" }]);
  // };

  useEffect(() => {
    console.log("hello")
    setMessages((msgs) => msgs = [...msgs, ...sampleMessages])
  }, [])

  return (
    <div className="border rounded-lg p-4 flex flex-col h-[524px]">
      <div className="flex-1 overflow-y-auto space-y-2 mb-2">
        {messages.map((m, i) => (
          <div key={i} className={`p-2 rounded-md text-sm ${m.role === "user" ? "bg-slate-200 self-end" : "bg-slate-100 self-start"}`}>
            <div className="font-semibold mb-1">{m.role === "user" ? "you" : "bot"}</div>
            <div className="break-words">{m.text}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-sm"
          placeholder="Ask something..."
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <Button>Send</Button>
      </div>
    </div>
  );
}
