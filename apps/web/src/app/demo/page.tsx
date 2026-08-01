import type { Metadata } from 'next';

import { DemoShellController } from '@/components/demo/demo-shell';
import { ScrollToTop } from '@/components/layout/scroll-to-top';

export const metadata: Metadata = {
  title: 'Verified Judge Demo',
  description: 'Public hash-verified frozen evidence from the TreeQ Carbon point-cloud pipeline.',
};

export default function DemoPage() {
  return (
    <>
      <DemoShellController />
      <ScrollToTop />
    </>
  );
}
