import CarbonHero from '@/components/hero/carbon-hero';
import LandingSections from '@/components/landing/landing-sections';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#04100b]">
      <CarbonHero />
      <LandingSections />
    </main>
  );
}
