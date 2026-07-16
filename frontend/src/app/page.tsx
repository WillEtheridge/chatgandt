import { SiteHeader } from "@/components/site-header";
import { SpiritGuideExperience } from "@/components/spirit-guide-experience";

export default function SpiritGuidePage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/" />
      <SpiritGuideExperience />
    </main>
  );
}
