import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";
import { TastingRoomExperience } from "@/components/tasting-room-experience";

export const metadata: Metadata = {
  title: "ChatG&T — Tasting Room",
  description: "Try to identify the fine-tuned response.",
};

export default function TastingRoomPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/tasting-room" />
      <TastingRoomExperience />
    </main>
  );
}
