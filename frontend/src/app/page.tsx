import Hero from "@/components/Landing/Hero";
import Features from "@/components/Landing/Features";

export default function LandingPage() {
  return (
    <>
      <Hero
        heroText="Simplify Legal Documents with AI"
        description="Upload long legal documents, get instant summaries, and ask any query to our AI-powered legal assistant."
      />
      <Features />
    </>
  );
}
