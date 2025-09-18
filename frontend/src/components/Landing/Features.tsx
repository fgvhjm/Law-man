import { FileText, MessageCircle } from "lucide-react";

export default function Features() {
  const features = [
    {
      icon: <FileText className="w-8 h-8 text-slate-900" />,
      title: "Instant Summaries",
      desc: "Quickly summarize lengthy legal documents into concise, readable insights."
    },
    {
      icon: <MessageCircle className="w-8 h-8 text-slate-900" />,
      title: "Ask Anything",
      desc: "Interact with our AI bot to clarify terms, sections, and legal jargon."
    }
  ];

  return (
    <section className="py-20 px-6 bg-slate-50">
      <div className="container mx-auto grid md:grid-cols-2 gap-12 max-w-5xl">
        {features.map((f, i) => (
          <div key={i} className="flex flex-col items-center text-center">
            <div className="mb-4">{f.icon}</div>
            <h3 className="text-xl font-semibold mb-2">{f.title}</h3>
            <p className="text-slate-600">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
