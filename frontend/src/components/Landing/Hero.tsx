import { Button } from "@/components/ui/button";

export interface HeroProps {
    heroText: string
    description: string 
}

export default function Hero({ heroText, description }: HeroProps) {
  return (
    <section className="text-center py-24 px-6 bg-gradient-to-b from-slate-50 to-white">
      <h1 className="text-4xl md:text-6xl font-bold text-slate-900 mb-6">
        {heroText}
      </h1>
      <p className="text-lg text-slate-600 mb-8 max-w-2xl mx-auto">
        {description}
      </p>
      <div className="flex justify-center gap-4">
        <Button size="lg">Get Started</Button>
        <Button variant="outline" size="lg">Learn More</Button>
      </div>
    </section>
  );
}
