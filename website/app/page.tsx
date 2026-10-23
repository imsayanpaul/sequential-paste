import { Download, Faq, Footer } from "@/components/Closing";
import { Hero } from "@/components/Hero";
import { Nav } from "@/components/Nav";
import { Bento, Marquee, Modes, Shortcuts } from "@/components/Sections";
import { Showcase } from "@/components/Showcase";
import { getStars } from "@/lib/site";

// Rebuilt at most hourly on Vercel, so the star count stays fresh
export const revalidate = 3600;

export default async function Home() {
  const stars = await getStars();
  return (
    <>
      <Nav stars={stars} />
      <main>
        <Hero />
        <Marquee />
        <Modes />
        <Bento />
        <Showcase />
        <Shortcuts />
        <Download />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
