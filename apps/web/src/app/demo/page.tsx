import type { Metadata } from 'next';

import { DemoShell } from '@/components/demo/demo-shell';

export const metadata: Metadata = {
  title: 'Verified Judge Demo',
  description: 'Public hash-verified frozen evidence from the TreeQ Carbon point-cloud pipeline.',
};

export default function DemoPage() {
  return <DemoShell />;
}
